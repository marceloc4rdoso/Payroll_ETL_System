from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):
    dependencies = [
        ("processor", "0004_billing_models"),
    ]

    operations = [
        migrations.AddField(
            model_name="billingorder",
            name="launch_date",
            field=models.DateField(default=timezone.localdate, verbose_name="Data de lançamento"),
        ),
    ]
