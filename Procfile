web: gunicorn config.wsgi --log-file -

postdeploy: python manage.py migrate && python manage.py collectstatic --noinput