# Generated by Django 2.2.12 on 2020-10-30 09:19

from django.conf import settings
import django.contrib.postgres.fields
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import django_fsm
import indigo_api.models.works


class Migration(migrations.Migration):

    replaces = [('indigo_api', '0073_renamed_localities_related'), ('indigo_api', '0074_document_view_source_perm'), ('indigo_api', '0075_work_locality'), ('indigo_api', '0076_work_locality_blank'), ('indigo_api', '0077_work_publication_document'), ('indigo_api', '0078_task_workflow'), ('indigo_api', '0079_rename_task_fields'), ('indigo_api', '0080_task_fields_added'), ('indigo_api', '0081_task_labels'), ('indigo_api', '0082_task_fields_removed'), ('indigo_api', '0083_task_label_ordering'), ('indigo_api', '0084_link_places_to_works'), ('indigo_api', '0085_annotation_task'), ('indigo_api', '0086_workflows'), ('indigo_api', '0087_workflows_closed'), ('indigo_api', '0088_workflow_due_date'), ('indigo_api', '0089_remove_workflow_closed_by_user'), ('indigo_api', '0090_publication_doc_filename'), ('indigo_api', '0091_task_last_assigned_to'), ('indigo_api', '0092_publicationdocument_trusted_url'), ('indigo_api', '0093_work_stub'), ('indigo_api', '0094_remove_document_stub'), ('indigo_api', '0095_pub_doc_size_null'), ('indigo_api', '0096_auto_20190424_1245'), ('indigo_api', '0097_workproperty'), ('indigo_api', '0098_task_closed_by_user_code'), ('indigo_api', '0099_populate_task_closed_by'), ('indigo_api', '0100_remove_whitespace'), ('indigo_api', '0101_taxonomies'), ('indigo_api', '0102_changes_requested'), ('indigo_api', '0103_add_extra_data_field'), ('indigo_api', '0104_task_closed_at'), ('indigo_api', '0105_backfill_task_last_assigned_to'), ('indigo_api', '0106_rename_task_fields'), ('indigo_api', '0107_taxonomy_tweaks'), ('indigo_api', '0108_place_settings'), ('indigo_api', '0109_backfill_place_settings'), ('indigo_api', '0110_django3_tweaks'), ('indigo_api', '0111_placesettings_styleguide_url'), ('indigo_api', '0112_arbitrary_expression_date'), ('indigo_api', '0113_work_properties'), ('indigo_api', '0114_migrate_work_properties'), ('indigo_api', '0115_drop_work_property'), ('indigo_api', '0116_work_props_perms'), ('indigo_api', '0117_amendments_made'), ('indigo_api', '0118_work_commenced'), ('indigo_api', '0119_migrate_work_commenced'), ('indigo_api', '0120_bulk_export_work_permission'), ('indigo_api', '0121_country_italics_terms'), ('indigo_api', '0122_annotation_selectors'), ('indigo_api', '0123_remove_task_anchor_id'), ('indigo_api', '0124_commencement'), ('indigo_api', '0125_migrate_commencements'), ('indigo_api', '0126_drop_commencement_details_from_work'), ('indigo_api', '0127_add_close_any_task_permission'), ('indigo_api', '0128_rename_badges'), ('indigo_api', '0129_workflow_priority'), ('indigo_api', '0130_migrate_refs_uris'), ('indigo_api', '0131_migrate_namespaces'), ('indigo_api', '0132_migrate_ids_eIds'), ('indigo_api', '0133_migrate_commencement_provisions'), ('indigo_api', '0134_akn3_part2'), ('indigo_api', '0135_auto_20201023_1407')]

    dependencies = [
        ('indigo_api', '0072_import_locality_from_indigo_app'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('pinax_badges', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='locality',
            name='country',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='localities', to='indigo_api.Country'),
        ),
        migrations.AlterModelOptions(
            name='document',
            options={'permissions': (('publish_document', 'Can publish and edit non-draft documents'), ('view_published_document', 'Can view publish documents through the API'), ('view_document_xml', 'Can view the source XML of documents'))},
        ),
        migrations.AddField(
            model_name='work',
            name='locality',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='works', to='indigo_api.Locality'),
        ),
        migrations.CreateModel(
            name='TaskLabel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=30, unique=True)),
                ('slug', models.SlugField(unique=True)),
                ('description', models.CharField(blank=True, max_length=256, null=True)),
            ],
            options={
                'ordering': ['title'],
            },
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=256)),
                ('description', models.TextField(blank=True, null=True)),
                ('state', django_fsm.FSMField(default='open', max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_tasks', to=settings.AUTH_USER_MODEL)),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='indigo_api.Country')),
                ('created_by_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('document', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='indigo_api.Document')),
                ('locality', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='indigo_api.Locality')),
                ('updated_by_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('work', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='indigo_api.Work')),
                ('labels', models.ManyToManyField(related_name='tasks', to='indigo_api.TaskLabel')),
                ('submitted_by_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='submitted_tasks', to=settings.AUTH_USER_MODEL)),
                ('reviewed_by_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_tasks', to=settings.AUTH_USER_MODEL)),
                ('code', models.CharField(blank=True, max_length=100, null=True)),
                ('changes_requested', models.BooleanField(default=False, help_text='Have changes been requested on this task?')),
                ('extra_data', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('closed_at', models.DateTimeField(help_text='When the task was marked as done or cancelled.', null=True)),
            ],
            options={
                'permissions': (('submit_task', 'Can submit an open task for review'), ('cancel_task', 'Can cancel a task that is open or has been submitted for review'), ('reopen_task', 'Can reopen a task that is closed or cancelled'), ('unsubmit_task', 'Can unsubmit a task that has been submitted for review'), ('close_task', 'Can close a task that has been submitted for review'), ('close_any_task', 'Can close any task that has been submitted for review, regardless of who submitted it')),
            },
        ),
        migrations.AlterField(
            model_name='work',
            name='country',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='works', to='indigo_api.Country'),
        ),
        migrations.AlterModelOptions(
            name='work',
            options={'permissions': (('review_work', 'Can review work details'),)},
        ),
        migrations.AddField(
            model_name='work',
            name='stub',
            field=models.BooleanField(default=False, help_text='Stub works do not have content or points in time'),
        ),
        migrations.CreateModel(
            name='TaxonomyVocabulary',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('authority', models.CharField(help_text='Organisation managing this taxonomy', max_length=30, unique=True)),
                ('name', models.CharField(help_text='Short name for this taxonomy, under this authority', max_length=30, unique=True)),
                ('slug', models.SlugField(help_text='Code used in the API', unique=True)),
                ('title', models.CharField(help_text='Friendly, full title for the taxonomy', max_length=30, unique=True)),
            ],
            options={
                'verbose_name': 'Taxonomy',
                'verbose_name_plural': 'Taxonomies',
            },
        ),
        migrations.CreateModel(
            name='VocabularyTopic',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level_1', models.CharField(max_length=30)),
                ('level_2', models.CharField(blank=True, help_text='(optional)', max_length=30, null=True)),
                ('vocabulary', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='topics', to='indigo_api.TaxonomyVocabulary')),
            ],
            options={
                'unique_together': {('level_1', 'level_2', 'vocabulary')},
            },
        ),
        migrations.AddField(
            model_name='work',
            name='taxonomies',
            field=models.ManyToManyField(related_name='works', to='indigo_api.VocabularyTopic'),
        ),
        migrations.AlterModelOptions(
            name='attachment',
            options={'ordering': ('filename',)},
        ),
        migrations.AlterModelOptions(
            name='subtype',
            options={'ordering': ('name',), 'verbose_name': 'Document subtype'},
        ),
        migrations.AlterField(
            model_name='amendment',
            name='amending_work',
            field=models.ForeignKey(help_text='Work making the amendment.', on_delete=django.db.models.deletion.CASCADE, related_name='+', to='indigo_api.Work'),
        ),
        migrations.AlterField(
            model_name='colophon',
            name='name',
            field=models.CharField(help_text='Name of this colophon', max_length=1024),
        ),
        migrations.AlterField(
            model_name='country',
            name='primary_language',
            field=models.ForeignKey(help_text='Primary language for this country', on_delete=django.db.models.deletion.PROTECT, related_name='+', to='indigo_api.Language'),
        ),
        migrations.AlterField(
            model_name='document',
            name='deleted',
            field=models.BooleanField(default=False, help_text='Has this document been deleted?'),
        ),
        migrations.AlterField(
            model_name='document',
            name='draft',
            field=models.BooleanField(default=True, help_text="Drafts aren't available through the public API"),
        ),
        migrations.AlterField(
            model_name='document',
            name='expression_date',
            field=models.DateField(help_text='Date of publication or latest amendment'),
        ),
        migrations.AlterField(
            model_name='document',
            name='frbr_uri',
            field=models.CharField(default='/', help_text='Used globally to identify this work', max_length=512),
        ),
        migrations.AlterField(
            model_name='document',
            name='language',
            field=models.ForeignKey(help_text='Language this document is in.', on_delete=django.db.models.deletion.PROTECT, to='indigo_api.Language'),
        ),
        migrations.AlterField(
            model_name='locality',
            name='code',
            field=models.CharField(help_text='Unique code of this locality (used in the FRBR URI)', max_length=100),
        ),
        migrations.AlterField(
            model_name='locality',
            name='name',
            field=models.CharField(help_text='Local name of this locality', max_length=512),
        ),
        migrations.AlterField(
            model_name='subtype',
            name='abbreviation',
            field=models.CharField(help_text='Short abbreviation to use in FRBR URI. No punctuation.', max_length=20, unique=True),
        ),
        migrations.AlterField(
            model_name='subtype',
            name='name',
            field=models.CharField(help_text='Name of the document subtype', max_length=1024),
        ),
        migrations.AlterField(
            model_name='work',
            name='commencing_work',
            field=models.ForeignKey(blank=True, help_text='Date that marked this work as commenced', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='commenced_works', to='indigo_api.Work'),
        ),
        migrations.AlterField(
            model_name='work',
            name='parent_work',
            field=models.ForeignKey(blank=True, help_text='Parent related work', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='child_works', to='indigo_api.Work'),
        ),
        migrations.AlterField(
            model_name='work',
            name='publication_date',
            field=models.DateField(blank=True, help_text='Date of publication', null=True),
        ),
        migrations.AlterField(
            model_name='work',
            name='repealed_by',
            field=models.ForeignKey(blank=True, help_text='Work that repealed this work', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='repealed_works', to='indigo_api.Work'),
        ),
        migrations.AlterField(
            model_name='work',
            name='repealed_date',
            field=models.DateField(blank=True, help_text='Date of repeal of this work', null=True),
        ),
        migrations.AlterField(
            model_name='work',
            name='title',
            field=models.CharField(default='(untitled)', max_length=1024, null=True),
        ),
        migrations.CreateModel(
            name='PlaceSettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('spreadsheet_url', models.URLField(blank=True, null=True)),
                ('as_at_date', models.DateField(blank=True, null=True)),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='place_settings', to='indigo_api.Country')),
                ('locality', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='place_settings', to='indigo_api.Locality')),
                ('styleguide_url', models.URLField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ArbitraryExpressionDate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(help_text='Arbitrary date, e.g. consolidation date')),
                ('description', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('updated_by_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('work', models.ForeignKey(help_text='Work', on_delete=django.db.models.deletion.CASCADE, related_name='arbitrary_expression_dates', to='indigo_api.Work')),
            ],
            options={
                'ordering': ['date'],
                'unique_together': {('date', 'work')},
            },
        ),
        migrations.AddField(
            model_name='work',
            name='properties',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=dict),
        ),
        migrations.RemoveField(
            model_name='document',
            name='stub',
        ),
        migrations.AlterModelOptions(
            name='work',
            options={'permissions': (('review_work', 'Can review work details'), ('bulk_add_work', 'Can import works in bulk'))},
        ),
        migrations.AlterField(
            model_name='work',
            name='properties',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name='amendment',
            name='amending_work',
            field=models.ForeignKey(help_text='Work making the amendment.', on_delete=django.db.models.deletion.CASCADE, related_name='amendments_made', to='indigo_api.Work'),
        ),
        migrations.AddField(
            model_name='work',
            name='commenced',
            field=models.BooleanField(default=False, help_text='Has this work commenced? (Date may be unknown)'),
        ),
        migrations.AlterModelOptions(
            name='documentactivity',
            options={'ordering': ('created_at',)},
        ),
        migrations.AlterModelOptions(
            name='work',
            options={'permissions': (('review_work', 'Can review work details'), ('bulk_add_work', 'Can import works in bulk'), ('bulk_export_work', 'Can export works in bulk'))},
        ),
        migrations.AddField(
            model_name='country',
            name='italics_terms',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=1024), blank=True, null=True, size=None),
        ),
        migrations.AddField(
            model_name='annotation',
            name='selectors',
            field=django.contrib.postgres.fields.jsonb.JSONField(null=True),
        ),
        migrations.CreateModel(
            name='Commencement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(blank=True, help_text='Date of the commencement, or null if it is unknown', null=True)),
                ('main', models.BooleanField(default=False, help_text='This commencement date is the date on which most of the provisions of the principal work come into force')),
                ('all_provisions', models.BooleanField(default=False, help_text='All provisions of this work commenced on this date')),
                ('provisions', django.contrib.postgres.fields.jsonb.JSONField(default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('commenced_work', models.ForeignKey(help_text='Principal work being commenced', on_delete=django.db.models.deletion.CASCADE, related_name='commencements', to='indigo_api.Work')),
                ('commencing_work', models.ForeignKey(help_text='Work that provides the commencement date for the principal work', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='commencements_made', to='indigo_api.Work')),
                ('created_by_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('updated_by_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['date'],
                'unique_together': {('commenced_work', 'commencing_work', 'date')},
            },
        ),
        migrations.RemoveField(
            model_name='work',
            name='commencement_date',
        ),
        migrations.RemoveField(
            model_name='work',
            name='commencing_work',
        ),
        migrations.CreateModel(
            name='PublicationDocument',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to=indigo_api.models.works.publication_document_filename)),
                ('size', models.IntegerField(null=True)),
                ('filename', models.CharField(max_length=255)),
                ('mime_type', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('work', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='publication_document', to='indigo_api.Work')),
                ('trusted_url', models.URLField(blank=True, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='annotation',
            name='task',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='annotation', to='indigo_api.Task'),
        ),
        migrations.AlterField(
            model_name='amendment',
            name='amended_work',
            field=models.ForeignKey(help_text='Work amended.', on_delete=django.db.models.deletion.CASCADE, related_name='amendments', to='indigo_api.Work'),
        ),
        migrations.AlterField(
            model_name='amendment',
            name='date',
            field=models.DateField(help_text='Date of the amendment'),
        ),
        migrations.AlterField(
            model_name='attachment',
            name='filename',
            field=models.CharField(db_index=True, help_text='Unique attachment filename', max_length=255),
        ),
        migrations.AlterField(
            model_name='colophon',
            name='country',
            field=models.ForeignKey(help_text='Which country does this colophon apply to?', on_delete=django.db.models.deletion.CASCADE, to='indigo_api.Country'),
        ),
        migrations.CreateModel(
            name='Workflow',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=256)),
                ('description', models.TextField(blank=True, null=True)),
                ('tasks', models.ManyToManyField(related_name='workflows', to='indigo_api.Task')),
                ('country', models.ForeignKey(default=3, on_delete=django.db.models.deletion.CASCADE, related_name='workflows', to='indigo_api.Country')),
                ('created_at', models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now)),
                ('created_by_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('locality', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='workflows', to='indigo_api.Locality')),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('updated_by_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('closed', models.BooleanField(default=False)),
                ('due_date', models.DateField(blank=True, null=True)),
                ('priority', models.BooleanField(db_index=True, default=False)),
            ],
            options={
                'permissions': (('close_workflow', 'Can close a workflow'),),
                'ordering': ('-priority', 'pk'),
            },
        ),
    ]
