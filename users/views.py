from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
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
        access = refresh.access_token  # This is correct

        return {
            "refresh": str(refresh),
            "access": str(access),
        }
    except Exception as e:
        import traceback

        traceback.print_exc()
        # Use DRF Response only in views
        return {"error": str(e)}


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
    s3_client.put_object(Bucket=BUCKET_NAME, Key=folder_key)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    try:
        user = request.user
        return Response(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "date_joined": user.date_joined,
            },
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        return Response(
            {"error": "Failed to fetch user profile", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upload_profile_pic(request):
    user = request.user
    uploaded_file = request.FILES.get("file")

    if not uploaded_file:
        return Response({"error": "No file provided"}, status=400)

    s3_key = f"uploads/user-{user.id}/profile_pic/profile_pic"

    try:
        s3_client.upload_fileobj(
            uploaded_file,
            BUCKET_NAME,
            s3_key,
            ExtraArgs={"ContentType": uploaded_file.content_type},
        )

        presigned_url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": BUCKET_NAME, "Key": s3_key},
            ExpiresIn=3600,
        )

        return Response({"profile_pic_url": presigned_url}, status=201)
    except ClientError as e:
        return Response({"error": str(e)}, status=500)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_profile_pic(request):
    try:
        user_id = request.user.id
        prefix = f"uploads/user-{user_id}/profile_pic/profile_pic"
        response = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix)

        if "Contents" not in response:
            return Response(
                {"error": "No profile picture found"}, status=status.HTTP_404_NOT_FOUND
            )

        for obj in response["Contents"]:
            s3_client.delete_object(Bucket=BUCKET_NAME, Key=obj["Key"])

        return Response(
            {"success": True, "message": "Profile picture deleted"},
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        traceback.print_exc()
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_profile_pic(request):
    try:
        user_id = request.user.id
        prefix = f"uploads/user-{user_id}/profile_pic/profile_pic"
        response = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix)

        if "Contents" not in response or not response["Contents"]:
            return Response({"profilePicUrl": None}, status=status.HTTP_200_OK)

        latest_obj = max(response["Contents"], key=lambda x: x["LastModified"])
        key = latest_obj["Key"]

        presigned_url = s3_client.generate_presigned_url(
            "get_object", Params={"Bucket": BUCKET_NAME, "Key": key}, ExpiresIn=3600
        )

        return Response({"profilePicUrl": presigned_url}, status=status.HTTP_200_OK)

    except Exception as e:
        traceback.print_exc()
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_user_profile(request):
    try:
        first_name = request.data.get("first_name", "").strip()
        last_name = request.data.get("last_name", "").strip()

        if not first_name and not last_name:
            return Response(
                {"error": "At least one of first_name or last_name is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name

        user.save()

        return Response(
            {
                "success": True,
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "date_joined": user.date_joined,
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        traceback.print_exc()
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
