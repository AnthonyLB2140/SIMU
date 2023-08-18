#!/bin/bash

# -----------------------------------------------------------------------------
# JSatOrb project: JSatOrb Docker images installing script
# -----------------------------------------------------------------------------
# This script has to be run once in order to install the JSatOrb Docker images 
# into the local Docker images repository, as they are not available through 
# DockerHub or anywhere else on the Web.
# -----------------------------------------------------------------------------

echo "Installing JSatOrb Docker images"

echo "-- JSatOrb frontend Docker image"
# Load the JSatOrb frontend Docker image.
gunzip -c ./docker_images/jsatorb-frontend-docker-image.tgz | docker load

# Check if the command succeeded
if [ $? -ne 0 ]; then
    echo "The Docker image load failed !"
    exit 1
fi

echo "-- JSatOrb backend Docker image"
# Load the JSatOrb backend Docker image.
gunzip -c ./docker_images/jsatorb-backend-docker-image.tgz | docker load

# Check if the command succeeded
if [ $? -ne 0 ]; then
    echo "The Docker image load failed !"
    exit 1
fi

echo "-- JSatOrb Celestrak server Docker image"
# Load the JSatOrb Celestrak Docker image.
gunzip -c ./docker_images/celestrak-json-proxy-docker-image.tgz | docker load

# Check if the command succeeded
if [ $? -ne 0 ]; then
    echo "The Docker image load failed !"
    exit 1
fi

echo "JSatOrb Docker images has been installed"
