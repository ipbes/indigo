web: gunicorn --worker-class gevent indigo.wsgi:application -t 600 --log-file -

release: python manage.py migrate --noinput