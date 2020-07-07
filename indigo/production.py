from .settings import *

# Configure default domain name

ALLOWED_HOSTS = ['indigo.akn4undocs.ipbes.net', 'www.indigo.akn4undocs.ipbes.net','127.0.0.1']

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Configure Postgres database
db_from_env = dj_database_url.config(conn_max_age=500)
DATABASES['default'].update(db_from_env)
