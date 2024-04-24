FROM python:3.10-slim-buster

# Default environment: Dev
ARG ENV=dev
ENV APP_DIR="/app" \
    HOST=0.0.0.0 \
    PORT=8000 \
    PYTHONPATH=. \
    PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.5.1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/opt/.cache \
    NODE_VERSION=15

# Add new user to run the whole thing as non-root.
RUN set -ex \
    && addgroup app \
    && adduser --ingroup app --home ${APP_DIR} --disabled-password app;

WORKDIR $APP_DIR

COPY install-packages.sh .
RUN ./install-packages.sh

ENV VIRTUAL_ENV=$APP_DIR/.venv \
    PATH="$APP_DIR/.venv/bin:$PATH"

# Install Python dependencies
COPY poetry.lock pyproject.toml $APP_DIR
RUN pip install poetry==$POETRY_VERSION && pip install -I uwsgi
RUN poetry install --no-interaction --no-ansi --no-root

COPY ./lemarche ./lemarche
COPY ./config ./config
COPY ./manage.py ./manage.py
COPY ./docker ./docker
COPY ./scripts ./scripts

RUN echo '[ ! -z "$TERM" -a -r /etc/motd ] && cat /etc/issue && cat /etc/motd' \
    >> /etc/bash.bashrc \
    ; echo "\
    ===================================================================\n\
    = Le Marché de l'inclusion Dev Docker container                   =\n\
    ===================================================================\n\
    \n\
    (c) Plateforme de l'inclusion\n\
    \n\
    Source directory is /app \n\
    \
    Run App with :\n\
    > python ./manage.py runserver \$HOST:\$PORT\n\
    \n\
    "\
    > /etc/motd

USER app

CMD ["bash"]
