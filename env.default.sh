# Clevercloud provides "ADDON" environment variables.
# If you wish to change these, update lemarche/settings.py
# to reflect the changes

# PostGreSQL Config
export POSTGRESQL_ADDON_HOST="localhost"
export POSTGRESQL_ADDON_PORT="5432"
export POSTGRESQL_ADDON_USER=""
export POSTGRESQL_ADDON_PASSWORD=""
export POSTGRESQL_ADDON_DB=""

# Django Settings
export SECRET_KEY="coucou"
export DJANGO_SETTINGS_MODULE="config.settings.dev"
export TRACKER_HOST="https://example.com"

# APIs
export API_EMPLOIS_INCLUSION_TOKEN=""

# MTCAPTCHA
# ########################
export MTCAPTCHA_PRIVATE_KEY=""
export MTCAPTCHA_PUBLIC_KEY=""

# OPENAI
# ########################
export OPENAI_ORG=""
export OPENAI_API_BASE=""
export OPENAI_API_KEY=""
export OPENAI_MODEL=""

# API Entreprise / see https://entreprise.api.gouv.fr/developpeurs#kit-de-mise-en-production
export API_ENTREPRISE_RECIPIENT=""
export API_ENTREPRISE_BASE_URL="https://staging.entreprise.api.gouv.fr/v3"
export API_ENTREPRISE_TOKEN=""
