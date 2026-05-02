from django.urls import path

from processor import views


app_name = "processor"

urlpatterns = [
    path("", views.dashboard_view, name="dashboard"),
    path("upload/", views.upload_view, name="upload"),
    path("uploads/", views.uploads_list_view, name="uploads"),
    path("sistemas/", views.SourceSystemListView.as_view(), name="system_list"),
    path("sistemas/novo/", views.SourceSystemCreateView.as_view(), name="system_create"),
    path("sistemas/<int:pk>/editar/", views.SourceSystemUpdateView.as_view(), name="system_update"),
    path("sistemas/<int:pk>/layout/", views.SourceSystemLayoutDesignerView.as_view(), name="system_layout"),
    path("sistemas/<int:pk>/excluir/", views.SourceSystemDeleteView.as_view(), name="system_delete"),
]
