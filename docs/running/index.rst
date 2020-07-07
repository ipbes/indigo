.. running:

Installing and Running Indigo
=============================

This guide is for developers who want to install and run their own instance
of the Indigo platform.

Indigo is a Django web application that can be run as a standalone project, or
as part of an existing Django project. This guide will explain how to run Indigo as
a standalone project.

Requirements
------------

Indigo requires:

* Python 2.7
* PostgreSQL 9.3+
* Ruby 2.6.0+ for `Slaw <https://github.com/longhotsummer/slaw>`_
* An AWS S3 account and bucket for storing attachments

Optional but useful:

* An SMTP server to send email through, or an appropriate service

Using Heroku/Dokku means that we're using well-document and widely understood
mechanisms for specifying dependencies and configuration across multiple
languages. It takes care of all this for you and we highly recommend using them.

Installing Indigo Locally
-------------------------

1. Ensure you have Python 2.7 and `virtualenv <https://virtualenv.pypa.io/en/stable/>`_ installed
2. Clone the `github.com/laws-africa/example-indigo <https://github.com/laws-africa/example-indigo>`_ repository. It has all Indigo's dependencies for Python and Ruby described in it::

    $ git clone https://github.com/laws-africa/example-indigo
    $ cd indigo

3. Setup and activate the virtual environment::

    $ virtualenv --no-site-packages --python=python2 env
    $ source env/bin/activate

4. Install Python dependencies::

    $ pip install -r requirements.txt

5. Ensure you have PostgreSQL installed and running. Create a postgresql user with username and password `indigo`, and create a corresponding database called `indigo`::

    $ sudo su - postgres -c 'createuser -d -P indigo'
    $ sudo su - postgres -c 'createdb indigo'

6. Run the Django database migrations to setup the initial database::

    $ python manage.py migrate
    $ python manage.py update_countries_plus

7. Then create the superuser::

    $ python manage.py createsuperuser

8. Finally, run the server::

    $ python manage.py runserver

9. Visit the website to login: http://localhost:8000/

10. Configure a country:

   * Visit http://localhost:8000/admin
   * Under **Indigo API** click Countries, then click Add Country in the top right corner
   * Choose a country and primary language from the dropdown lists
   * Click Save

11. Now go back to http://localhost:8000/ and your country will be included in the list.

Ruby dependencies
.................

You won't be able to import documents yet. First, you'll need to install Ruby and the Slaw parser library. We strongly recommend installing and using RVM or a similar Ruby version manager. You'll need at least Ruby version 2.6.

Once you've install Ruby, install Bundler and the Indigo dependencies::

    $ gem install bundler
    $ bundle install

You can test that Slaw is installed with slaw --version::

    $ slaw --version
    slaw 1.0.4

Django Customisation
....................

You can now easily change Django settings, add your own modules, change URLs, etc. You simply need to create your own settings file, import the settings from Indigo, and update `manage.py` to reference your new settings file. For example:

1. Create a python module folder `my_app`::

    $ mkdir my_app; touch my_app/__init__.py

2. Create `my_app/settings.py` so that it looks like this::

    from indigo.settings import *

    # override any Django settings, as you would normally.

    # add your own apps, eg:
    # INSTALLED_APPS = ('my_app',) + INSTALLED_APPS

    # add your own URLs
    # ROOT_URLCONF = 'my_app.urls'

    # etc.

3. Update `manage.py` so that it references your new `my_app.settings` file::

    #!/usr/bin/env python
    import os
    import sys

    if __name__ == "__main__":
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_app.settings")

        from django.core.management import execute_from_command_line

        execute_from_command_line(sys.argv)

4. Run your updated app with ``python manage.py runserver``

Production Installation
-----------------------

Indigo requires some non-Python dependencies. This guide explains how to deploy
Indigo and these dependencies on `Heroku <https://heroku.com/>`_ or `Dokku <http://progrium.viewdocs.io/dokku/>`_.
Dokku uses Docker to emulate a Heroku-like environment on your own servers (or cloud).

.. note::

    We don't recommend using Heroku for production because some Indigo functionality
    -- such as parsing new documents -- can take longer than the 30 seconds
    Heroku allows for web API calls. However, Heroku is great for quickly trying Indigo
    out.

Installation on Heroku and Dokku are similar and only really differ in the commands that are run.
We describe using Dokku below, and assume that you have already have `Dokku installed <http://dokku.viewdocs.io/dokku/getting-started/installation/>`_.

1. Ensure you have PostgreSQL installed and running. Create a postgresql user with username `indigo`, and create a corresponding database called `indigo`. For example::

    $ sudo su - postgres -c 'createuser -d -P indigo'
    $ sudo su - postgres -c 'createdb indigo'

2. Create a new Dokku application::

    $ dokku apps:create indigo

3. (optional) Create a new AWS S3 account and bucket for storing attachments. You'll need the AWS Access Key Id and AWS Secret Access Key in the next step. You can safely skip this step if you don't care about saving attachments just yet.

4. Set config options as follows (ensure you enter your correct database and AWS settings)::

    $ dokku config:set indigo \
        DATABASE_URL=postgres://indigo:DATABASE-PASSWORD@DATABASE-HOST/indigo \
        DISABLE_COLLECTSTATIC=1 \
        DJANGO_DEBUG=false \
        DJANGO_SECRET_KEY=some random characters \
        AWS_ACCESS_KEY_ID=aws access key \
        AWS_SECRET_ACCESS_KEY=aws secret access key \
        AWS_S3_BUCKET=your-bucket-name

5. Deploying requires using `git push` to push to dokku. So you'll need to add `dokku` as a git remote on your local host. If you have cloned the `example-indigo` repo from above, you can do this::

    $ git remote add dokku dokku@DOKKU-HOSTNAME:indigo

6. Now deploy to dokku using `git push dokku`. This is how you deploy any and all updates::

    $ git push dokku

7. Create the an admin user by running this command **on the Dokku server**::

    $ dokku run indigo python manage.py createsuperuser

8. Visit your new Indigo app in your browser at https://your-dokku-host.example.com

9. Configure a country:

   * Visit `https://your-dokku-host.example.com/admin`
   * Under **Indigo API** click Countries, then click Add Country in the top right corner
   * Choose a country and primary language from the dropdown lists
   * Click Save

Background Tasks
----------------

Indigo can optionally do some operations in the background. It requires a worker or
cron job to run the ``django-background-tasks`` task queue. Indigo tasks are placed
in the ``indigo`` task queue. See `django-background-tasks <https://django-background-tasks.readthedocs.io/en/latest/>`
for more details on running background tasks.

To enable background tasks, set ``INDIGO.NOTIFICATION_EMAILS_BACKGROUND`` to True.
