# Generated by Django 5.2 on 2025-04-16 06:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_alter_account_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='account',
            name='access_token',
        ),
        migrations.RemoveField(
            model_name='account',
            name='expires_at',
        ),
        migrations.RemoveField(
            model_name='account',
            name='id_token',
        ),
        migrations.RemoveField(
            model_name='account',
            name='refresh_token',
        ),
        migrations.RemoveField(
            model_name='account',
            name='refresh_token_expires_in',
        ),
        migrations.RemoveField(
            model_name='account',
            name='scope',
        ),
        migrations.RemoveField(
            model_name='account',
            name='session_state',
        ),
        migrations.RemoveField(
            model_name='account',
            name='token_type',
        ),
    ]
