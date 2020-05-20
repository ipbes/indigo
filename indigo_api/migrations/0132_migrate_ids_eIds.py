# Generated by Django 2.2.12 on 2020-05-16 12:33

import json
from reversion.models import Version

from django.contrib.contenttypes.models import ContentType
from django.db import migrations

from indigo_api.data_migrations import UnnumberedParagraphsToHcontainer, ComponentSchedulesToAttachments, AKNeId

from cobalt import Act


def forward(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    Document = apps.get_model("indigo_api", "Document")
    ct_doc = ContentType.objects.get_for_model(Document)
    para_to_hcontainer = UnnumberedParagraphsToHcontainer()
    component_to_attachment = ComponentSchedulesToAttachments()
    eid_migration = AKNeId()

    def update_xml(xml):
        cobalt_doc = Act(xml)
        para_to_hcontainer.migrate_act(cobalt_doc)
        component_to_attachment.migrate_act(cobalt_doc)
        eid_migration.migrate_act(cobalt_doc)
        return cobalt_doc.to_xml().decode("utf-8")

    for document in Document.objects.using(db_alias).all():
        document.document_xml = update_xml(document.document_xml)
        document.save()

        # Update historical Document versions
        for version in Version.objects.filter(content_type=ct_doc.pk)\
                .filter(object_id=document.pk).using(db_alias).all():
            data = json.loads(version.serialized_data)
            data[0]['fields']['document_xml'] = update_xml(data[0]['fields']['document_xml'])
            version.serialized_data = json.dumps(data)
            version.save()


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0131_migrate_namespaces'),
    ]

    operations = [
        migrations.RunPython(forward),
    ]
