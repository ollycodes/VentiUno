# Generated by Django 4.1.4 on 2023-01-04 22:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blackjack', '0008_alter_guestprofile_username'),
    ]

    operations = [
        migrations.AlterField(
            model_name='guestprofile',
            name='username',
            field=models.CharField(default='ExploitedEntity', max_length=24, unique=True),
        ),
    ]
