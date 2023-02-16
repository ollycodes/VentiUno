# Generated by Django 4.1.4 on 2023-02-09 20:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blackjack', '0020_alter_guest_username_alter_table_pending_players'),
    ]

    operations = [
        migrations.AlterField(
            model_name='guest',
            name='username',
            field=models.CharField(default='ExpressNonsense', max_length=24, unique=True),
        ),
        migrations.AlterField(
            model_name='table',
            name='pending_players',
            field=models.JSONField(blank=True, default={}, null=True),
        ),
    ]
