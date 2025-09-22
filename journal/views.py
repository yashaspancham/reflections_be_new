from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Entry
from rest_framework import status
from .serializers import EntrySerializer
from diff_match_patch import diff_match_patch
import urllib
from journal.utils import (
    generate_title,
    generate_img_url,
    html_to_text,
    refresh_all_img_urls,
)
import traceback
from django.db.models import Q


class JournalPagination(PageNumberPagination):
    page_size = 8



@api_view(["GET"])
def list_entries_api(request):
    try:
        sort = request.query_params.get("sort", "-lastUpdated")
        search = request.query_params.get("search", "")
        entries = Entry.objects.all()
        if search:
            entries = entries.filter(entryContent__icontains=search)
        entries = entries.order_by(sort)
        paginator = JournalPagination()
        page_num = int(request.query_params.get("page", 1))
        total_entries = entries.count()
        last_page = max(1, (total_entries + paginator.page_size - 1) // paginator.page_size)
        # if requested page > last_page → clamp it
        if page_num > last_page:
            page_num = last_page
        request.GET._mutable = True
        request.GET["page"] = str(page_num)
        request.GET._mutable = False

        result_page = paginator.paginate_queryset(entries, request)
        serializer = EntrySerializer(result_page, many=True)

        custom_entries = []
        for entry in serializer.data:
            content = entry.get("entryContent", "")
            createdAt = entry.get("createdAt", "")
            lastUpdated = entry.get("lastUpdated", "")
            title = generate_title(content)
            url = generate_img_url(content)
            text = html_to_text(content)
            custom_entries.append(
                {
                    "id": entry["id"],
                    "title": title,
                    "url": url,
                    "content": text,
                    "createdAt": createdAt,
                    "lastUpdated": lastUpdated,
                }
            )

        return Response(
            {
                "success": True,
                "total_entries": total_entries,
                "total_pages": last_page,
                "current_page": page_num,
                "next_page": paginator.get_next_link(),
                "prev_page": paginator.get_previous_link(),
                "entries": custom_entries,
                "clamped": page_num == last_page,
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        traceback.print_exc()
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




@api_view(["POST"])
def create_entry_content(request):
    content = request.data.get("content", "")

    if not content.strip():
        return Response(
            {"error": "Content cannot be empty"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        entry = Entry.objects.create(entryContent=content)
        return Response(
            {"msg": "Success", "entry_id": entry.id}, status=status.HTTP_201_CREATED
        )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
def update_entry_content(request):
    patch_text = request.data.get("content", "")
    entry_id = request.data.get("entry_id")

    if not entry_id:
        return Response(
            {"error": "Entry ID required"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        entry = Entry.objects.get(id=entry_id)
    except Entry.DoesNotExist:
        return Response({"error": "Entry not found"}, status=status.HTTP_404_NOT_FOUND)

    patch_text = urllib.parse.unquote(patch_text)
    oldHTML = entry.entryContent

    dmp = diff_match_patch()
    patches = dmp.patch_fromText(patch_text)
    newHTML, _ = dmp.patch_apply(patches, oldHTML)

    try:
        entry.entryContent = newHTML
        entry.save()
        return Response({"msg": "Success"}, status=status.HTTP_200_OK)
    except Exception:
        return Response(
            {"error": "Unable to save"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
def get_entry_by_id(request):
    try:
        entry_id = request.query_params.get("entry_id")
        entry = Entry.objects.get(id=entry_id)
        serializer = EntrySerializer(entry)
        custom_entry_data = {
            "id": serializer.data["id"],
            "entryContent": refresh_all_img_urls(serializer.data["entryContent"]),
            "createdAt": serializer.data["createdAt"],
            "lastUpdated": serializer.data["lastUpdated"],
        }
        return Response(custom_entry_data, status=status.HTTP_200_OK)
    except Entry.DoesNotExist:
        return Response({"error": "Entry not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        traceback.print_exc()
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["DELETE"])
def delete_entry(request):
    try:
        entry_id = request.query_params.get("entry_id")
        entry = Entry.objects.get(id=entry_id)
        entry.delete()
        return Response({"message": "Entry deleted"}, status=status.HTTP_200_OK)
    except Entry.DoesNotExist:
        return Response({"error": "Entry not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        traceback.print_exc()
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)