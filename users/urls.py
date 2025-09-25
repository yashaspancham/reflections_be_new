from django.urls import path
from .views import signup, signin, refresh_access

urlpatterns = [
    path("signup/", signup, name="signup"),
    path("signin/", signin, name="signin"),
    path("refresh_access/", refresh_access, name="refresh_access"),
]
