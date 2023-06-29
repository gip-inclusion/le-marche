# ----------------------------------------------------
# Base-image
# ----------------------------------------------------
FROM python:3.10-slim-buster as common-base
# Django directions: https://blog.ploetzli.ch/2020/efficient-multi-stage-build-django-docker/
# Pip on docker : https://pythonspeed.com/articles/multi-stage-docker-python/
# https://blog.mikesir87.io/2018/07/leveraging-multi-stage-builds-single-dockerfile-dev-prod/
# https://pythonspeed.com/articles/base-image-python-docker-images/

# Default environment: Dev
ARG ENV=dev
ENV APP_DIR="/app"

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.5.1 \
    NODE_VERSION=15

ENV HOST=0.0.0.0 \
    PORT=8000

WORKDIR /app

COPY install-packages.sh .
RUN ./install-packages.sh

# ----------------------------------------------------
# Install dependencies
# ----------------------------------------------------
FROM common-base AS dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV GECKODRIVER_URL=https://github.com/mozilla/geckodriver/releases/download/v0.33.0/geckodriver-v0.33.0-linux32.tar.gz

RUN pip install poetry==$POETRY_VERSION
RUN pip install -I uwsgi

#     apt-get install build-essential -y
COPY poetry.lock pyproject.toml /app/

RUN poetry config virtualenvs.create false && \
    poetry config virtualenvs.path /opt/venv && \
    poetry install $(test $ENV == "prod" && echo "--no-dev") --no-interaction --no-ansi

# Needed for selenium test
RUN wget -qO- $GECKODRIVER_URL | tar xvz -C /usr/bin/

# ----------------------------------------------------
# Build project
# ----------------------------------------------------
FROM common-base AS app-run
COPY --from=dependencies /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    VIRTUALENV="/opt/venv" \
    PYTHONPATH="$PYTHONPATH:/app/lemarche:/app/config"
COPY ./lemarche ./lemarche
COPY ./config ./config
COPY ./manage.py ./manage.py
COPY ./pyproject.toml ./pyproject.toml
COPY ./docker ./docker
COPY ./scripts ./scripts

# ----------------------------------------------------
# Run Dev
# ----------------------------------------------------
FROM app-run AS dev
ENV DJANGO_SETTINGS_MODULE="config.settings.dev" \
    ENV="dev" \
    DEBUG="True"

RUN echo '[ ! -z "$TERM" -a -r /etc/motd ] && cat /etc/issue && cat /etc/motd' \
    >> /etc/bash.bashrc \
    ; echo "\
    ===================================================================\n\
    = Bitoubi Dev Docker container                                =\n\
    ===================================================================\n\
    \n\
    (c) plateforme de l'Inclusion\n\
    \n\
    Source directory is /app \n\

    Run App with :\n\
    > python ./manage.py runserver \$HOST:\$PORT\n\
    \n\
    "\
    > /etc/motd

CMD ["bash"]

# ----------------------------------------------------
# Run Dev
# ----------------------------------------------------
FROM app-run AS prod
ENV DJANGO_SETTINGS_MODULE="config.settings.prod" \
    ENV="prod" \
    DEBUG="False"

CMD [".docker/dev/django/entrypoint.sh"]

# # For some _real_ performance, at cost of ease of use:
# FROM python:3.9-alpine as prod
# COPY --from=dependencies /opt/venv /opt/venv
# ENV PATH="/opt/venv/bin:$PATH"
# COPY . .
# RUN apk add python3-dev build-base linux-headers pcre-dev
# RUN pip install uwsgi
