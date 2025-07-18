# Generated by Django 5.2.3 on 2025-07-05 02:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ts_company', '0007_colis_delivery_address'),
    ]

    operations = [
        migrations.AddField(
            model_name='colis',
            name='notification_lot_closed_sent',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='lot',
            name='numero_lot',
            field=models.CharField(max_length=50, unique=True),
        ),
    ]
