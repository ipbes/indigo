import os

# fetch the development settings 
from .settings import *

# Configure default domain name

ALLOWED_HOSTS = ['indigo.akn4undocs.ipbes.net', 'www.indigo.akn4undocs.ipbes.net','127.0.0.1']

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Configure Postgres database
db_from_env = dj_database_url.config(conn_max_age=500)
DATABASES['default'].update(db_from_env)

# ##### SECURITY CONFIGURATION ############################

# TODO: Make sure, that sensitive information uses https
# TODO: Evaluate the following settings, before uncommenting them
# Settings from https://www.codingforentrepreneurs.com/blog/ssltls-settings-for-django/
# redirects all requests to https
SECURE_SSL_REDIRECT = True
# session cookies will only be set, if https is used
SESSION_COOKIE_SECURE = True
# how long is a session cookie valid?
SESSION_COOKIE_AGE = 1209600
CSRF_COOKIE_SECURE = True