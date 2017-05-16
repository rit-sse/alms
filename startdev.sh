#!/bin/bash

# Cleanup
function finish {
    docker-compose -f docker-compose.dev.yml kill
    docker-compose -f docker-compose.dev.yml rm
}
trap finish EXIT

# start required services
docker-compose -f docker-compose.dev.yml up -d

# bootstrap tables in the db
sleep 2
docker run -it --rm --network alms_default -e POSTGRES_PASSWORD=notreall ritsse/node-api:dev-latest npm run bootstrap

# Drop into shell with shared network
docker run -it -v `pwd`:/usr/src/app -e POSTGRES_PASSWORD=notreall --network alms_default python:3 bash
