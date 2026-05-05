from django.contrib import admin

from processor.models import BillingClosure, BillingLine, BillingOrder, ServiceProduct, SourceSystem, Upload


def _is_capybird_admin(user) -> bool:
    if not (user.is_staff or user.is_superuser):
        return False
    contato = getattr(user, "contato", None)
    if contato and getattr(contato, "is_active", False) and getattr(getattr(contato, "empresa", None), "is_maintainer", False):
        return True
    vinculo = getattr(user, "empresa_vinculo", None)
    if vinculo and getattr(vinculo, "is_active", False) and getattr(getattr(vinculo, "empresa", None), "is_maintainer", False):
        return True
    return False


@admin.register(Upload)
class UploadAdmin(admin.ModelAdmin):
    list_display = ("id", "empresa", "status", "row_count", "created_at", "processed_at")
    list_filter = ("status", "empresa")
    search_fields = ("id", "empresa__name", "empresa__cnpj")
    readonly_fields = ("created_at", "processed_at")


@admin.register(SourceSystem)
class SourceSystemAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "code")


@admin.register(ServiceProduct)
class ServiceProductAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "product_type", "unit_price", "is_active", "created_at")
    list_filter = ("product_type", "is_active")
    search_fields = ("name", "code")

    def has_module_permission(self, request):
        return _is_capybird_admin(request.user)

    def has_view_permission(self, request, obj=None):
        return _is_capybird_admin(request.user)

    def has_add_permission(self, request):
        return _is_capybird_admin(request.user)

    def has_change_permission(self, request, obj=None):
        return _is_capybird_admin(request.user)

    def has_delete_permission(self, request, obj=None):
        return _is_capybird_admin(request.user)


class BillingLineInline(admin.TabularInline):
    model = BillingLine
    extra = 0

    def has_view_permission(self, request, obj=None):
        return _is_capybird_admin(request.user)

    def has_add_permission(self, request, obj=None):
        return _is_capybird_admin(request.user)

    def has_change_permission(self, request, obj=None):
        return _is_capybird_admin(request.user)

    def has_delete_permission(self, request, obj=None):
        return _is_capybird_admin(request.user)


@admin.register(BillingOrder)
class BillingOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "empresa", "status", "launch_date", "created_by", "created_at")
    list_filter = ("status", "empresa")
    search_fields = ("id", "empresa__name", "empresa__cnpj")
    inlines = [BillingLineInline]

    def has_module_permission(self, request):
        return _is_capybird_admin(request.user)

    def has_view_permission(self, request, obj=None):
        return _is_capybird_admin(request.user)

    def has_add_permission(self, request):
        return _is_capybird_admin(request.user)

    def has_change_permission(self, request, obj=None):
        return _is_capybird_admin(request.user)

    def has_delete_permission(self, request, obj=None):
        return _is_capybird_admin(request.user)


@admin.register(BillingClosure)
class BillingClosureAdmin(admin.ModelAdmin):
    list_display = ("empresa", "month", "year", "status", "created_by", "created_at", "closed_at")
    list_filter = ("status", "empresa", "year", "month")
    search_fields = ("empresa__name", "empresa__cnpj")

    def has_module_permission(self, request):
        return _is_capybird_admin(request.user)

    def has_view_permission(self, request, obj=None):
        return _is_capybird_admin(request.user)

    def has_add_permission(self, request):
        return _is_capybird_admin(request.user)

    def has_change_permission(self, request, obj=None):
        return _is_capybird_admin(request.user)

    def has_delete_permission(self, request, obj=None):
        return _is_capybird_admin(request.user)
