from django.contrib import admin

from people.models import Contato, Empresa


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ("name", "cnpj", "layout_type", "is_active", "created_at")
    list_filter = ("layout_type", "is_active")
    search_fields = ("name", "cnpj")


@admin.register(Contato)
class ContatoAdmin(admin.ModelAdmin):
    list_display = ("name", "empresa", "email", "phone", "is_active")
    list_filter = ("is_active", "empresa")
    search_fields = ("name", "email", "phone", "empresa__name")
