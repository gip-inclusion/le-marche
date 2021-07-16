#!/bin/bash
# Docker environment settings : https://vsupalov.com/docker-arg-env-variable-guide/
docker_dev() {
    docker build \
        --target dev \
        -t "c4_api" -f ./Dockerfile . \
        --build-arg ENV=DEV \
    && docker run --rm -it \
        -p 8000:8000 \
        --env-file=env.docker.local \
        -e DEBUG="true" \
        --name c4_api \
        -v `pwd`/lemarche:/app/lemarche \
        -v `pwd`/config:/app/config \
        c4_api
}

docker_prod() {
    docker build \
        --target prod \
        -t "c4_api" -f ./Dockerfile . \
        --build-arg ENV=DEV \
    && docker run --rm -it \
        -p 8000:8000 \
        --env-file=env.docker.local \
        -e DEBUG="false" \
        --name c4_api \
        c4_api
}

usage() {
    echo "
-p|--prod    run full docker (Prod config)
-d|--dev     run dev docker (Dev config and local mounts)
"
}

while [ "$1" != "" ]; do
    case $1 in
        -p | --prod )
            echo "Running full docker"
            docker_prod
            exit
            ;;
        -d | --dev )
            echo "Running dev docker"
            docker_dev
            exit
            ;;
        * )
            usage
            exit 1
            ;;
    esac
    shift
done
usage
exit 1
            
