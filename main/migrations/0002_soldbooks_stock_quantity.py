# Generated by Django 4.1.6 on 2023-09-17 13:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='soldbooks',
            name='stock_quantity',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
    ]
