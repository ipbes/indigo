from .settings import *

# Configure default domain name

ALLOWED_HOSTS = ['10.208.58.26', '127.0.0.1', '172.17.0.4', '172.17.0.5', '3.238.71.183']

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Configure Postgres database
db_from_env = dj_database_url.config(conn_max_age=500)
DATABASES['default'].update(db_from_env)

# AWS settings
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_S3_BUCKET')
AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME
AWS_S3_FILE_OVERWRITE = False

MEDIA_URL = "https://%s/" % AWS_S3_CUSTOM_DOMAIN
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
