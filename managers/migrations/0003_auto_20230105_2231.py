# Generated by Django 3.1.6 on 2023-01-05 17:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('employee', '0001_initial'),
        ('managers', '0002_auto_20230105_2219'),
    ]

    operations = [
        # migrations.AlterField(
        #     model_name='manager',
        #     name='manager_department',
        #     field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='employee.department'),
        # ),
    ]
