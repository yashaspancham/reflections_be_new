import os
import requests
import boto3
from botocore.client import Config
from django.shortcuts import render
from botocore.exceptions import ClientError
from django.http import JsonResponse
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import urllib.parse
from dotenv import load_dotenv
import json
from diff_match_patch import diff_match_patch
from journal.models import Entry, Task
from api.utils import list_s3_files, write_to_file, read_from_file

load_dotenv()
s3_client = boto3.client("s3", region_name="ap-south-1")
BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")


def hello(request):
    return JsonResponse({"message": "hello from the django backend for reflections"})


@csrf_exempt
def upload_file_and_get_presigned_url(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST request required"}, status=400)

    uploaded_file = request.FILES.get("file")
    if not uploaded_file:
        return JsonResponse({"error": "No file presnet"}, status=400)
    if len(list_s3_files()) >= 50:
        return JsonResponse({"error": "maximum of 50 iamges only"}, status=400)

    s3_key = f"uploads/{uploaded_file.name}"

    try:
        s3_client.upload_fileobj(
            uploaded_file,
            BUCKET_NAME,
            s3_key,
            ExtraArgs={"ContentType": uploaded_file.content_type},
        )

        presigned_url = s3_client.generate_presigned_url(
            "get_object", Params={"Bucket": BUCKET_NAME, "Key": s3_key}, ExpiresIn=3600
        )

        return JsonResponse({"url": presigned_url, "Key": s3_key}, status=201)
    except ClientError as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def createEntryContent(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST request required"}, status=400)
    data = json.loads(request.body)
    content = data.get("content", "")

    if not content.strip():
        return JsonResponse({"error": "Content cannot be empty"}, status=400)
    print("content: ", content)

    try:
        entry = Entry.objects.create(entryContent=content)
        print("entry: ", entry)
        return JsonResponse({"msg": "Success", "entry_id": entry.id}, status=201)
    except Exception as e:
        import traceback

        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def updateEntryContent(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST request required"}, status=400)

    data = json.loads(request.body)
    patch_text = data.get("content", "")
    entry_id = data.get("entry_id")
    patch_text = urllib.parse.unquote(patch_text)
    try:
        entry = Entry.objects.get(id=entry_id)
    except Entry.DoesNotExist:
        return JsonResponse({"error": "Entry not found"}, status=404)
    oldHTML = entry.entryContent
    dmp = diff_match_patch()
    patches = dmp.patch_fromText(patch_text)
    newHTML, _ = dmp.patch_apply(patches, oldHTML)
    try:
        entry.entryContent = newHTML
        entry.save()
    except Exception as e:
        return JsonResponse({"error": "Unable to save"}, status=500)
    return JsonResponse({"msg": "Success"}, status=201)


@csrf_exempt
def list_presigned_urls(request):
    if request.method != "GET":
        return JsonResponse({"error": "GET request required"}, status=400)
    try:
        response = s3_client.list_objects_v2(Bucket=BUCKET_NAME)
        objects = response.get("Contents", [])
        urls = []
        for obj in objects:
            key = obj["Key"]
            presigned_url = s3_client.generate_presigned_url(
                "get_object", Params={"Bucket": BUCKET_NAME, "Key": key}, ExpiresIn=3600
            )
            if key != "uploads/":
                urls.append({"key": key, "url": presigned_url})
        # print("urls: ", urls)
        return JsonResponse({"files": urls}, status=200)
    except ClientError as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def download_image(request):
    url = request.GET.get("url")
    if not url:
        return HttpResponse("Missing url parameter", status=400)

    try:
        response = requests.get(url, stream=True)
        if response.status_code != 200:
            return HttpResponse("Failed to fetch image", status=500)

        content_type = response.headers.get("Content-Type", "image/jpeg")
        filename = url.split("/")[-1].split("?")[0]

        django_response = HttpResponse(response.content, content_type=content_type)
        django_response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return django_response

    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)


@csrf_exempt
def delete_image(request):
    if request.method == "DELETE":
        try:
            # get URL from query param
            url = request.GET.get("url")
            if not url:
                return JsonResponse({"error": "No URL provided"}, status=400)

            # extract S3 key from URL
            parsed = urlparse(url)
            key = unquote(parsed.path.lstrip("/"))  # remove leading slash

            s3 = boto3.client("s3")
            bucket_name = "reflections-static-assets"

            s3.delete_object(Bucket=bucket_name, Key=key)

            return JsonResponse({"message": "Image deleted successfully"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=405)
