# Generated by Django 5.1.6 on 2025-03-04 05:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('medscanpro', '0004_scanrecord_count'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScanHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('barcode', models.CharField(max_length=255)),
                ('scan_time', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
