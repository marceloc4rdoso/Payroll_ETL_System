from django.urls import path

from processor import views


app_name = "processor"

urlpatterns = [
    path("", views.upload_view, name="upload"),
    path("uploads/", views.uploads_list_view, name="uploads"),
]

