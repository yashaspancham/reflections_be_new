from django.urls import path
from .views import (
    list_entries_api,
    create_entry_content,
    update_entry_content,
    get_entry_by_id,
    delete_entry,
    entry_stats
)

urlpatterns = [
    path("getAllEntries/", list_entries_api, name="list_entries_api"),
    path("createEntry/", create_entry_content, name="create_entry_content"),
    path("updateEntry/", update_entry_content, name="update_entry_content"),
    path("getEntryById/", get_entry_by_id, name="get_entry_by_id"),
    path("deleteEntry/", delete_entry, name="delete_entry"),
    path("entry_stats/",entry_stats,name="entry_stats"),
]
