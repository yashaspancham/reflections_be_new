from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Entry
from rest_framework import status
from .models import Entry
from .serializers import EntrySerializer
from diff_match_patch import diff_match_patch
import urllib
from journal.utils import generate_title_and_img_url, html_to_text


class JournalPagination(PageNumberPagination):
    page_size = 8


@api_view(["GET"])
def list_entries_api(request):
    try:
        entries = Entry.objects.all().order_by("-lastUpdated")
        paginator = JournalPagination()
        result_page = paginator.paginate_queryset(entries, request)
        serializer = EntrySerializer(result_page, many=True)
        custom_entries = []
        for entry in serializer.data:
            content = entry.get("entryContent", "")
            createdAt=entry.get("createdAt","")
            lastUpdated=entry.get("lastUpdated","")
            title_and_url=generate_title_and_img_url(content)
            title = title_and_url["content_title"]
            url = title_and_url["presigned_url"]
            text=html_to_text(content)
            custom_entries.append(
                {
                    "id": entry["id"],
                    "title": title,
                    "url": url,
                    "content": text,
                    "createdAt":createdAt,
                    "lastUpdated":lastUpdated
                }
            )

        return Response(
            {
                "success": True,
                "total_entries": paginator.page.paginator.count,
                "total_pages": paginator.page.paginator.num_pages,
                "current_page": paginator.page.number,
                "next_page": paginator.get_next_link(),
                "prev_page": paginator.get_previous_link(),
                "entries": custom_entries,
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(["POST"])
def create_entry_content(request):
    print("This is in journal")
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
    print("This is in journal")
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
