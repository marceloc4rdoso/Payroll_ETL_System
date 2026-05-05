from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("processor", "0005_billingorder_launch_date"),
    ]

    operations = [
        migrations.CreateModel(
            name="BillingClosure",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("year", models.PositiveIntegerField(verbose_name="Ano")),
                ("month", models.PositiveIntegerField(verbose_name="Mês")),
                (
                    "status",
                    models.CharField(
                        choices=[("OPEN", "Aberto"), ("CLOSED", "Fechado")],
                        default="OPEN",
                        max_length=16,
                        verbose_name="Status",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criado em")),
                ("closed_at", models.DateTimeField(blank=True, null=True, verbose_name="Fechado em")),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="billing_closures",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Criado por",
                    ),
                ),
                (
                    "empresa",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="billing_closures",
                        to="people.empresa",
                        verbose_name="Empresa",
                    ),
                ),
            ],
            options={
                "verbose_name": "Fechamento",
                "verbose_name_plural": "Fechamentos",
                "ordering": ["-year", "-month", "-created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="billingclosure",
            constraint=models.UniqueConstraint(fields=("empresa", "year", "month"), name="billing_unique_closure_per_company_month"),
        ),
        migrations.AddField(
            model_name="billingorder",
            name="closure",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="orders",
                to="processor.billingclosure",
                verbose_name="Fechamento",
            ),
        ),
    ]
