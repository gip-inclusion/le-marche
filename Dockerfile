FROM python:3.8-slim-buster

ARG ENV="dev"
ARG MYSQL_DB="database" \
    MYSQL_HOST="localhost"\
    MYSQL_USER="root" \
    MYSQL_PORT="3306" \
    MYSQL_PASSWORD="[SECRET]"

ENV ENV=${ENV} \
  PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  POETRY_VERSION=1.1.1 \
  NODE_VERSION=14 \
  HOST=0.0.0.0 \
  PORT=8000

ENV MYSQL_DB=${MYSQL_DB} \
    MYSQL_HOST=${MYSQL_HOST} \
    MYSQL_PORT=${MYSQL_PORT} \
    MYSQL_USER=${MYSQL_USER} \
    MYSQL_PASSWORD=${MYSQL_PASSWORD} \
    PYTHONPATH=${PYTHONPATH}:/app/itou_c4_api
 

COPY install-packages.sh .
RUN ./install-packages.sh

# Install python environment
RUN pip install "poetry==$POETRY_VERSION"
RUN pip install uwsgi

#     apt-get install build-essential -y
WORKDIR /app
COPY poetry.lock pyproject.toml /app/
COPY . /app

RUN poetry config virtualenvs.create false && \
    poetry install $(test $ENV == "prod" && echo "--no-dev") --no-interaction --no-ansi

# CMD ["bash"]
CMD ["itou_c4_api/runner.sh"]
