from rest_framework.decorators import api_view
from django.contrib.auth import authenticate
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
import os
import boto3
from dotenv import load_dotenv

load_dotenv()
s3_client = boto3.client("s3", region_name=os.getenv("AWS_REGION"))
BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")


def get_tokens_for_user(user):
    try:
        refresh = RefreshToken.for_user(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }
    except Exception as e:
        traceback.print_exc()
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
def signin(request):
    email = request.data.get("email")
    password = request.data.get("password")

    user = authenticate(username=email, password=password)
    if not user:
        return Response(
            {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
        )

    tokens = get_tokens_for_user(user)
    folder_exists = check_user_s3_folder(user.id)
    if not folder_exists:
        create_user_s3_folder(user.id)

    response = Response(
        {"msg": "Login successful", "tokens": tokens},
        status=status.HTTP_200_OK,
    )
    return response


def check_user_s3_folder(user_id: str) -> bool:
    folder_key = f"uploads/{user_id}/"
    response = s3_client.list_objects_v2(
        Bucket=BUCKET_NAME, Prefix=folder_key, MaxKeys=1
    )
    return "Contents" in response


@api_view(["POST"])
def refresh_access(request):
    refresh_token = request.data.get("refresh") 
    if not refresh_token:
        return Response(
            {"error": "No refresh token"}, status=status.HTTP_401_UNAUTHORIZED
        )

    try:
        refresh = RefreshToken(refresh_token)
        new_access = str(refresh.access_token)
        new_refresh = str(refresh)
        return Response(
            {"access": new_access, "refresh": new_refresh}, status=status.HTTP_200_OK
        )
    except TokenError:
        return Response(
            {"error": "Invalid refresh token. Please sign in again."},
            status=status.HTTP_401_UNAUTHORIZED,
        )


@api_view(["POST"])
def signup(request):
    email = request.data.get("email")
    password = request.data.get("password")

    if not email or not password:
        return Response(
            {"error": "Email and password required"}, status=status.HTTP_400_BAD_REQUEST
        )

    if User.objects.filter(email=email).exists():
        return Response(
            {"error": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST
        )

    user = User.objects.create_user(username=email, email=email, password=password)
    create_user_s3_folder(user.id)
    return Response({"msg": "User created"}, status=status.HTTP_201_CREATED)


def create_user_s3_folder(user_id: str):
    folder_key = f"uploads/user-{user_id}/"
    s3_client.put_object(Bucket=BUCKET_NAME, Key=folder_key)  #
