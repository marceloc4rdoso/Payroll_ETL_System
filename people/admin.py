from django.contrib import admin

from people.forms import ContatoForm
from people.models import Contato, Empresa, UserEmpresaVinculo


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ("name", "cnpj", "is_maintainer", "source_system", "layout_type", "has_logo", "is_active", "created_at")
    list_filter = ("is_maintainer", "source_system", "layout_type", "is_active")
    search_fields = ("name", "cnpj")

    @admin.display(boolean=True, description="Logo")
    def has_logo(self, obj: Empresa) -> bool:
        return bool(obj.logo)


@admin.register(Contato)
class ContatoAdmin(admin.ModelAdmin):
    form = ContatoForm
    list_display = ("name", "empresa", "user", "email", "phone", "is_active")
    list_filter = ("is_active", "empresa")
    search_fields = ("name", "email", "phone", "empresa__name", "user__username", "user__email")


@admin.register(UserEmpresaVinculo)
class UserEmpresaVinculoAdmin(admin.ModelAdmin):
    list_display = ("user", "empresa", "is_active", "created_at")
    list_filter = ("is_active", "empresa")
    search_fields = ("user__username", "user__email", "empresa__name", "empresa__cnpj")
