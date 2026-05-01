from django.urls import path

from people import views


app_name = "people"

urlpatterns = [
    path("", views.companies_list_view, name="companies"),
]

