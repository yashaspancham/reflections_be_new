import os
import requests
import boto3
from botocore.client import Config
from django.shortcuts import render
from botocore.exceptions import ClientError
from django.http import JsonResponse
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import AccessToken
from urllib.parse import urlparse, unquote
from dotenv import load_dotenv
import json
from diff_match_patch import diff_match_patch
from journal.models import Entry
from api.utils import list_s3_files
import traceback

load_dotenv()
s3_client = boto3.client("s3", region_name=os.getenv("AWS_REGION"))
BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")


def hello(request):
    return JsonResponse({"message": "hello from the django backend for reflections"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upload_file_and_get_presigned_url(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST request required"}, status=400)

    uploaded_file = request.FILES.get("file")
    if not uploaded_file:
        return JsonResponse({"error": "No file present"}, status=400)

    user_id = get_user_id_from_request(request)

    prefix = f"uploads/user-{user_id}/"
    response = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix)
    objects = response.get("Contents", [])
    if len(objects) >= 50:
        return JsonResponse({"error": "Maximum of 50 images allowed"}, status=400)

    s3_key = f"{prefix}{uploaded_file.name}"
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

        return JsonResponse({"url": presigned_url, "key": s3_key}, status=201)
    except ClientError as e:
        return JsonResponse({"error": str(e)}, status=500)



def get_user_id_from_request(request):
    auth_header = request.headers.get(
        "Authorization"
    )
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        access_token = AccessToken(token)
        return access_token["user_id"]
    return None


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_presigned_urls(request):
    try:
        user_id = get_user_id_from_request(request)

        response = s3_client.list_objects_v2(
            Bucket=BUCKET_NAME, Prefix=f"uploads/user-{user_id}/"
        )
        objects = response.get("Contents", [])
        urls = []

        for obj in objects:
            key = obj["Key"]
            if key.endswith("/"):
                continue
            presigned_url = s3_client.generate_presigned_url(
                "get_object", Params={"Bucket": BUCKET_NAME, "Key": key}, ExpiresIn=3600
            )
            urls.append({"key": key, "url": presigned_url})

        return JsonResponse({"files": urls}, status=200)

    except ClientError as e:
        return JsonResponse({"error": str(e), "files": []}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
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


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_image(request):
    if request.method == "DELETE":
        try:
            url = request.GET.get("url")
            if not url:
                return JsonResponse({"error": "No URL provided"}, status=400)

            parsed = urlparse(url)
            key = unquote(parsed.path.lstrip("/"))

            user_id = get_user_id_from_request(request)

            expected_prefix = f"uploads/user-{user_id}/"
            if not key.startswith(expected_prefix):
                return JsonResponse(
                    {"error": "Unauthorized to delete this file"}, status=403
                )

            s3 = boto3.client("s3")
            s3.delete_object(Bucket=BUCKET_NAME, Key=key)

            return JsonResponse({"message": "Image deleted successfully"})

        except Exception as e:
            traceback.print_exc()
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=405)
