import re
from lxml import etree

from django.utils.translation import override, ugettext as _

from indigo.plugins import plugins, LocaleBasedMatcher


# Ensure that these translations are included by makemessages
from indigo.xmlutils import closest

_('Act')
_('Article')
_('By-law')
_('Chapter')
_('Government Notice')
_('Part')
_('Section')
_('Preface')
_('Preamble')


@plugins.register('toc')
class TOCBuilderBase(LocaleBasedMatcher):
    """ This builds a Table of Contents for an Act.

    A Table of Contents is a tree of :class:`TOCElement` instances, each element
    representing an item of interest in the Table of Contents. Each item
    has attributes useful for presenting a Table of Contents, such as a type
    (chapter, part, etc.), a number, a heading and further child elements.

    The TOC is assembled from certain tags in the document, see ``toc_elements``.

    The Table of Contents can also be used to lookup the XML element corresponding
    to an item in the Table of Contents identified by its subcomponent path.
    This is useful when handling URIs such as ``.../eng/main/section/1`` or
    ``.../eng/main/part/C``.

    Some components can be uniquely identified by their type and number, such as
    ``Section 2``. Others require context, such as ``Part 2 of Chapter 1``. The
    latter are controlled by ``toc_non_unique_elements``.
    """

    locale = (None, None, None)
    """ The locale this TOC builder is suited for, as ``(country, language, locality)``.
    """

    toc_elements = ['coverpage', 'preface', 'preamble', 'part', 'chapter', 'section', 'conclusions', 'attachment',
                    'component']
    """ Elements we include in the table of contents, without their XML namespace.
    """

    toc_deadends = ['meta', 'attachments', 'components', 'embeddedStructure', 'quotedStructure', 'subFlow']
    """ Elements we don't check or recurse into because they contain sub-documents or subflows.
    """

    toc_non_unique_components = ['chapter', 'part']
    """ These TOC elements (tag names without namespaces) aren't numbered uniquely throughout the document
    and will need their parent components for context. Subclasses must provide this.
    """

    titles = {}
    """ Dict from toc elements (tag names without namespaces) to functions that take a :class:`TOCElement` instance
    and return a string title for that element.

    Include the special item `default` to handle elements not in the list.
    """

    component_elements = ['component', 'attachment']
    """ Elements that are considered components.
    """

    # eg. schedule1
    component_id_re = re.compile('([^0-9]+)([0-9]+)')

    non_commenceable_types = set(['coverpage', 'preface', 'preamble', 'conclusions', 'attachment', 'component'])

    def table_of_contents_for_document(self, document):
        """ Build the table of contents for a document.
        """
        return self.table_of_contents(document.doc, document.django_language)

    def table_of_contents_entry_for_element(self, document, element):
        """ Build the table of contents entry for an element from a document.
        """
        self.setup(document.doc, document.django_language)

        with override(self.language):
            name, component_el = self.determine_component(element)
            # find the first node at or above element, that is a valid TOC element
            element = closest(element, lambda e: self.is_toc_element(e))
            if element is not None:
                return self.make_toc_entry(element, name, self.get_component_id(name, component_el))

    def setup(self, act, language):
        self.act = act
        self.language = language
        self._toc_elements_ns = set(f'{{{self.act.namespace}}}{s}' for s in self.toc_elements)
        self._toc_deadends_ns = set(f'{{{self.act.namespace}}}{s}' for s in self.toc_deadends)

    def determine_component(self, element):
        """ Determine the component element which contains +element+.
        """
        ancestors = [element] + list(element.iterancestors())

        # reversed so that we go through components before the main document element,
        # because all components are ancestors of that
        for name, element in reversed(self.act.components().items()):
            if element in ancestors:
                return name, element

        return None, None

    def is_toc_element(self, element):
        return element.tag in self._toc_elements_ns or (
            # AKN 2.0 crossheadings are <hcontainer name="crossheading">
            'crossheading' in self.toc_elements and element.tag.endswith('}hcontainer')
            and element.get('name', None) == 'crossheading')

    def table_of_contents(self, act, language):
        """ Get the table of contents of ``act`` as a list of :class:`TOCElement` instances. """
        self.setup(act, language)

        with override(language):
            return self.build_table_of_contents()

    def build_table_of_contents(self):
        toc = []
        for component, element in self.act.components().items():
            toc += self.process_elements(component, self.get_component_id(component, element), [element])

        return toc

    def get_component_id(self, name, element):
        """ Get an ID for this component element.
        """
        return None if name == 'main' else element.get('eId')

    def process_elements(self, component, component_id, elements, parent=None):
        """ Process the list of ``elements`` and their children, and
        return a (potentially empty) set of TOC items.
        """
        items = []
        for e in elements:
            # don't descend into these elements, which can contain nested documents or other subflows
            if e.tag in self._toc_deadends_ns:
                continue

            if self.is_toc_element(e):
                item = self.make_toc_entry(e, component, component_id, parent=parent)
                item.children = self.process_elements(component, component_id, e.iterchildren(), parent=item)
                items.append(item)
            else:
                items += self.process_elements(component, component_id, e.iterchildren())
        return items

    def make_toc_entry(self, element, component, component_id, parent=None):
        type_ = element.tag.split('}', 1)[-1]
        id_ = element.get('eId')

        def get_heading(element):
            # collect text without descending into authorial notes
            xpath = etree.XPath(".//text()[not(ancestor::a:authorialNote)]",
                                namespaces={'a': self.act.namespace})
            return ''.join(xpath(element.heading))

        # support for crossheadings in AKN 2.0
        if type_ == 'hcontainer' and element.get('name', None) == 'crossheading':
            type_ = 'crossheading'

        try:
            heading = get_heading(element)
        except AttributeError:
            heading = None

        if not heading and type_ in self.component_elements:
            try:
                # try to use the alias from the attachment/component meta attribute
                heading = element.doc.meta.identification.FRBRWork.FRBRalias.get('value')
            except AttributeError:
                pass

            if not heading:
                # try the doc name
                try:
                    heading = element.doc.get('name', '').capitalize()
                except AttributeError:
                    pass

        try:
            num = element.num
        except AttributeError:
            num = None

        num = num.text if num else None

        if type_ in self.component_elements:
            subcomponent = None
        else:
            # if we have a chapter/part as a child of a chapter/part, we need to include
            # the parent as context because they aren't unique, eg: part/1/chapter/2
            if type_ in self.toc_non_unique_components and parent and parent.type in self.toc_non_unique_components:
                subcomponent = parent.subcomponent + "/"
            else:
                subcomponent = ""

            # eg. 'preamble' or 'chapter/2'
            subcomponent += type_

            if num:
                subcomponent += '/' + num.strip('.()')

        toc_item = TOCElement(element, component, type_, heading=heading, id_=id_,
                              num=num, subcomponent=subcomponent, parent=parent, component_id=component_id)
        toc_item.title = self.friendly_title(toc_item)

        return toc_item

    def friendly_title(self, item):
        """ Build a friendly title for this, based on heading names etc.
        """
        if item.type in self.titles:
            return self.titles[item.type](item)

        if 'default' in self.titles:
            return self.titles['default'](item)

        return self.default_title(item)

    def default_title(self, item):
        if item.heading:
            title = item.heading
        else:
            title = _(item.type.capitalize())
            if item.num:
                title += ' ' + item.num

        return title

    def commenceable_items(self, toc):
        """ Return a list of those items in +toc+ that are considered commenceable.

        By default, these are all the child items in the main component, except
        the preface, preamble and conclusion.
        """
        def process(item):
            if item.component == 'main':
                if item.children:
                    for kid in item.children:
                        process(kid)
                elif item.type not in self.non_commenceable_types and item.num:
                    items.append(item)

        items = []
        for entry in toc:
            process(entry)

        return items

    def insert_commenceable_provisions(self, doc, provisions, id_set):
        toc = self.table_of_contents_for_document(doc)
        items = self.commenceable_items(toc)
        self.insert_provisions(provisions, id_set, items)

    def insert_provisions(self, provisions, id_set, items):
        """ Insert provisions from current toc at their correct indexes in `provisions`.
            `provisions` is a list of provisions for a work, usually built up by adding provisions to it
                from each point in time (using this method).
            `id_set` is the current set of ids that have already been added to `provisions`;
                it helps ensure that our list contains only unique provisions.
            `items` is a list of commenceable provisions from the current document's ToC.
        """
        # take note of any removed items to compensate for later
        removed_indexes = [i for i, p in enumerate(provisions) if p.id not in [i.id for i in items]]
        for i, item in enumerate(items):
            if item.id and item.id not in id_set:
                id_set.add(item.id)
                # We need to insert this provision at the correct position in the work provision list.
                # If any provisions from a previous document have been removed in this document
                # (indexes stored in removed_indexes), bump the insertion index up to take them into account.
                for n in removed_indexes:
                    if i >= n:
                        i += 1
                provisions.insert(i, item)


class TOCElement(object):
    """
    An element in the table of contents of a document, such as a chapter, part or section.

    :ivar children: further TOC elements contained in this one, may be None or empty
    :ivar component: component name (after the ! in the FRBR URI) of the component that this item is a part of
    :ivar element: :class:`lxml.objectify.ObjectifiedElement` the XML element of this TOC element
    :ivar heading: heading for this element, excluding the number, may be None
    :ivar id: XML id string of the node in the document, may be None
    :ivar num: number of this element, as a string, may be None
    :ivar qualified_id: the id of the element, qualified by the component id (if any)
    :ivar subcomponent: name of this subcomponent, may be None
    :ivar title: friendly title of this entry
    :ivar type: element type, one of: ``chapter, part, section`` etc.
    """

    def __init__(self, element, component, type_, heading=None, id_=None, num=None, subcomponent=None, parent=None, children=None, component_id=None):
        self.element = element
        self.component = component
        self.type = type_
        self.heading = heading
        self.id = id_
        self.num = num
        self.children = children
        self.subcomponent = subcomponent
        self.title = None
        self.qualified_id = id_ if component == 'main' else f"{component_id}/{id_}"

    def as_dict(self):
        info = {
            'type': self.type,
            'component': self.component,
            'subcomponent': self.subcomponent,
            'title': self.title,
        }

        if self.heading:
            info['heading'] = self.heading

        if self.num:
            info['num'] = self.num

        if self.id:
            info['id'] = self.id

        if self.children:
            info['children'] = [c.as_dict() for c in self.children]

        return info
