# Generated by Django 2.2.13 on 2020-07-02 08:38

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('indigo_api', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Editor',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('accepted_terms', models.BooleanField(default=False)),
                ('country', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='indigo_api.Country')),
                ('permitted_countries', models.ManyToManyField(blank=True, help_text='Countries the user can work with.', related_name='editors', to='indigo_api.Country')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Publication',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Name of this publication', max_length=512)),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='indigo_api.Country')),
            ],
            options={
                'ordering': ['name'],
                'unique_together': {('country', 'name')},
            },
        ),
    ]