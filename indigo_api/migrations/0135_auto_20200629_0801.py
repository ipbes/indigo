# Generated by Django 2.2.13 on 2020-06-29 08:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0134_akn3_part2'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='workflow',
            options={'ordering': ('-priority', 'pk'), 'permissions': (('close_workflow', 'Can close a workflow'),)},
        ),
    ]
