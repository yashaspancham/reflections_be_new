import os
import boto3
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from rest_framework_simplejwt.tokens import AccessToken
from .models import Entry
from django.utils import timezone
from datetime import timedelta


load_dotenv()
s3_client = boto3.client("s3", region_name=os.getenv("AWS_REGION"))
BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")


def html_to_text(html_content: str) -> str:
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text(" ", strip=True)


def generate_title(entryContent: str):
    soup = BeautifulSoup(entryContent, "html.parser")
    heading = soup.find(["h1", "h2", "h3", "h4", "h5", "h6"])
    title = heading.get_text(strip=True) if heading else "Untitled"
    return title


def generate_img_url(entryContent: str):
    soup = BeautifulSoup(entryContent, "html.parser")
    img = soup.find("img")
    url = img["src"] if img and img.has_attr("src") else None
    if url != None:
        return refresh_presigned_url(url)
    return None


def refresh_all_img_urls(html_content: str) -> str:
    soup = BeautifulSoup(html_content, "html.parser")
    imgs = soup.find_all("img")

    for img in imgs:
        if img.has_attr("src"):
            old_url = img["src"]
            try:
                img["src"] = refresh_presigned_url(old_url)
            except Exception as e:
                print(f"Could not refresh {old_url}: {e}")

    return str(soup)


def extract_object_key(url: str):
    parsed_url = urlparse(url)
    return parsed_url.path.lstrip("/")


def refresh_presigned_url(url: str):
    object_key = extract_object_key(url)
    presigned_url = s3_client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": BUCKET_NAME,
            "Key": object_key,
        },
        ExpiresIn=3600,
    )
    return presigned_url


def get_user_id_from_request(request):
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        access_token = AccessToken(token)
        return access_token["user_id"]
    return None


# Functions for entry_stats API
# week starts on monday and ends on sunday
def get_total_entries(user):
    try:
        return Entry.objects.filter(user=user).count() or 0
    except Exception:
        return 0


def get_entries_this_week(user):
    try:
        today = timezone.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        return (
            Entry.objects.filter(user=user, created_at__date__gte=start_of_week).count()
            or 0
        )
    except Exception:
        return 0


def get_entries_this_month(user):
    try:
        today = timezone.now().date()
        start_of_month = today.replace(day=1)
        return (
            Entry.objects.filter(
                user=user, created_at__date__gte=start_of_month
            ).count()
            or 0
        )
    except Exception:
        return 0


def get_entries_this_year(user):
    try:
        today = timezone.now().date()
        start_of_year = today.replace(month=1, day=1)
        return (
            Entry.objects.filter(user=user, created_at__date__gte=start_of_year).count()
            or 0
        )
    except Exception:
        return 0


def get_total_words(user):
    try:
        entries = Entry.objects.filter(user=user).values_list("entryContent", flat=True)
        total_words = 0
        for entry in entries:
            text = html_to_text(entry or "")
            total_words += len(text.split())
        return total_words
    except Exception as e:
        print(f"Error in get_total_words: {e}")
        return 0


def get_total_letters(user):
    try:
        entries = Entry.objects.filter(user=user).values_list("entryContent", flat=True)
        total_letters = 0
        for entry in entries:
            text = html_to_text(entry or "")
            total_letters += len(text.replace(" ", ""))
        return total_letters
    except Exception as e:
        print(f"Error in get_total_letters: {e}")
        return 0


def get_total_words_this_week(user):
    try:
        now = timezone.now()
        week_start = now - timedelta(days=now.weekday())  # Monday of this week
        entries = Entry.objects.filter(user=user, createdAt__gte=week_start).values_list("entryContent", flat=True)
        total_words = 0
        for entry in entries:
            text = html_to_text(entry or "")
            total_words += len(text.split())
        return total_words
    except Exception as e:
        print(f"Error in get_total_words_this_week: {e}")
        return 0


def get_total_letters_this_week(user):
    try:
        now = timezone.now()
        week_start = now - timedelta(days=now.weekday())
        entries = Entry.objects.filter(user=user, createdAt__gte=week_start).values_list("entryContent", flat=True)
        total_letters = 0
        for entry in entries:
            text = html_to_text(entry or "")
            total_letters += len(text.replace(" ", ""))
        return total_letters
    except Exception as e:
        print(f"Error in get_total_letters_this_week: {e}")
        return 0


def get_streaks(user):
    try:
        entry_dates = (
            Entry.objects.filter(user=user)
            .dates("createdAt", "day", order="ASC")
        )

        if not entry_dates:
            return {"current_streak": 0, "longest_streak": 0}
        #compute longest streak
        longest_streak = 1
        current_streak = 1
        temp_streak = 1
        today = timezone.now().date()
        last_date = entry_dates[0]

        for entry_date in entry_dates[1:]:
            if (entry_date - last_date).days == 1:
                temp_streak += 1
            else:
                temp_streak = 1

            if temp_streak > longest_streak:
                longest_streak = temp_streak

            last_date = entry_date

        # Compute current streak ending today
        streak_today = 0
        for i, entry_date in enumerate(reversed(entry_dates)):
            expected_date = today - timedelta(days=i)
            if entry_date == expected_date:
                streak_today += 1
            else:
                break

        return {"current_streak": streak_today, "longest_streak": longest_streak}

    except Exception as e:
        print(f"Error in get_streaks: {e}")
        return {"current_streak": 0, "longest_streak": 0}


def get_average_words_per_entry_this_week(user):
    try:
        entries = Entry.objects.filter(user=user).values_list("entryContent", flat=True)
        total_entries = entries.count()
        if total_entries == 0:
            return 0

        total_words = 0
        for entry in entries:
            text = html_to_text(entry or "")
            total_words += len(text.split())

        return total_words / total_entries
    except Exception as e:
        print(f"Error in get_average_words_per_entry: {e}")
        return 0


def get_average_letters_per_entry(user):
    try:
        entries = Entry.objects.filter(user=user).values_list("entryContent", flat=True)
        total_entries = entries.count()
        if total_entries == 0:
            return 0

        total_letters = 0
        for entry in entries:
            text = html_to_text(entry or "")
            total_letters += len(text.replace(" ", ""))

        return total_letters / total_entries
    except Exception as e:
        print(f"Error in get_average_letters_per_entry: {e}")
        return 0