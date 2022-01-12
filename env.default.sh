# Clevercloud provides "ADDON" environment variables.
# If you wish to change these, update lemarche/settings.py
# to reflect the changes

# PostGreSQL Config
export POSTGRESQL_HOST="localhost"
export POSTGRESQL_PORT="5432"
export LEMARCHE_POSTGRES_USER=""
export LEMARCHE_POSTGRES_PASSWORD=""
export LEMARCHE_POSTGRES_DB=""

# Django Settings
export SECRET_KEY="coucou"
export DJANGO_SETTINGS_MODULE="config.settings.dev"
export TRACKER_HOST="https://example.com"
