from django.urls import path
from .views import hello, upload_file_and_get_presigned_url, createEntryContent, updateEntryContent, list_presigned_urls, download_image, delete_image

urlpatterns = [
    path('hello/', hello),
    path('upload/', upload_file_and_get_presigned_url, name='upload-file'),
    path('createEntry/', createEntryContent, name="create_entry_content"),
    path('updateEntry/', updateEntryContent, name="update_entry_content"),
    path('all_images/', list_presigned_urls,name="get_all_images"),
    path('download_image/', download_image, name="download_image"),
    path('delete_image', delete_image, name="delete_image"),
]
