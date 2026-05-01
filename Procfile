web: gunicorn parque.wsgi:application
release: python manage.py migrate && python manage.py createsuperuser --noinput
