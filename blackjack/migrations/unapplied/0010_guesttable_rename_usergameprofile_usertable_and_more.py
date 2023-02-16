# Generated by Django 4.1.4 on 2023-01-06 22:13

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('blackjack', '0009_alter_guestprofile_username'),
    ]

    operations = [
        migrations.CreateModel(
            name='GuestTable',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(default='WorthReading', max_length=24, unique=True)),
                ('game_data', models.JSONField()),
            ],
        ),
        migrations.RenameModel(
            old_name='UserGameProfile',
            new_name='UserTable',
        ),
        migrations.DeleteModel(
            name='GuestProfile',
        ),
    ]