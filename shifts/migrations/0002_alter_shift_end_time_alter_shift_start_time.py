# Generated by Django 5.1.3 on 2024-12-01 22:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shifts', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shift',
            name='end_time',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='shift',
            name='start_time',
            field=models.TimeField(blank=True, null=True),
        ),
    ]
