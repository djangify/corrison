#!/bin/bash
python manage.py collectstatic --noinput
python manage.py migrate
exec gunicorn 'corrison.wsgi' --bind=0.0.0.0:3000 --timeout 120 --workers 3