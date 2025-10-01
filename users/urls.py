from django.urls import path
from .views import (
    signup,
    signin,
    refresh_access,
    get_user_profile,
    upload_profile_pic,
    delete_profile_pic,
    get_profile_pic,
    update_user_profile,
)

urlpatterns = [
    path("signup/", signup, name="signup"),
    path("signin/", signin, name="signin"),
    path("refresh_access/", refresh_access, name="refresh_access"),
    path("get_user_profile/", get_user_profile, name="get_user_profile"),
    path("upload_profile_pic/", upload_profile_pic, name="upload_profile_pic"),
    path("delete_profile_pic/", delete_profile_pic, name="delete_profile_pic"),
    path("get_profile_pic/", get_profile_pic, name="get_profile_pic"),
    path("update_user_profile/", update_user_profile, name="update_user_profile"),
]
