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
from api.utils import list_s3_files
load_dotenv()
s3_client = boto3.client("s3", region_name=os.getenv("AWS_REGION"))
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
            url = request.GET.get("url")
            if not url:
                return JsonResponse({"error": "No URL provided"}, status=400)

            parsed = urlparse(url)
            key = unquote(parsed.path.lstrip("/"))
            s3 = boto3.client("s3")
            s3.delete_object(Bucket=BUCKET_NAME, Key=key)
            return JsonResponse({"message": "Image deleted successfully"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=405)