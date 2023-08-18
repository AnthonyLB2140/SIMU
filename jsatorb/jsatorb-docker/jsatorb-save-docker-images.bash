#!/bin/bash

# -----------------------------------------------------------------------------
# JSatOrb project: JSatOrb Docker images saving script
# -----------------------------------------------------------------------------
# This script has to be run once in order to save the JSatOrb Docker images 
# into a local Docker images folder, as they are not available through 
# DockerHub or anywhere else on the Web.
# -----------------------------------------------------------------------------
# This script has to be run from the jsatorb-docker project's root folder.
# -----------------------------------------------------------------------------

echo "Saving JSatOrb Docker images"

echo "-- JSatOrb frontend Docker image"
# Save the JSatOrb frontend Docker image.
docker save jsatorb-frontend:prod | gzip > ./docker_images/jsatorb-frontend-docker-image.tgz

# Check if the command succeeded
if [ $? -ne 0 ]; then
    echo "The Docker image save failed !"
    exit 1
fi

echo "-- JSatOrb backend Docker image"
# Save the JSatOrb backend Docker image.
docker save jsatorb-backend:prod | gzip > ./docker_images/jsatorb-backend-docker-image.tgz

# Check if the command succeeded
if [ $? -ne 0 ]; then
    echo "The Docker image save failed !"
    exit 1
fi

echo "-- JSatOrb Celestrak server Docker image"
# Save the JSatOrb Celestrak Docker image.
docker save thib21/celestrak-json-proxy:dev | gzip > ./docker_images/celestrak-json-proxy-docker-image.tgz

# Check if the command succeeded
if [ $? -ne 0 ]; then
    echo "The Docker image save failed !"
    exit 1
fi

echo "JSatOrb Docker images have been saved"