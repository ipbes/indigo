# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2020-04-22 12:39
from __future__ import unicode_literals

from lxml import etree

from django.db import migrations

from cobalt import Act, FrbrUri, datestring
from cobalt.uri import FRBR_URI_RE
from indigo.analysis.refs.base import BaseRefsFinder


def new_frbr_uri(uri, forward):
    """ Generates a cobalt FrbrUri object using all the existing URI's attributes.
        If `forward` is True, the optional /akn prefix is included; otherwise it isn't.
    """
    if not isinstance(uri, FrbrUri):
        uri = FrbrUri.parse(uri)
    prefix = None
    if forward:
        prefix = 'akn'

    return FrbrUri(
        prefix=prefix,
        country=uri.country,
        locality=uri.locality,
        doctype=uri.doctype,
        subtype=uri.subtype,
        actor=uri.actor,
        date=uri.date,
        number=uri.number,
        work_component=uri.work_component,
        language=uri.language,
        expression_date=uri.expression_date,
        expression_component=uri.expression_component,
        expression_subcomponent=uri.expression_subcomponent,
        format=uri.format
    )


def set_frbr_uri_meta_ident(doc, uri):
    """ Borrowed from frbr_uri.setter on StructuredDocument in cobalt.akn
        Sets the identification information in the meta block of an AKN document based on its FRBR URI.
    """
    if not isinstance(uri, FrbrUri):
        uri = FrbrUri.parse(uri)

    uri.language = doc.meta.identification.FRBRExpression.FRBRlanguage.get('language', 'eng')
    uri.expression_date = '@' + datestring(doc.expression_date)

    if uri.work_component is None:
        uri.work_component = 'main'

    # set URIs of the main document and components
    for component, element in doc.components().items():
        uri.work_component = component
        ident = element.find(f'.//{{{doc.namespace}}}meta/{{{doc.namespace}}}identification')

        ident.FRBRWork.FRBRuri.set('value', uri.uri())
        ident.FRBRWork.FRBRthis.set('value', uri.work_uri())
        ident.FRBRWork.FRBRcountry.set('value', uri.country)

        ident.FRBRExpression.FRBRuri.set('value', uri.expression_uri(False))
        ident.FRBRExpression.FRBRthis.set('value', uri.expression_uri())

        ident.FRBRManifestation.FRBRuri.set('value', uri.expression_uri(False))
        ident.FRBRManifestation.FRBRthis.set('value', uri.expression_uri())


class RefsFinderRef(BaseRefsFinder):
    """ Finds hrefs in documents, of the form:

        href="/za/act/2012/22">Act no 22 of 2012
        href="/akn/za/act/2012/22">Act no 22 of 2012

        and either adds or removes the /akn prefix, depending on what is passed to `handle_refs`

    """

    ancestors = ['meta', 'coverPage', 'preface', 'preamble', 'body', 'mainBody', 'conclusions']
    candidate_xpath = "//a:*[starts-with(@href, '/')]"
    pattern_re = FRBR_URI_RE

    def handle_refs(self, document, forward):
        root = etree.fromstring(document.document_xml)
        self.setup(root)

        for ancestor in self.ancestor_nodes(root):
            for node in self.candidate_nodes(ancestor):
                ref = node.get('href')
                match = self.pattern_re.match(ref)
                if match:
                    ref = str(new_frbr_uri(ref, forward))
                    node.set('href', ref)

        document.document_xml = etree.tostring(root, encoding='utf-8').decode('utf-8')


def migrate_uris(apps, schema_editor, forward):
    """ Start or stop using AKN3 FRBR URIs (i.e. /akn prefix)
    - Update URIs of all existing works and documents
    - Update meta/identification block of each AKN document
    - Update hrefs in all documents
    """
    db_alias = schema_editor.connection.alias
    Work = apps.get_model("indigo_api", "Work")
    Document = apps.get_model("indigo_api", "Document")

    for work in Work.objects.using(db_alias).all():
        work.frbr_uri = new_frbr_uri(work.frbr_uri, forward)
        work.save()

    for doc in Document.objects.using(db_alias).all():
        doc.frbr_uri = doc.work.frbr_uri
        cobalt_doc = Act(doc.document_xml)
        set_frbr_uri_meta_ident(cobalt_doc, doc.frbr_uri)
        doc.document_xml = cobalt_doc.to_xml()
        RefsFinderRef.handle_refs(RefsFinderRef(), doc, forward)
        doc.save()


def migrate_forward(apps, schema_editor):
    migrate_uris(apps, schema_editor, forward=True)


def migrate_backward(apps, schema_editor):
    migrate_uris(apps, schema_editor, forward=False)


class Migration(migrations.Migration):

    dependencies = [
        ('indigo_api', '0128_rename_badges'),
    ]

    operations = [
        migrations.RunPython(migrate_forward, migrate_backward),
    ]
