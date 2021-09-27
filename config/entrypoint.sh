#!/usr/bin/env sh
# Getting static files for Admin panel hosting!
# ./manage.py collectstatic --noinput
export PYTHONPATH=$PYTHONPATH:./lemarche:./config

# Include compiled sources
./manage.py collectstatic --noinput
./manage.py compress --force

./manage.py migrate
uwsgi --plugins http,python \
      --http "${HOST}:${PORT}" \
      --module config.wsgi \
      --master \
      --processes 4 \
      --threads 2
