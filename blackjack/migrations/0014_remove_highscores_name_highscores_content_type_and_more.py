# Generated by Django 4.1.7 on 2023-04-05 21:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('blackjack', '0013_highscores_player_biggest_bet_alter_guest_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='highscores',
            name='name',
        ),
        migrations.AddField(
            model_name='highscores',
            name='content_type',
            field=models.ForeignKey(default=0, limit_choices_to={'model__in': ('guest', 'userproxy')}, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='highscores',
            name='object_id',
            field=models.PositiveIntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='highscores',
            name='table',
            field=models.PositiveIntegerField(default=1),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='guest',
            name='name',
            field=models.CharField(default='SacrilegiousTear', max_length=24, unique=True),
        ),
        migrations.AlterField(
            model_name='player',
            name='high_score',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
