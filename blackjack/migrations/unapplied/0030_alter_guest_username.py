# Generated by Django 4.1.4 on 2023-02-09 21:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blackjack', '0029_alter_guest_username'),
    ]

    operations = [
        migrations.AlterField(
            model_name='guest',
            name='username',
            field=models.CharField(default='SoftRobe', max_length=24, unique=True),
        ),
    ]
