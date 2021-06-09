#!/usr/bin/env sh
# Getting static files for Admin panel hosting!
# ./manage.py collectstatic --noinput
export PYTHONPATH=$PYTHONPATH:./itou_c4_api
./manage.py collectstatic --noinput
uwsgi --plugins http,python \
      --http "${HOST}:${PORT}" \
      --module itou_c4_api.wsgi \
      --master \
      --processes 4 \
      --threads 2
