#!/bin/bash
python manage.py collectstatic --noinput
python manage.py makemigrations
python manage.py migrate
exec gunicorn 'corrison.wsgi' --bind=0.0.0.0:8000 --timeout 120 --workers 3