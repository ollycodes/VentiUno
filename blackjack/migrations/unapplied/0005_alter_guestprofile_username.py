# Generated by Django 4.1.4 on 2022-12-14 16:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blackjack', '0004_alter_guestprofile_username'),
    ]

    operations = [
        migrations.AlterField(
            model_name='guestprofile',
            name='username',
            field=models.CharField(default='BacterialCoincidence', max_length=24, unique=True),
        ),
    ]