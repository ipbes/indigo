import re
import logging

from django.http import Http404
from django.shortcuts import get_object_or_404
from django.template.loader import find_template, render_to_string, TemplateDoesNotExist

from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.reverse import reverse
from rest_framework import mixins, viewsets, renderers
from rest_framework.response import Response
from rest_framework.decorators import detail_route
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly
import lxml.etree as ET
from lxml.etree import LxmlError

from .models import Document
from .serializers import DocumentSerializer, AkomaNtosoRenderer, ConvertSerializer
from .importer import Importer
from cobalt import FrbrUri
from cobalt.render import HTMLRenderer

log = logging.getLogger(__name__)

FORMAT_RE = re.compile('\.([a-z0-9]+)$')


def document_to_html(document):
    """ Render an entire document to HTML. """
    # use this to render the bulk of the document with the Cobalt XSLT renderer
    renderer = HTMLRenderer(act=document.doc)
    body_html = renderer.render_xml(document.document_xml)

    # find
    template_name = find_document_template(document)

    # and then render some boilerplate around it
    return render_to_string(template_name, {
        'document': document,
        'content_html': body_html,
        'renderer': renderer,
    })


def find_document_template(document):
    """ Return the filename of a template to use to render this document.

    This takes into account the country, type, subtype and language of the document,
    providing a number of opportunities to adjust the rendering logic.
    """
    uri = document.doc.frbr_uri
    doctype = uri.doctype

    options = []
    if uri.subtype:
        options.append('_'.join([doctype, uri.subtype, document.language, uri.country]))
        options.append('_'.join([doctype, uri.subtype, document.language]))
        options.append('_'.join([doctype, uri.subtype, uri.country]))
        options.append('_'.join([doctype, uri.subtype]))

    options.append('_'.join([doctype, document.language, uri.country]))
    options.append('_'.join([doctype, document.language]))
    options.append('_'.join([doctype, uri.country]))
    options.append(doctype)

    options = [f + '.html' for f in options]

    for option in options:
        try:
            if find_template(option):
                return option
        except TemplateDoesNotExist:
            pass

    raise ValueError("Couldn't find a template to use for %s. Tried: %s" % (uri, ', '.join(options)))


class DocumentViewMixin(object):
    def table_of_contents(self, document):
        # this updates the TOC entries by adding a 'url' component
        # based on the document's URI and the path of the TOC subcomponent
        uri = document.doc.frbr_uri
        toc = document.table_of_contents()

        def add_url(item):
            uri.expression_component = item['component']
            uri.expression_subcomponent = item.get('subcomponent')

            item['url'] = reverse(
                'published-document-detail',
                request=self.request,
                kwargs={'frbr_uri': uri.expression_uri()[1:]})

            for kid in item.get('children', []):
                add_url(kid)

        for item in toc:
            add_url(item)

        return toc


# Read/write REST API
class DocumentViewSet(DocumentViewMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows Documents to be viewed or edited.
    """
    queryset = Document.objects.filter(deleted__exact=False).prefetch_related('tags').all()
    serializer_class = DocumentSerializer
    permission_classes = (DjangoModelPermissionsOrAnonReadOnly,)

    def perform_destroy(self, instance):
        instance.deleted = True
        instance.save()

    @detail_route(methods=['GET', 'PUT'])
    def content(self, request, *args, **kwargs):
        """ This exposes a GET and PUT resource at ``/api/documents/1/content`` which allows
        the content of the document to be fetched and set independently of the metadata. This
        is useful because the content can be large.
        """
        instance = self.get_object()

        if request.method == 'GET':
            return Response({'content': self.get_object().document_xml})

        if request.method == 'PUT':
            try:
                instance.reset_xml(request.data.get('content'))
                instance.save()
            except LxmlError as e:
                raise ValidationError({'content': ["Invalid XML: %s" % e.message]})

            return Response({'content': instance.document_xml})

    @detail_route(methods=['GET'])
    def toc(self, request, *args, **kwargs):
        """ This exposes a GET resource at ``/api/documents/1/toc`` which gives
        a table of contents for the document.
        """
        return Response({'toc': self.table_of_contents(self.get_object())})


class PublishedDocumentDetailView(DocumentViewMixin,
                                  mixins.RetrieveModelMixin,
                                  mixins.ListModelMixin,
                                  viewsets.GenericViewSet):
    """
    The public read-only API for viewing and listing documents by FRBR URI.
    """
    queryset = Document.objects.filter(draft=False)
    serializer_class = DocumentSerializer
    # these determine what content negotiation takes place
    renderer_classes = (renderers.JSONRenderer, AkomaNtosoRenderer, renderers.StaticHTMLRenderer)

    def initial(self, request, **kwargs):
        super(PublishedDocumentDetailView, self).initial(request, **kwargs)
        # ensure the URI starts with a slash
        self.kwargs['frbr_uri'] = '/' + self.kwargs['frbr_uri']

    def get(self, request, **kwargs):
        # try parse it as an FRBR URI, if that succeeds, we'll lookup the document
        # that document matches, otherwise we'll assume they're trying to
        # list documents with a prefix URI match.
        try:
            self.frbr_uri = FrbrUri.parse(self.kwargs['frbr_uri'])

            # in a URL like
            #
            #   /act/1980/1/toc
            #
            # don't mistake 'toc' for a language, it's really equivalent to
            #
            #   /act/1980/1/eng/toc
            #
            # if eng is the default language.
            if self.frbr_uri.language == 'toc':
                self.frbr_uri.language = self.frbr_uri.default_language
                self.frbr_uri.expression_component = 'toc'

            return self.retrieve(request)
        except ValueError:
            return self.list(request)

    def list(self, request):
        # force JSON for list view
        self.request.accepted_renderer = renderers.JSONRenderer()
        self.request.accepted_media_type = self.request.accepted_renderer.media_type
        return super(PublishedDocumentDetailView, self).list(request)

    def retrieve(self, request, *args, **kwargs):
        component = self.frbr_uri.expression_component or 'main'
        subcomponent = self.frbr_uri.expression_subcomponent
        format = self.request.accepted_renderer.format

        # get the document
        document = self.get_object()

        if subcomponent:
            element = document.doc.get_subcomponent(component, subcomponent)

        else:
            # special cases of the entire document

            # table of contents
            if (component, format) == ('toc', 'json'):
                serializer = self.get_serializer(document)
                return Response({'toc': self.table_of_contents(document)})

            # json description
            if (component, format) == ('main', 'json'):
                serializer = self.get_serializer(document)
                return Response(serializer.data)

            # entire thing
            if (component, format) == ('main', 'xml'):
                return Response(document.document_xml)

            # the item we're interested in
            element = document.doc.components().get(component)

        if element:
            if format == 'html':
                if component == 'main' and not subcomponent:
                    return Response(document_to_html(document))
                else:
                    return Response(HTMLRenderer(act=document.doc).render(element))

            if format == 'xml':
                return Response(ET.tostring(element, pretty_print=True))

        raise Http404

    def get_object(self):
        """ Filter one document,  used by retrieve() """
        # TODO: filter on expression (expression date, etc.)
        # TODO: support multiple docs
        obj = get_object_or_404(self.get_queryset().filter(frbr_uri=self.frbr_uri.work_uri()))

        if obj.language != self.frbr_uri.language:
            raise Http404("The document %s exists but is not available in the language '%s'"
                          % (self.frbr_uri.work_uri(), self.frbr_uri.language))

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)
        return obj

    def filter_queryset(self, queryset):
        """ Filter the queryset, used by list() """
        queryset = queryset.filter(frbr_uri__istartswith=self.kwargs['frbr_uri'])
        if queryset.count() == 0:
            raise Http404
        return queryset

    def get_format_suffix(self, **kwargs):
        # we could also pull this from the parsed URI
        match = FORMAT_RE.search(self.kwargs['frbr_uri'])
        if match:
            # strip it from the uri
            self.kwargs['frbr_uri'] = self.kwargs['frbr_uri'][0:match.start()]
            return match.group(1)


class ConvertView(APIView):
    """
    Support for converting between two document types. This allows conversion from
    plain text, JSON, XML, and PDF to plain text, JSON, XML and HTML.
    """

    def post(self, request, format=None):
        serializer, document = self.handle_input()
        output_format = serializer.validated_data.get('outputformat')
        return self.handle_output(document, output_format)

    def handle_input(self):
        self.fragment = self.request.data.get('fragment')
        document = None
        serializer = ConvertSerializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)

        input_format = serializer.validated_data.get('inputformat')

        upload = self.request.data.get('file')
        if upload:
            # we got a file
            try:
                document = self.get_importer().import_from_upload(upload)
                return serializer, document
            except ValueError as e:
                log.error("Error during import: %s" % e.message, exc_info=e)
                raise ValidationError({'file': e.message or "error during import"})

        elif input_format == 'application/json':
            doc_serializer = DocumentSerializer(
                data=self.request.data['content'],
                context={'request': self.request})
            doc_serializer.is_valid(raise_exception=True)
            document = doc_serializer.update_document(Document())

        elif input_format == 'text/plain':
            try:
                document = self.get_importer().import_from_text(self.request.data['content'])
            except ValueError as e:
                log.error("Error during import: %s" % e.message, exc_info=e)
                raise ValidationError({'content': e.message or "error during import"})

        if not document:
            raise ValidationError("Nothing to convert! Either 'file' or 'content' must be provided.")

        return serializer, document

    def handle_output(self, document, output_format):
        if output_format == 'application/json':
            if self.fragment:
                raise ValidationError("Cannot output application/json from a fragment")

            # disable tags, they can't be used without committing this object to the db
            document.tags = None

            doc_serializer = DocumentSerializer(instance=document, context={'request': self.request})
            data = doc_serializer.data
            data['content'] = document.document_xml
            return Response(data)

        if output_format == 'application/xml':
            if self.fragment:
                return Response({'output': document.to_xml()})
            else:
                return Response({'output': document.document_xml})

        if output_format == 'text/html':
            if self.fragment:
                return Response(HTMLRenderer().render(document.to_xml()))
            else:
                return Response({'output': document_to_html(document)})

        # TODO: handle plain text output

    def get_importer(self):
        importer = Importer()
        importer.fragment = self.request.data.get('fragment')
        importer.fragment_id_prefix = self.request.data.get('id_prefix')

        return importer
