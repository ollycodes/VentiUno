# Generated by Django 4.1.4 on 2022-12-14 16:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blackjack', '0002_remove_guestprofile_guest_username_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='guestprofile',
            name='username',
            field=models.CharField(default='AvianColt', max_length=24, unique=True),
        ),
    ]