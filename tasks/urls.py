from django.urls import path
from .views import (
    get_tasks,
)

urlpatterns = [
    path("get_tasks/", get_tasks, name="get_tasks"),
]