# Generated by Django 4.1.4 on 2023-02-09 21:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blackjack', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='guest',
            name='username',
            field=models.CharField(default='JumbledTrailer', max_length=24, unique=True),
        ),
        migrations.AlterField(
            model_name='table',
            name='last_played',
            field=models.TimeField(auto_now=True),
        ),
    ]