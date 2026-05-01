from django.contrib import admin

from people.models import Contato, Empresa


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ("name", "cnpj", "source_system", "layout_type", "has_logo", "is_active", "created_at")
    list_filter = ("source_system", "layout_type", "is_active")
    search_fields = ("name", "cnpj")

    @admin.display(boolean=True, description="Logo")
    def has_logo(self, obj: Empresa) -> bool:
        return bool(obj.logo)


@admin.register(Contato)
class ContatoAdmin(admin.ModelAdmin):
    list_display = ("name", "empresa", "email", "phone", "is_active")
    list_filter = ("is_active", "empresa")
    search_fields = ("name", "email", "phone", "empresa__name")
