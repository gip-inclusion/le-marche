#!/usr/bin/env sh
# Getting static files for Admin panel hosting!
# ./manage.py collectstatic --noinput
export PYTHONPATH=$PYTHONPATH:./lemarche
./manage.py collectstatic --noinput
uwsgi --plugins http,python \
      --http "${HOST}:${PORT}" \
      --module lemarche.wsgi \
      --master \
      --processes 4 \
      --threads 2
