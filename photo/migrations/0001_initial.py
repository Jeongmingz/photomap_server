# Generated by Django 5.2 on 2025-04-16 11:25

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PhotoBrand',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('patten', models.CharField(max_length=1000)),
            ],
        ),
        migrations.CreateModel(
            name='Photo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=1000)),
                ('url', models.URLField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(db_column='userId', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('brand', models.ForeignKey(blank=True, db_column='brandId', null=True, on_delete=django.db.models.deletion.SET_NULL, to='photo.photobrand')),
            ],
        ),
        migrations.CreateModel(
            name='PhotoFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.URLField()),
                ('type', models.IntegerField()),
                ('order', models.IntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('photo', models.ForeignKey(db_column='photoId', on_delete=django.db.models.deletion.CASCADE, to='photo.photo')),
            ],
        ),
    ]
