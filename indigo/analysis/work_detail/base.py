from django.utils.translation import ugettext as _

from indigo.plugins import LocaleBasedMatcher, plugins
from indigo_api.models import Subtype


@plugins.register('work-detail')
class BaseWorkDetail(LocaleBasedMatcher):
    """ Provides some locale-specific work details.

    Subclasses should implement `work_numbered_title`.
    """

    no_numbered_title_subtypes = []
    """ These subtypes don't have numbered titles. """
    no_numbered_title_numbers = ['constitution']
    """ These numbers don't have numbered titles. """

    def work_numbered_title(self, work):
        """ Return a formatted title using the number for this work, such as "Act 5 of 2009".
        This usually differs from the short title. May return None.
        """
        # these don't have numbered titles
        number = work.number
        # also check partials, e.g. 'constitution-amendment' shouldn't get one
        if any(partial in self.no_numbered_title_numbers for partial in number.split("-")):
            return None

        # these don't have numbered titles
        if work.work_uri.subtype in self.no_numbered_title_subtypes:
            return None

        work_type = self.work_friendly_type(work)
        return _('%(type)s %(number)s of %(year)s') % {'type': _(work_type), 'number': number.upper(), 'year': work.year}

    def work_friendly_type(self, work):
        """ Return a friendly document type for this work, such as "Act" or "By-law".
        """
        uri = work.work_uri

        if uri.subtype:
            # use the subtype full name, if we have it
            subtype = Subtype.for_abbreviation(uri.subtype)
            if subtype:
                return _(subtype.name)
            return _(uri.subtype.upper())

        return _('Act')


class ChapterWorkDetail(BaseWorkDetail):
    """ Takes Chapter numbers into account when working out a work's numbered title.
    """
    def work_numbered_title(self, work):
        if work.properties.get('cap'):
            # eg. Chapter 2
            return _('Chapter %(cap)s') % {'cap': work.properties['cap']}

        return super().work_numbered_title(work)
