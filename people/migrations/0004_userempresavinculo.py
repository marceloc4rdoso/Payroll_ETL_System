from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("people", "0003_empresa_source_system_alter_empresa_layout_type"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserEmpresaVinculo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_active", models.BooleanField(default=True, verbose_name="Ativo")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criado em")),
                (
                    "empresa",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="usuarios_vinculados", to="people.empresa", verbose_name="Empresa vinculada"),
                ),
                (
                    "user",
                    models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="empresa_vinculo", to=settings.AUTH_USER_MODEL, verbose_name="Usuário"),
                ),
            ],
            options={
                "verbose_name": "Vínculo Usuário → Empresa",
                "verbose_name_plural": "Vínculos Usuário → Empresa",
            },
        ),
        migrations.AddIndex(
            model_name="userempresavinculo",
            index=models.Index(fields=["empresa", "is_active"], name="people_user_empresa_5ec45f_idx"),
        ),
    ]
