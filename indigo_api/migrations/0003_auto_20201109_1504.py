# Generated by Django 2.2.13 on 2020-11-09 15:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0002_auto_20200702_0838'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='document',
            name='search_text',
        ),
        migrations.RemoveField(
            model_name='document',
            name='search_vector',
        ),
    ]