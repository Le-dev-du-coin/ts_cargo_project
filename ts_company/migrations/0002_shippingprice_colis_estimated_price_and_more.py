# Generated by Django 5.2.3 on 2025-07-02 02:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ts_company', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShippingPrice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('method', models.CharField(choices=[('EXPRESS_AERIEN', 'Vol Express (Aérien)'), ('NORMAL_AERIEN', 'Vol Normal (Aérien)'), ('MARITIME', 'Bateau (Maritime)')], max_length=20, unique=True)),
                ('price_per_kg', models.DecimalField(decimal_places=2, help_text='Prix par kg en F CFA', max_digits=10)),
                ('min_charge_weight', models.DecimalField(decimal_places=2, default=1.0, help_text='Poids minimum pour le calcul au kg', max_digits=10)),
                ('last_updated', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddField(
            model_name='colis',
            name='estimated_price',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Prix estimé en F CFA', max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='colis',
            name='shipping_method',
            field=models.CharField(choices=[('EXPRESS_AERIEN', 'Vol Express (Aérien)'), ('NORMAL_AERIEN', 'Vol Normal (Aérien)'), ('MARITIME', 'Bateau (Maritime)')], max_length=20),
        ),
    ]
