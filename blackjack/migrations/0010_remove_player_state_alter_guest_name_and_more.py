# Generated by Django 4.1.7 on 2023-04-02 22:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blackjack', '0009_remove_player_card_back_alter_guest_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='player',
            name='state',
        ),
        migrations.AlterField(
            model_name='guest',
            name='name',
            field=models.CharField(default='PiousPossession', max_length=24, unique=True),
        ),
        migrations.AlterField(
            model_name='player',
            name='bet',
            field=models.PositiveIntegerField(default=0),
        ),
    ]