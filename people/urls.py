from django.urls import path

from people import views


app_name = "people"

urlpatterns = [
    path("", views.PeopleHomeView.as_view(), name="home"),
    path("empresas/", views.EmpresaListView.as_view(), name="empresa_list"),
    path("empresas/novo/", views.EmpresaCreateView.as_view(), name="empresa_create"),
    path("empresas/<int:pk>/editar/", views.EmpresaUpdateView.as_view(), name="empresa_update"),
    path("empresas/<int:pk>/excluir/", views.EmpresaDeleteView.as_view(), name="empresa_delete"),
    path("contatos/", views.ContatoListView.as_view(), name="contato_list"),
    path("contatos/novo/", views.ContatoCreateView.as_view(), name="contato_create"),
    path("contatos/<int:pk>/editar/", views.ContatoUpdateView.as_view(), name="contato_update"),
    path("contatos/<int:pk>/excluir/", views.ContatoDeleteView.as_view(), name="contato_delete"),
]
