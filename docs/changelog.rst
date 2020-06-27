Changelog
=========

11.0.0 (?)
----------

Important
.........

This version migrates data from Akoma Ntoso 2.0 to Akoma Ntoso 3.0. This cannot be undone.

You **must** upgrade to this version before upgrading to future versions.

Upgrade process
...............

1. **Make a backup of your database before proceeding**
2. Install Indigo version 11.0.0.
3. Apply outstanding migrations one at a time.

The `indigo_api` migrations 0130 to 0134 make significant changes to all current and historical documents. They may each take up to an hour to run.

Changes
.......

* BREAKING: migrate from Akoma Ntoso 2.0 to Akoma Ntoso 3.0
* BREAKING: content API URLs with work components must use !, such as ``/za/act/1992/1/!main``
* BREAKING: v1 of the content API has been removed, as it is not AKN3 compliant.
* BREAKING: static XSL filenames have changed:
  * act.xsl has moved to html_act.xsl
  * country-specific files such as act-za.xsl must be renamed to html_act-za.xsl
  * text.xsl has moved to text_act.xsl
  * country-specific files such as act_text-za.xsl must be renamed to text_act-za.xsl
* BREAKING: work FRBR URIs now all start with ``/akn``
* FEATURE: add ``akn`` as a final candidate when looking for XSL and coverpage files
* Vastly improved document differ/comparisons using xmldiff.

10.0.0 (5 June 2020)
--------------------

**Note**: This is the last version to support Akoma Ntoso 2.0. You **must** upgrade to this version before upgrading to subsequent versions.

* BREAKING: upgrade to Django 2.22
* BREAKING: new badges with clearer names and permissions
* FEATURE: SUBPART element
* FEATURE: numbered title in API
* FEATURE: user profile photos
* FIX: many fixes for table editing
* FIX: improved annotation anchoring
* List of contributors for place and work

9.1.0 (13 March 2020)
---------------------

* Changes to act coverpage template to better support customisation
* FIX: correctly count number of breadth-complete works for daily work metrics

9.0.0 (10 March 2020)
---------------------

* FEATURE: model multiple commencements and include commenced provision information in API
* FIX: issue when locking a document for editing
* Improved inline view of differences between points in time
* Report JS exceptions to admins

8.0.0 (10 February 2020)
------------------------

* FEATURE: New place overview page
* FEATURE: New page to show tasks assigned to a user
* FEATURE: Filter works by completeness
* Group sources in document 'show source' view
* Include amendment publication documents in 'show source' view
* Decrypt encrypted PDFs when importing only certain pages
* Move from arrow to iso8601

7.0.0 (9 December 2019)
-----------------------

* FEATURE: export work details as XLSX
* FEATURE: resizable table columns (using CKEditor)
* FEATURE: highlight text and make comments
* Make it easier to override colophons
* Rename output renderers to exporters, so as not to clash with DRF renderers

6.0.0 (18 November 2019)
------------------------

* FEATURE: choose which pages to import from PDFs
* FEATURE: link to internal section references
* FEATURE: advanced work filtering (publication, commencement, repeal, amendment etc.)
* FEATURE: show offline warning when editing a document
* FEATURE: site sidebar removed and replaced with tabs
* FEATURE: show source attachments and work publication document side-by-side when editing a document
* FEATURE: explicit support for commenced work with an unknown commencement date
* New schedule syntax makes headings and subheadings clearer
* Move document templates from templates/documents/ to templates/indigo_api/documents/


5.0.0 (21 October 2019)
-----------------------

* FEATURE: count of comments on a document, and comment navigation
* FEATURE: resolver for looking up documents in the local database
* FEATURE: include images in PDFs and ePUBs
* FEATURE: Support for arbitrary expression dates
* Custom work properties for a place moved into settings

4.1.0 (3 October 2019)
----------------------

* FEATURE: Paste tables directly from Word when in edit mode.
* FEATURE: Scaffolding for showing document issues.
* FEATURE: Show document hierarchy in editor.
* FEATURE: Support customisable importing of HTML files.
* FEATURE: Customisable PDF footers
* Clearer indication of repealed works.
* indigo-web 3.6.1 - explicit styling for crossHeading elements
* Badge icons are now stylable images
* Javascript traditions inherit from the defaults better, and are simpler to manage.

4.0.0 (12 September 2019)
-------------------------

This release drops support for Python 2.x. Please upgrade to at least Python 3.6.

* BREAKING: Drop support for Python 2.x
* FEATURE: Calculate activity metrics for places
* FEATURE: Importing bulk works from Google Sheets now allows you to choose a tab to import from
* Preview when importing bulk works
* Requests are atomic and run in transactions by default
* Improved place listing view, including activity for the place
* Localities page for a place

3.0 (5 July 2019)
-----------------

This is the first major release of Indigo with over a year of active development. Upgrade to this version by installing updated dependencies and running migrations.

* FEATURE: Support images in documents
* FEATURE: Download as XML
* FEATURE: Annotations/comments on documents
* FEATURE: Download documents as ZIP archives
* FEATURE: You can now highlight lines of text in the editor and transform them into a table, using the Edit > Insert Table menu item.
* FEATURE: Edit menu with Find, Replace, Insert Table, Insert Image, etc.
* FEATURE: Presence indicators for other users editing the same document.
* FEATURE: Assignable tasks and workflows.
* FEATURE: Social/oauth login supported.
* FEATURE: Localisation support for different languages and legal traditions.
* FEATURE: Badge-based permissions system
* FEATURE: Email notifications
* FEATURE: Improved diffs in document and work version histories
* FEATURE: Batch creation of works from Google Sheets
* FEATURE: Permissions-based API access
* FEATURE: Attach publication documents to works
* FEATURE: Measure work completeness
* BREAKING: Templates for localised rendering have moved to ``templates/indigo_api/akn/``
* BREAKING: The LIME editor has been removed.
* BREAKING: Content API for published documents is now a separate module and versioned under ``/v2/``
* BREAKING: Some models have moved from ``indigo_app`` to ``indigo_api``, you may need to updated your references appropriately.

2.0 (6 April 2017)
------------------

* Upgraded to Django 1.10
* Upgraded a number of dependencies to support Django 1.10
* FEATURE: significantly improved mechanism for maintaining amended versions of documents
* FEATURE: you can now edit tables directly inline in a document
* FEATURE: quickly edit a document section without having to open it via the TOC
* FEATURE: support for newlines in tables
* FEATURE: improved document page layout
* FEATURE: pre-loaded set of publication names per country
* Assent and commencement notices are no longer H3 elements, so PDFs don't include them in their TOCs. #28
* FIX: bug when saving an edited section
* FIX: ensure TOC urls use expression dates
* FIX: faster document saving

After upgrading to this version, you **must** run migrations::

    python manage.py migrate

We also recommend updating the list of countries::

    python manage.py update_countries_plus

1.1 (2016-12-19)
----------------

* First tagged release
