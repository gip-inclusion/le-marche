#!/bin/bash
poetry update
poetry export --without-hashes --with dev --output requirements/dev.txt
poetry export --without-hashes --output requirements/staging.txt
