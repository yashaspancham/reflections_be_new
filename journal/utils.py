import os
import boto3
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from rest_framework_simplejwt.tokens import AccessToken

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
    auth_header = request.headers.get(
        "Authorization"
    )
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        access_token = AccessToken(token)
        return access_token["user_id"]
    return None