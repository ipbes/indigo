# -*- coding: utf-8 -*-
import re
import csv
import io
import logging

from cobalt import FrbrUri
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.conf import settings
import requests
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account

from indigo.plugins import LocaleBasedMatcher, plugins
from indigo_api.models import Subtype, Work, PublicationDocument, Task, Amendment, Commencement, \
    VocabularyTopic, TaskLabel
from indigo_api.signals import work_changed


class RowValidationFormBase(forms.Form):
    country = forms.ChoiceField(required=True)
    locality = forms.ChoiceField(required=False)
    title = forms.CharField()
    primary_work = forms.CharField(required=False)
    doctype = forms.ChoiceField(required=True)
    subtype = forms.ChoiceField(required=False)
    number = forms.CharField(validators=[
        RegexValidator(r'^[a-zA-Z0-9-]+$', 'No spaces or punctuation allowed (use \'-\' for spaces).')
    ])
    year = forms.CharField(validators=[
        RegexValidator(r'\d{4}', 'Must be a year (yyyy).')
    ])
    publication_name = forms.CharField(required=False)
    publication_number = forms.CharField(required=False)
    publication_date = forms.DateField(error_messages={'invalid': 'Date format should be yyyy-mm-dd.'})
    assent_date = forms.DateField(required=False, error_messages={'invalid': 'Date format should be yyyy-mm-dd.'})
    commencement_date = forms.DateField(required=False, error_messages={'invalid': 'Date format should be yyyy-mm-dd.'})
    stub = forms.BooleanField(required=False)
    # handle spreadsheet that still uses 'principal'
    principal = forms.BooleanField(required=False)
    commenced_by = forms.CharField(required=False)
    amends = forms.CharField(required=False)
    repealed_by = forms.CharField(required=False)
    taxonomy = forms.CharField(required=False)

    def __init__(self, country, locality, subtypes, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['country'].choices = [(country.code, country.name)]
        self.fields['locality'].choices = [(locality.code, locality.name)] \
            if locality else []
        self.fields['doctype'].choices = self.get_doctypes_for_country(country.code)
        self.fields['subtype'].choices = [(s.abbreviation, s.name) for s in subtypes]

    def get_doctypes_for_country(self, country_code):
        return [[d[1], d[0]] for d in
                settings.INDIGO['DOCTYPES'] +
                settings.INDIGO['EXTRA_DOCTYPES'].get(country_code, [])]

    def clean_title(self):
        title = self.cleaned_data.get('title')
        return re.sub('[\u2028 ]+', ' ', title)


class ChapterMixin(forms.Form):
    """ Includes (optional) Chapter (cap) field.
    For this field to be recorded on bulk creation, add `'cap': 'Chapter (Cap.)'`
    for the relevant country in settings.INDIGO['WORK_PROPERTIES']
    """
    cap = forms.CharField(required=False)


class PublicationDateOptionalRowValidationForm(RowValidationFormBase):
    """ Make `publication_date` optional on bulk creation.
    To make it optional for individual work creation, also add the country code to
    AddWorkView.PUB_DATE_OPTIONAL_COUNTRIES in apps.IndigoLawsAfricaConfig.
    """
    publication_date = forms.DateField(required=False, error_messages={'invalid': 'Date format should be yyyy-mm-dd.'})


@plugins.register('bulk-creator')
class BaseBulkCreator(LocaleBasedMatcher):
    """ Create works in bulk from a google sheets spreadsheet.
    """
    locale = (None, None, None)
    """ The locale this bulk creator is suited for, as ``(country, language, locality)``.
    """

    row_validation_form_class = RowValidationFormBase
    """ The validation form for each row of the spreadsheet. 
        Can be subclassed / mixed in to add fields or making existing fields optional.
    """

    aliases = []
    """ list of tuples of the form ('alias', 'meaning')
    (to be declared by subclasses), e.g. ('gazettement_date', 'publication_date')
    """

    default_doctype = 'act'
    """ If this is overridden by a subclass, the default doctype must be given in
        settings.INDIGO['EXTRA_DOCTYPES'] for the relevant country code, e.g.
        default_doctype = 'not_act'
        INDIGO['EXTRA_DOCTYPES'] = {
            'za': [('Not an Act', 'not_act')],
        }
    """

    log = logging.getLogger(__name__)

    _service = None
    _gsheets_secret = None

    GSHEETS_SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

    def gsheets_id_from_url(self, url):
        match = re.match(r'^https://docs.google.com/spreadsheets/d/(\S+)/', url)
        if match:
            return match.group(1)

    def get_datatable(self, spreadsheet_url, sheet_name):
        spreadsheet_id = self.gsheets_id_from_url(spreadsheet_url)
        if not spreadsheet_id:
            raise ValidationError("Unable to extract key from Google Sheets URL")

        if self.is_gsheets_enabled:
            return self.get_datatable_gsheets(spreadsheet_id, sheet_name)
        else:
            return self.get_datatable_csv(spreadsheet_id)

    def get_datatable_csv(self, spreadsheet_id):
        try:
            url = 'https://docs.google.com/spreadsheets/d/%s/export?format=csv' % spreadsheet_id
            response = requests.get(url, timeout=5)
            response.raise_for_status()
        except requests.RequestException as e:
            raise ValidationError("Error talking to Google Sheets: %s" % str(e))

        reader = csv.reader(io.StringIO(response.content.decode('utf-8')))
        rows = list(reader)

        if not rows or not rows[0]:
            raise ValidationError(
                "Your sheet did not import successfully; "
                "please check that you have link sharing ON (Anyone with the link)."
            )
        return rows

    @property
    def is_gsheets_enabled(self):
        return bool(settings.INDIGO.get('GSHEETS_API_CREDS'))

    def get_spreadsheet_sheets(self, spreadsheet_id):
        if self.is_gsheets_enabled:
            try:
                metadata = self.gsheets_client.spreadsheets()\
                    .get(spreadsheetId=spreadsheet_id)\
                    .execute()
                return metadata['sheets']
            except HttpError as e:
                self.log.warning("Error getting data from google sheets for {}".format(spreadsheet_id), exc_info=e)
                raise ValueError(str(e))

        return []

    def get_datatable_gsheets(self, spreadsheet_id, sheet_name):
        """ Fetch a datatable from a Google Sheets spreadsheet, using the given URL and sheet
        index (tab index).
        """
        try:
            result = self.gsheets_client\
                .spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=sheet_name)\
                .execute()
        except HttpError as e:
            self.log.warning("Error getting data from google sheets for {}".format(spreadsheet_id), exc_info=e)
            raise ValidationError("Unable to access spreadsheet. Is the URL correct and have you shared it with {}?".format(
                self._gsheets_secret['client_email'],
            ))

        rows = result.get('values', [])
        if not rows or not rows[0]:
            raise ValidationError("There doesn't appear to be data in sheet {} of {}".format(sheet_name, spreadsheet_id))
        return rows

    @property
    def gsheets_client(self):
        if not self._service:
            if not self._gsheets_secret:
                self._gsheets_secret = settings.INDIGO['GSHEETS_API_CREDS']
            credentials = service_account.Credentials.from_service_account_info(self._gsheets_secret, scopes=self.GSHEETS_SCOPES)
            self._service = build('sheets', 'v4', credentials=credentials)
        return self._service

    def get_row_validation_form(self, country, locality, subtypes, row_data):
        return self.row_validation_form_class(country, locality, subtypes, row_data)

    def create_works(self, view, table, dry_run, workflow, user):
        self.workflow = workflow
        self.user = user
        self.subtypes = Subtype.objects.all()

        works = []

        # clean up headers
        headers = [h.split(' ')[0].lower() for h in table[0]]

        # Transform rows into list of dicts for easy access.
        # The rows in table only have entries up to the last non-empty cell,
        # so we ensure that we have at least an empty string for every header.
        rows = [
            {header: (row[i] if i < len(row) else '') for i, header in enumerate(headers) if header}
            for row in table[1:]
        ]

        for idx, row in enumerate(rows):
            # ignore if it's blank or explicitly marked 'ignore' in the 'ignore' column
            if row.get('ignore') or not [val for val in row.values() if val]:
                continue

            works.append(self.create_work(view, row, idx, dry_run))

        if not dry_run:
            # link all commencements first so that amendments and repeals will have dates to work with
            for info in works:
                if info['status'] == 'success' and info.get('commencement_date') or info.get('commenced_by'):
                    self.link_commencement(info['work'], info)

            for info in works:
                if info['status'] == 'success':
                    if info.get('primary_work'):
                        self.link_parent_work(info['work'], info)

                    if info.get('taxonomy'):
                        self.link_taxonomy(info['work'], info)

                if info['status'] != 'error':
                    # this will check duplicate works as well
                    # (they won't overwrite the existing works but the amendments/repeals will be linked)
                    if info.get('amends'):
                        self.link_amendment(info['work'], info)
                    if info.get('repealed_by'):
                        self.link_repeal(info['work'], info)

        return works

    def create_work(self, view, row, idx, dry_run):
        # copy all row details
        info = row
        info['row'] = idx + 2

        row = self.validate_row(view, row)

        if row.get('errors'):
            info['status'] = 'error'
            info['error_message'] = row['errors']
            return info

        frbr_uri = self.get_frbr_uri(row)

        try:
            work = Work.objects.get(frbr_uri=frbr_uri)
            info['work'] = work
            info['status'] = 'duplicate'
            info['amends'] = row.get('amends') or None
            info['commencement_date'] = row.get('commencement_date') or None

        except Work.DoesNotExist:
            work = Work()

            work.frbr_uri = frbr_uri
            work.country = view.country
            work.locality = view.locality
            work.title = row.get('title')
            work.publication_name = row.get('publication_name')
            work.publication_number = row.get('publication_number')
            work.publication_date = row.get('publication_date')
            work.commenced = bool(row.get('commencement_date') or row.get('commenced_by'))
            work.assent_date = row.get('assent_date')
            work.stub = row.get('stub')
            # handle spreadsheet that still uses 'principal'
            if 'stub' not in info:
                work.stub = not row.get('principal')
            work.created_by_user = view.request.user
            work.updated_by_user = view.request.user
            self.add_extra_properties(work, info)

            try:
                work.full_clean()
                if not dry_run:
                    work.save_with_revision(view.request.user)

                    # signals
                    work_changed.send(sender=work.__class__, work=work, request=view.request)

                    # info for links
                    pub_doc_params = {
                        'date': row.get('publication_date'),
                        'number': work.publication_number,
                        'publication': work.publication_name,
                        'country': view.country.place_code,
                        'locality': view.locality.code if view.locality else None,
                    }
                    info['params'] = pub_doc_params

                    self.link_publication_document(work, info)

                    if not work.stub:
                        self.create_task(work, info, task_type='import')

                info['work'] = work
                info['status'] = 'success'

            except ValidationError as e:
                info['status'] = 'error'
                if hasattr(e, 'message_dict'):
                    info['error_message'] = ' '.join(
                        ['%s: %s' % (f, '; '.join(errs)) for f, errs in e.message_dict.items()]
                    )
                else:
                    info['error_message'] = str(e)

        return info

    def transform_aliases(self, row):
        """ Adds the term the platform expects to `row` for validation (and later saving).
        e.g. if the spreadsheet has `gazettement_date` where we expect `publication_date`,
        `publication_date` and the appropriate value will be added to `row`
        if ('gazettement_date', 'publication_date') was specified in the subclass's aliases
        """
        for alias, meaning in self.aliases:
            if alias in row:
                row[meaning] = row[alias]

    def transform_error_aliases(self, errors):
        """ Changes the term the platform expects back into its alias for displaying.
        e.g. if spreadsheet has `gazettement_date` where we expect `publication_date`,
        the error will display as `gazettement_date`
        if ('gazettement_date', 'publication_date') was specified in the subclass's aliases
        """
        for alias, meaning in self.aliases:
            for title in errors.keys():
                if meaning == title:
                    errors[alias] = errors.pop(title)

    def validate_row(self, view, row):
        self.transform_aliases(row)

        row_data = row
        # lowercase country, locality, doctype and subtype
        row_data['country'] = row.get('country', '').lower()
        row_data['locality'] = row.get('locality', '').lower()
        row_data['doctype'] = row.get('doctype', '').lower() or self.default_doctype
        row_data['subtype'] = row.get('subtype', '').lower()

        form = self.get_row_validation_form(view.country, view.locality, self.subtypes, row_data)

        errors = form.errors
        self.transform_error_aliases(errors)

        row = form.cleaned_data
        row['errors'] = errors
        return row

    def get_frbr_uri(self, row):
        frbr_uri = FrbrUri(country=row.get('country'),
                           locality=row.get('locality'),
                           doctype=row.get('doctype', self.default_doctype),
                           subtype=row.get('subtype'),
                           date=row.get('year'),
                           number=row.get('number'),
                           actor=row.get('actor', None))

        return frbr_uri.work_uri().lower()

    def add_extra_properties(self, work, info):
        place = self.locality or self.country
        for extra_property in place.settings.work_properties.keys():
            if info.get(extra_property):
                work.properties[extra_property] = info.get(extra_property)

    def link_publication_document(self, work, info):
        params = info.get('params')
        locality_code = self.locality.code if self.locality else None
        finder = plugins.for_locale('publications', self.country.code, None, locality_code)

        if not finder or not params.get('date'):
            return self.create_task(work, info, task_type='link-publication-document')

        try:
            publications = finder.find_publications(params)
        except requests.HTTPError:
            return self.create_task(work, info, task_type='link-publication-document')

        if len(publications) != 1:
            return self.create_task(work, info, task_type='link-publication-document')

        pub_doc_details = publications[0]
        pub_doc = PublicationDocument()
        pub_doc.work = work
        pub_doc.file = None
        pub_doc.trusted_url = pub_doc_details.get('url')
        pub_doc.size = pub_doc_details.get('size')
        pub_doc.save()

    def link_commencement(self, work, info):
        # if the work has commencement details, try linking it
        # make a task if a `commenced_by` FRBR URI is given but not found
        date = info.get('commencement_date') or None

        commencing_work = None
        if info.get('commenced_by'):
            commencing_work = self.find_work(info['commenced_by'])
            if not commencing_work:
                self.create_task(work, info, task_type='link-commencement')

        Commencement.objects.get_or_create(
            commenced_work=work,
            commencing_work=commencing_work,
            date=date,
            defaults={
                'main': True,
                'all_provisions': True,
                'created_by_user': self.user,
            },
        )

    def link_repeal(self, work, info):
        # if the work is `repealed_by` something, try linking it or make the relevant task
        repealing_work = self.find_work(info['repealed_by'])

        if not repealing_work:
            # a work with the given FRBR URI / title wasn't found
            self.create_task(work, info, task_type='no-repeal-match')

        elif work.repealed_by and work.repealed_by != repealing_work:
            # the work was already marked as repealed by a different work
            self.create_task(work, info, task_type='check-update-repeal', repealing_work=repealing_work)

        elif not work.repealed_by:
            # the work was not already repealed; link the new repeal information
            repeal_date = repealing_work.commencement_date

            if not repeal_date:
                # there's no date for the repeal (yet), so create a task on the repealing work for once it commences
                return self.create_task(repealing_work, info, task_type='link-repeal-pending-commencement')

            work.repealed_by = repealing_work
            work.repealed_date = repeal_date

            try:
                work.save_with_revision(self.user)
            except ValidationError:
                # something else went wrong
                self.create_task(work, info, task_type='link-repeal', repealing_work=repealing_work)

    def link_parent_work(self, work, info):
        # if the work has a `primary_work`, try linking it
        # make a task if this fails
        parent_work = self.find_work(info['primary_work'])
        if not parent_work:
            return self.create_task(work, info, task_type='link-primary-work')

        work.parent_work = parent_work

        try:
            work.save_with_revision(self.user)
        except ValidationError:
            self.create_task(work, info, task_type='link-primary-work')

    def link_amendment(self, work, info):
        # if the work `amends` something, try linking it
        # (this will only work if there's only one amendment listed)
        # make a task if this fails
        amended_work = self.find_work(info['amends'])
        if not amended_work:
            return self.create_task(work, info, task_type='link-amendment')

        date = info.get('commencement_date') or work.commencement_date
        if not date:
            return self.create_task(work, info, task_type='link-amendment-pending-commencement', amended_work=amended_work)

        amendment, new = Amendment.objects.get_or_create(
            amended_work=amended_work,
            amending_work=work,
            date=date,
            defaults={
                'created_by_user': self.user,
            },
        )

        if new:
            self.create_task(amended_work, info, task_type='apply-amendment', amendment=amendment)

    def link_taxonomy(self, work, info):
        topics = [x.strip(",") for x in info.get('taxonomy').split()]
        unlinked_topics = []
        for t in topics:
            topic = VocabularyTopic.get_topic(t)
            if topic:
                work.taxonomies.add(topic)
                work.save_with_revision(self.user)

            else:
                unlinked_topics.append(t)
        if unlinked_topics:
            info['unlinked_topics'] = ", ".join(unlinked_topics)
            self.create_task(work, info, task_type='link-taxonomy')

    def create_task(self, work, info, task_type, repealing_work=None, amended_work=None, amendment=None):
        task = Task()

        if task_type == 'link-publication-document':
            task.title = 'Link gazette'
            task.description = f'''This work's gazette (original publication document) couldn't be linked automatically.

Find it and upload it manually.'''

        elif task_type == 'import':
            task.title = 'Import content'
            task.description = '''Import the content for this work – either the initial publication (usually a PDF of the Gazette) or a later consolidation (usually a .docx file).'''

        elif task_type == 'link-commencement':
            task.title = 'Link commencement'
            task.description = f'''It looks like this work was commenced by "{info['commenced_by']}" (see row {info['row']} of the spreadsheet), but it couldn't be linked automatically.

Possible reasons:
– a typo in the spreadsheet
– the commencing work doesn't exist on the system.

Please link the commencing work manually.'''

        elif task_type == 'link-amendment':
            task.title = 'Link amendment'
            amended_work = info['amends']
            if len(amended_work) > 256:
                amended_work = "".join(amended_work[:256] + ', etc')
            task.description = f'''It looks like this work amends "{amended_work}" (see row {info['row']} of the spreadsheet), but it couldn't be linked automatically.

Possible reasons:
– a typo in the spreadsheet
– more than one amended work was listed (it only works if there's one)
– the amended work doesn't exist on the system.

Please link the amendment manually.'''

        elif task_type == 'link-amendment-pending-commencement':
            task.title = 'Link amendment'
            task.description = f'''It looks like this work amends {amended_work.title} ({amended_work.numbered_title()}), but it couldn't be linked automatically because this work hasn't commenced yet (so there's no date for the amendment).

Please link the amendment manually (and apply it) when this work comes into force.'''

        elif task_type == 'apply-amendment':
            task.title = 'Apply amendment'
            task.description = f'''Apply the amendments made by {amendment.amending_work.title} ({amendment.amending_work.numbered_title()}) on {amendment.date}.

The amendment has already been linked, so start at Step 3 of https://docs.laws.africa/managing-works/amending-works.'''

        elif task_type == 'no-repeal-match':
            task.title = 'Link repeal'
            task.description = f'''It looks like this work was repealed by "{info['repealed_by']}" (see row {info['row']} of the spreadsheet), but it couldn't be linked automatically.

Possible reasons:
– a typo in the spreadsheet
– the repealing work doesn't exist on the system.

Please link the repeal manually.'''

        elif task_type == 'check-update-repeal':
            task.title = 'Update repeal information?'
            task.description = f'''On the spreadsheet (see row {info['row']}), it says that this work was repealed by {repealing_work.title} ({repealing_work.numbered_title()}).

But this work is already listed as having been repealed by {work.repealed_by} ({work.repealed_by.numbered_title()}), so the repeal information wasn't updated automatically.

If the old / existing repeal information was wrong, update it manually. Otherwise (if the spreadsheet was wrong), cancel this task.
'''

        elif task_type == 'link-repeal-pending-commencement':
            repealed_work = info['work']
            task.title = 'Link repeal'
            task.description = f'''It looks like this work repeals {repealed_work.title} ({repealed_work.numbered_title()}), but it couldn't be linked automatically because this work hasn't commenced yet (so there's no date for the repeal).

Please link the repeal manually when this work comes into force.'''

        elif task_type == 'link-repeal':
            task.title = 'Link repeal'
            task.description = f'''It looks like this work was repealed by {repealing_work.title} ({repealing_work.numbered_title()}), but it couldn't be linked automatically.

Please link it manually.'''

        elif task_type == 'link-primary-work':
            task.title = 'Link primary work'
            task.description = f'''It looks like this work's primary work is "{info['primary_work']}" (see row {info['row']} of the spreadsheet), but it couldn't be linked automatically.

Possible reasons:
– a typo in the spreadsheet
– the primary work doesn't exist on the system.

Please link the primary work manually.'''

        elif task_type == 'link-taxonomy':
            task.title = 'Link taxonomy'
            task.description = f'''It looks like this work has the following taxonomy: "{info['unlinked_topics']}" (see row {info['row']} of the spreadsheet), but it couldn't be linked automatically.

Possible reasons:
– a typo in the spreadsheet
– the taxonomy doesn't exist on the system.'''

        task.country = self.country
        task.locality = self.locality
        task.work = work
        task.code = task_type
        task.created_by_user = self.user

        # need to save before assigning workflow because of M2M relation
        task.save()
        if self.workflow:
            task.workflows.set([self.workflow])
            task.save()

        if 'pending-commencement' in task_type:
            # add the `pending commencement` label, if it exists
            pending_commencement_label = TaskLabel.objects.filter(slug='pending-commencement').first()
            if pending_commencement_label:
                task.labels.add(pending_commencement_label)
                task.save()

        return task

    def find_work(self, given_string):
        """ The string we get from the spreadsheet could be e.g.
            `/ug/act/1933/14 - Administrator-General’s Act` (new and preferred style)
            `Administrator-General’s Act` (old style)
            First see if the string before the first space can be parsed as an FRBR URI, and find a work based on that.
            If not, assume a title has been given and try to match on the whole string.
        """
        first = given_string.split()[0]
        try:
            FrbrUri.parse(first)
            return Work.objects.filter(frbr_uri=first).first()
        except ValueError:
            potential_matches = Work.objects.filter(title=given_string, country=self.country, locality=self.locality)
            if len(potential_matches) == 1:
                return potential_matches.first()

    @property
    def share_with(self):
        if not self._gsheets_secret:
            self._gsheets_secret = settings.INDIGO['GSHEETS_API_CREDS']

        return self._gsheets_secret.get('client_email')
