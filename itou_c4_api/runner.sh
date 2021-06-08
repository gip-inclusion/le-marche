#!/usr/bin/env sh
# Getting static files for Admin panel hosting!
# ./manage.py collectstatic --noinput
export PYTHONPATH=$PYTHONPATH:./itou_c4_api
uwsgi --plugins http,python \
      --http "0.0.0.0:${PORT}" \
      --module itou_c4_api.wsgi \
      --master \
      --processes 4 \
      --threads 2
