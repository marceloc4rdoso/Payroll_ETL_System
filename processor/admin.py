from django.contrib import admin

from processor.models import SourceSystem, Upload


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
