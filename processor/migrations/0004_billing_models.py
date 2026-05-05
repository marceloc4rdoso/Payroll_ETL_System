from decimal import Decimal

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("processor", "0003_sourcesystem_generated_at_sourcesystem_layout_spec_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="ServiceProduct",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=32, unique=True, verbose_name="Código")),
                ("name", models.CharField(max_length=120, verbose_name="Nome")),
                (
                    "product_type",
                    models.CharField(
                        choices=[("PER_RECORD", "Por registro"), ("FIXED", "Fixo")],
                        default="PER_RECORD",
                        max_length=16,
                        verbose_name="Tipo",
                    ),
                ),
                (
                    "unit_price",
                    models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12, verbose_name="Valor unitário"),
                ),
                ("is_active", models.BooleanField(default=True, verbose_name="Ativo")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criado em")),
            ],
            options={
                "verbose_name": "Produto/Serviço",
                "verbose_name_plural": "Produtos/Serviços",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="BillingOrder",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "status",
                    models.CharField(
                        choices=[("DRAFT", "Rascunho"), ("CLOSED", "Fechado")],
                        default="DRAFT",
                        max_length=16,
                        verbose_name="Status",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criado em")),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="billing_orders",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Criado por",
                    ),
                ),
                (
                    "empresa",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="billing_orders",
                        to="people.empresa",
                        verbose_name="Empresa",
                    ),
                ),
            ],
            options={
                "verbose_name": "Pedido",
                "verbose_name_plural": "Pedidos",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="BillingLine",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("manual_label", models.CharField(blank=True, max_length=160, verbose_name="Descrição manual")),
                ("quantity", models.PositiveIntegerField(default=0, verbose_name="Quantidade (registros)")),
                (
                    "unit_price",
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal("0.00"),
                        max_digits=12,
                        verbose_name="Valor unitário (snapshot)",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criado em")),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lines",
                        to="processor.billingorder",
                        verbose_name="Pedido",
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="lines",
                        to="processor.serviceproduct",
                        verbose_name="Produto/Serviço",
                    ),
                ),
                (
                    "upload",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="billing_lines",
                        to="processor.upload",
                        verbose_name="Upload",
                    ),
                ),
            ],
            options={
                "verbose_name": "Item do pedido",
                "verbose_name_plural": "Itens do pedido",
                "ordering": ["id"],
            },
        ),
    ]
