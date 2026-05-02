import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models


def empresa_logo_path(instance: "Empresa", filename: str) -> str:
    cnpj = (instance.cnpj or "sem_cnpj").strip() or "sem_cnpj"
    return f"company_logos/{cnpj}/{filename}"


class Empresa(models.Model):
    """
    Cadastro de empresas/clientes do sistema (multi-empresa).

    Observação: a spec.md não define todos os campos de cadastro, então este modelo
    cobre o mínimo necessário para amarrar Uploads -> Empresa e selecionar o layout.
    """

    class LayoutType(models.TextChoices):
        FOLHAMATIC = "FOLHAMATIC", "Folhamatic"
        RMLABORE_DEFAULT = "RMLABORE_DEFAULT", "RM Labore (Default)"
        RMLABORE_CUSTOM = "RMLABORE_CUSTOM", "RM Labore (Custom)"
        GENESIS = "GENESIS", "Genesis"
        CONTIMATIC = "CONTIMATIC", "Contimatic"

    name = models.CharField("Razão social / Nome", max_length=150)
    city = models.CharField("Cidade", max_length=80, blank=True)
    state = models.CharField("UF", max_length=2, blank=True)
    cnpj = models.CharField(
        "CNPJ (14 dígitos)",
        max_length=14,
        unique=True,
        validators=[RegexValidator(r"^\d{14}$", message="Informe 14 dígitos para o CNPJ.")],
        help_text="Armazenado somente com dígitos (ex.: 11437239000140).",
    )
    layout_type = models.CharField("Layout do TXT", max_length=32, default=LayoutType.RMLABORE_DEFAULT)
    source_system = models.ForeignKey(
        "processor.SourceSystem",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="empresas",
        verbose_name="Sistema de origem",
    )
    logo = models.FileField("Logo", upload_to=empresa_logo_path, null=True, blank=True)
    is_maintainer = models.BooleanField("Mantenedora (Capybird)", default=False)
    is_active = models.BooleanField("Ativo", default=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(cnpj=""),
                name="people_empresa_cnpj_not_empty",
            )
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def sistema_nome(self) -> str:
        if self.source_system:
            return self.source_system.name
        known = dict(self.LayoutType.choices)
        return known.get(self.layout_type, self.layout_type)

    @staticmethod
    def normalize_cnpj(value: str) -> str:
        return re.sub(r"\D", "", value or "")

    def clean(self) -> None:
        super().clean()
        self.cnpj = self.normalize_cnpj(self.cnpj)
        if self.cnpj and len(self.cnpj) != 14:
            raise ValidationError({"cnpj": "CNPJ deve ter 14 dígitos."})
        if self.source_system:
            self.layout_type = self.source_system.code


class Contato(models.Model):
    """
    Contatos vinculados à empresa (ex.: responsável pelo envio, financeiro, RH).
    """

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name="contatos",
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contato",
        verbose_name="Usuário",
    )
    name = models.CharField("Nome", max_length=120)
    email = models.EmailField("E-mail", blank=True)
    phone = models.CharField("Telefone", max_length=30, blank=True)
    role = models.CharField("Cargo/Função", max_length=80, blank=True)
    is_active = models.BooleanField("Ativo", default=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)

    class Meta:
        verbose_name = "Contato"
        verbose_name_plural = "Contatos"
        indexes = [
            models.Index(fields=["empresa", "name"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.empresa.name})"


class UserEmpresaVinculo(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="empresa_vinculo",
        verbose_name="Usuário",
    )
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name="usuarios_vinculados",
        verbose_name="Empresa vinculada",
    )
    is_active = models.BooleanField("Ativo", default=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)

    class Meta:
        verbose_name = "Vínculo Usuário → Empresa"
        verbose_name_plural = "Vínculos Usuário → Empresa"
        indexes = [
            models.Index(fields=["empresa", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.user} → {self.empresa}"
