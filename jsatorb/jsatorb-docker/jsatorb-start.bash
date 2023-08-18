#!/bin/bash

# -----------------------------------------------------------------------------
# JSatOrb project: JSatOrb Docker compose starting script
# -----------------------------------------------------------------------------
# This script get the current user ID and Group UID, prior to running the 
# Docker compose up command.
# Those values are used in the Docker compose script in order to replace the 
# default root user by the current user in the container.
# Asscociated with the correct bind-mount (see docker-compose file for details),
# it enables to write the mission data sets in the 
# /home/$USER/JSatOrb/mission-data folder with the correct identity and file 
# permissions.
# -----------------------------------------------------------------------------

# Get User ID and Group UID in two variables to be used in the Docker-compose file.
export USER_ID=$(id --user) 
export GROUP_UID=$(id --group)

# Show user id and group uid values in console
echo "USER_ID=$USER_ID"
echo "GROUP_UID=$GROUP_UID"

# Start the JSatOrb Docker containers.
docker-compose up -d
