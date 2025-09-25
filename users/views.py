from rest_framework.decorators import api_view
from django.contrib.auth import authenticate
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken


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
    user_data = {
        "id": user.id,
        "email": user.email,
        "username": user.username,
    }

    response = Response(
        {"msg": "Login successful", "tokens": tokens, "user_data": user_data},
        status=status.HTTP_200_OK,
    )
    return response


@api_view(["POST"])
def refresh_access(request):
    refresh_token = request.COOKIES.get("refreshToken")
    if not refresh_token:
        return Response(
            {"error": "No refresh token"}, status=status.HTTP_401_UNAUTHORIZED
        )

    try:
        refresh = RefreshToken(refresh_token)
        new_access = str(refresh.access_token)
        return Response({"access": new_access}, status=status.HTTP_200_OK)
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
    tokens = get_tokens_for_user(user)
    return Response(
        {"msg": "User created", "tokens": tokens}, status=status.HTTP_201_CREATED
    )
