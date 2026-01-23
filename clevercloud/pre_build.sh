# generate requirements file to let clevercloud know which packages to install
uv export --format requirements-txt --no-dev --frozen > requirements.txt
