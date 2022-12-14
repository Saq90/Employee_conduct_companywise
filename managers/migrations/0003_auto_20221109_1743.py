# Generated by Django 3.1.6 on 2022-11-09 12:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0009_auto_20221109_1638'),
        ('managers', '0002_manager_company_staff'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='manager',
            name='company_staff',
        ),
        migrations.AlterField(
            model_name='manager',
            name='user',
            field=models.OneToOneField(default=True, on_delete=django.db.models.deletion.CASCADE, to='account.companystaff'),
        ),
    ]
