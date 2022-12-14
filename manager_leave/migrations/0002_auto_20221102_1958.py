# Generated by Django 3.1.6 on 2022-11-02 14:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager_leave', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='managerleave',
            name='balancedays',
            field=models.PositiveIntegerField(blank=True, default=10, null=True, verbose_name='Leave days per year counter'),
        ),
    ]
