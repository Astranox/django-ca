# Generated by Django 2.1.4 on 2018-12-08 17:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_ca', '0010_auto_20181128_2054'),
    ]

    operations = [
        migrations.AlterField(
            model_name='certificateauthority',
            name='issuer_alt_name',
            field=models.CharField(blank=True, default='', help_text='URL for your CA.', max_length=255, verbose_name='issuerAltName'),
        ),
    ]
