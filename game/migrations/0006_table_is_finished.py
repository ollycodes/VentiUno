# Generated by Django 4.1.3 on 2022-11-10 22:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0005_rename_game_table'),
    ]

    operations = [
        migrations.AddField(
            model_name='table',
            name='is_finished',
            field=models.BooleanField(default=False),
        ),
    ]
