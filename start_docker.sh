#!/bin/bash
# Docker environment settings : https://vsupalov.com/docker-arg-env-variable-guide/
docker_dev() {
    docker build \
        --target dev \
        -t "c4_api" -f ./Dockerfile . \
        --build-arg ENV=DEV \
    && docker run --rm -it \
        -p 8000:8000 \
        --env-file=env.docker_dev.local \
        -e DEBUG="true" \
        --name c4_api \
        -v `pwd`/lemarche:/app/lemarche \
        -v `pwd`/config:/app/config \
        c4_api
}

docker_compose() {
    docker-compose up --force-recreate
}

docker_prod() {
    docker build \
        --target prod \
        -t "c4_api" -f ./Dockerfile . \
        --build-arg ENV=PROD \
    && docker run --rm -it \
        -p 8000:8000 \
        --env-file=env.docker_prod.local \
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
        -c | --compose )
            echo "Running dev docker-compose"
            docker_compose
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
            
