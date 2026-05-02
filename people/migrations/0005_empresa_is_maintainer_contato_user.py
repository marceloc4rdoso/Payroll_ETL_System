from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("people", "0004_userempresavinculo"),
    ]

    operations = [
        migrations.AddField(
            model_name="empresa",
            name="is_maintainer",
            field=models.BooleanField(default=False, verbose_name="Mantenedora (Capybird)"),
        ),
        migrations.AddField(
            model_name="contato",
            name="user",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="contato",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Usuário",
            ),
        ),
    ]
