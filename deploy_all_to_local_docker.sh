#!/bin/bash
set -e

COMPOSE="docker/docker-compose.yml"
CMD="docker compose"

if ! docker compose version &>/dev/null; then
    CMD="docker-compose"
fi

case "${1:-up}" in
    build)
        $CMD -f $COMPOSE build --no-cache
        ;;
    up)
        mkdir -p docker/data/{db-data,phoenix,openwebui,pgadmin}
        $CMD -f $COMPOSE up -d
        sleep 3
        $CMD -f $COMPOSE ps
        ;;
    down)
        $CMD -f $COMPOSE down
        ;;
    restart)
        $CMD -f $COMPOSE restart
        ;;
    logs)
        $CMD -f $COMPOSE logs -f ${2:-}
        ;;
    ps)
        $CMD -f $COMPOSE ps
        ;;
    rag)
        echo "Building and deploying rag-api..."
        $CMD -f $COMPOSE build rag-api
        $CMD -f $COMPOSE up -d rag-api
        sleep 2
        $CMD -f $COMPOSE ps rag-api
        ;;
    clean)
        echo "Remove all data? (y/N)"
        read -r ans
        [[ "$ans" =~ ^[Yy]$ ]] && $CMD -f $COMPOSE down -v --remove-orphans
        ;;
    *)
        echo "Usage: $0 {build|up|down|restart|logs|ps|rag|clean}"
        exit 1
        ;;
esac
