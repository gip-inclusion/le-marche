#!/bin/bash

# ask if the use wants to run poetry update
printf "Run 'poetry update' first ? (y/n)"
read answer
if [ "$answer" != "${answer#[Yy]}" ]; then 
    poetry update
fi

# update requirements .txt files
echo "Updating 'requirements/dev.txt'"
poetry export --without-hashes --with dev --output requirements/dev.txt
echo "Updating 'requirements/staging.txt'"
poetry export --without-hashes --output requirements/staging.txt
