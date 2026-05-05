from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("processor", "0006_billing_closure"),
    ]

    operations = [
        migrations.AddField(
            model_name="serviceproduct",
            name="is_default_for_uploads",
            field=models.BooleanField(default=False, verbose_name="Padrão para Uploads"),
        ),
        migrations.AddField(
            model_name="upload",
            name="billing_order",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="source_upload",
                to="processor.billingorder",
                verbose_name="Pedido",
            ),
        ),
    ]
