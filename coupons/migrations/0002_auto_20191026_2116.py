# Generated by Django 2.2.6 on 2019-10-26 21:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coupons', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coupon',
            name='expires',
            field=models.DateField(null=True),
        ),
    ]
