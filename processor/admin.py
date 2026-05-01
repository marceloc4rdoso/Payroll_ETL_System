from django.contrib import admin

from processor.models import Upload


@admin.register(Upload)
class UploadAdmin(admin.ModelAdmin):
    list_display = ("id", "empresa", "status", "row_count", "created_at", "processed_at")
    list_filter = ("status", "empresa")
    search_fields = ("id", "empresa__name", "empresa__cnpj")
    readonly_fields = ("created_at", "processed_at")
