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
    path("produtos/", views.ServiceProductListView.as_view(), name="product_list"),
    path("produtos/novo/", views.ServiceProductCreateView.as_view(), name="product_create"),
    path("produtos/<int:pk>/editar/", views.ServiceProductUpdateView.as_view(), name="product_update"),
    path("pedidos/", views.BillingOrderListView.as_view(), name="order_list"),
    path("pedidos/novo/", views.BillingOrderCreateView.as_view(), name="order_create"),
    path("pedidos/<int:pk>/", views.BillingOrderDetailView.as_view(), name="order_detail"),
    path("pedidos/<int:pk>/editar/", views.BillingOrderUpdateView.as_view(), name="order_update"),
    path("pedidos/<int:order_id>/itens/novo/", views.BillingLineCreateView.as_view(), name="line_create"),
    path("itens/<int:pk>/editar/", views.BillingLineUpdateView.as_view(), name="line_update"),
    path("itens/<int:pk>/excluir/", views.BillingLineDeleteView.as_view(), name="line_delete"),
    path("fechamentos/", views.BillingClosureListView.as_view(), name="closure_list"),
    path("fechamentos/novo/", views.BillingClosureCreateView.as_view(), name="closure_create"),
    path("fechamentos/<int:pk>/", views.BillingClosureDetailView.as_view(), name="closure_detail"),
    path("fechamentos/<int:pk>/fechar/", views.BillingClosureCloseView.as_view(), name="closure_close"),
]
