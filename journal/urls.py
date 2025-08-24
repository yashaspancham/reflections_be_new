from django.urls import path
from .views import list_entries_api, create_entry_content, update_entry_content

urlpatterns = [
    path("getAllEntries/", list_entries_api, name="list_entries_api"),
    path("createEntry/", create_entry_content, name="create_entry_content"),
    path("updateEntry/", update_entry_content, name="update_entry_content"),
]