# Generated by Django 4.1.4 on 2023-02-09 20:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blackjack', '0024_alter_guest_username_alter_table_pending_players'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='table',
            name='pending_players',
        ),
        migrations.RemoveField(
            model_name='table',
            name='table_entry',
        ),
        migrations.AlterField(
            model_name='guest',
            name='username',
            field=models.CharField(default='SoggyCoconut', max_length=24, unique=True),
        ),
    ]
