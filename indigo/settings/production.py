from .settings import *

# Configure default domain name

ALLOWED_HOSTS = ['10.208.58.26', '127.0.0.1', '172.17.0.2', '172.17.0.3']

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Configure Postgres database
db_from_env = dj_database_url.config(conn_max_age=500)
DATABASES['default'].update(db_from_env)
