from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone

from people.models import Empresa


def system_sample_path(instance: "SourceSystem", filename: str) -> str:
    return f"layout_samples/{instance.code}/{filename}"


class SourceSystem(models.Model):
    code = models.CharField("Código", max_length=32, unique=True)
    name = models.CharField("Nome", max_length=120)
    is_active = models.BooleanField("Ativo", default=True)
    sample_file = models.FileField("Arquivo modelo", upload_to=system_sample_path, null=True, blank=True)
    sample_sha256 = models.CharField("SHA-256 do modelo", max_length=64, blank=True)
    layout_spec = models.JSONField("Especificação do layout", null=True, blank=True)
    generated_at = models.DateTimeField("Gerado em", null=True, blank=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)

    class Meta:
        verbose_name = "Sistema"
        verbose_name_plural = "Sistemas"
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"

    @property
    def is_layout_ready(self) -> bool:
        return bool(self.layout_spec)


def upload_original_path(instance: "Upload", filename: str) -> str:
    dt = timezone.localdate()
    return f"uploads/{dt:%Y/%m/%d}/empresa_{instance.empresa_id}/{filename}"


def upload_output_path(instance: "Upload", filename: str) -> str:
    dt = timezone.localdate()
    return f"outputs/{dt:%Y/%m/%d}/empresa_{instance.empresa_id}/{filename}"


class Upload(models.Model):
    """
    Registro de histórico de processamento.

    Guarda o TXT original e os arquivos CSV gerados.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendente"
        PROCESSING = "PROCESSING", "Processando"
        DONE = "DONE", "Concluído"
        FAILED = "FAILED", "Falhou"

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name="uploads",
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payroll_uploads",
    )
    original_file = models.FileField("Arquivo TXT", upload_to=upload_original_path)

    detected_layout_type = models.CharField(
        "Layout aplicado",
        max_length=32,
        blank=True,
        help_text="Copia do layout_type da Empresa no momento do upload.",
    )
    status = models.CharField(
        "Status",
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    row_count = models.PositiveIntegerField("Linhas/Registros gerados", default=0)
    error_message = models.TextField("Erro", blank=True)

    web_csv = models.FileField(
        "CSV Web (1:1)",
        upload_to=upload_output_path,
        null=True,
        blank=True,
    )
    print_csv = models.FileField(
        "CSV Impressão (Dobra A/B)",
        upload_to=upload_output_path,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    processed_at = models.DateTimeField("Processado em", null=True, blank=True)

    class Meta:
        verbose_name = "Upload"
        verbose_name_plural = "Uploads"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["empresa", "created_at"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"Upload #{self.pk} ({self.empresa.name})"

    def mark_processing(self) -> None:
        self.status = self.Status.PROCESSING
        self.error_message = ""
        self.save(update_fields=["status", "error_message"])

    def mark_done(self, row_count: int) -> None:
        self.status = self.Status.DONE
        self.row_count = row_count
        self.processed_at = timezone.now()
        self.save(update_fields=["status", "row_count", "processed_at"])

    def mark_failed(self, message: str) -> None:
        self.status = self.Status.FAILED
        self.error_message = message
        self.processed_at = timezone.now()
        self.save(update_fields=["status", "error_message", "processed_at"])
