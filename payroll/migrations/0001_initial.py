# Generated by Django 3.1.6 on 2022-12-20 10:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('employee', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Salary',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('month', models.DateField()),
                ('basic', models.PositiveIntegerField(default=0)),
                ('da_percent', models.PositiveIntegerField(blank=True, default=0, null=True)),
                ('hra_percent', models.PositiveIntegerField(blank=True, default=0, null=True, verbose_name='House rent Allowance')),
                ('conveyance', models.PositiveIntegerField(blank=True, default=0, null=True)),
                ('bonuses', models.PositiveIntegerField(blank=True, default=0, null=True)),
                ('allowance', models.PositiveIntegerField(blank=True, default=0, null=True)),
                ('medical_allowance', models.PositiveIntegerField(blank=True, default=0, null=True)),
                ('tds', models.PositiveIntegerField(blank=True, default=0, null=True, verbose_name='Tax Deducted at Source (T.D.S.)')),
                ('esi', models.PositiveIntegerField(blank=True, default=0, null=True)),
                ('providence_fund', models.PositiveIntegerField(blank=True, default=0, null=True, verbose_name='Provident Fund')),
                ('leave', models.PositiveIntegerField(blank=True, default=0, null=True)),
                ('tax', models.PositiveIntegerField(blank=True, default=0, null=True)),
                ('labour_welfare', models.PositiveIntegerField(blank=True, default=0, null=True)),
                ('loan_repayment', models.PositiveIntegerField(blank=True, default=0, null=True)),
                ('others', models.PositiveIntegerField(blank=True, default=0, null=True)),
                ('employee', models.ForeignKey(blank=True, default=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='employee.employee')),
            ],
        ),
    ]
