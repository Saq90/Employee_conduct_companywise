# Generated by Django 3.1.6 on 2022-11-07 10:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0006_auto_20221107_1541'),
        ('employee', '0002_auto_20221004_1610'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='company_staff',
            field=models.OneToOneField(default=True, on_delete=django.db.models.deletion.CASCADE, to='account.companystaff'),
        ),
    ]
