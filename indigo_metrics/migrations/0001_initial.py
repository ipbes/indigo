# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-02-11 12:00
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('indigo_api', '0089_remove_workflow_closed_by_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkMetrics',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('n_languages', models.IntegerField(help_text=b'Number of languages in published documents', null=True)),
                ('n_expressions', models.IntegerField(help_text=b'Number of published documents', null=True)),
                ('n_points_in_time', models.IntegerField(help_text=b'Number of recorded points in time', null=True)),
                ('n_expected_expressions', models.IntegerField(help_text=b'Expected number of published documents', null=True)),
                ('work', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='metrics', to='indigo_api.Work')),
            ],
        ),
    ]
