from django.urls import path
from .views import get_tasks, add_task, update_task, delete_task

urlpatterns = [
    path("get_tasks/", get_tasks, name="get_tasks"),
    path("add_task/", add_task, name="add_task"),
    path("update_task/<int:task_id>/", update_task, name="update_task"),
    path("delete_task/<int:task_id>/", delete_task, name="delete_task"),
]
