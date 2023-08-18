#!/bin/bash

# -----------------------------------------------------------------------------
# JSatOrb project: JSatOrb backend logs viewing script
# -----------------------------------------------------------------------------
# This script enables the JSatOrb user to get a look at the JSatOrb 
# backend/REST server logs live.
# -----------------------------------------------------------------------------

# Show the message to stop the logs view
echo "-- Launching the display of JSatOrb's backend server logs"
echo "-- Hit Ctrl-c to stop viewing"

sleep 2

echo "-- BEGINNING OF THE JSATOR BACKEND LOGS --------------------------------------"
# Start to follow the JSatOrb container logs
docker logs --follow jsatorb-backend-container
