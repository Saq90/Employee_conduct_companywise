# Generated by Django 3.1.6 on 2023-01-05 17:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('managers', '0003_auto_20230105_2231'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='manager',
            name='manager_department',
        ),
    ]