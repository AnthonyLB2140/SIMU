#!/bin/bash

# -----------------------------------------------------------------------------
# JSatOrb project: JSatOrb frontend logs viewing script
# -----------------------------------------------------------------------------
# This script enables the JSatOrb user to get a look at the JSatOrb 
# frontend server logs live.
# -----------------------------------------------------------------------------

# Show the message to stop the logs view
echo "-- Launching the display of JSatOrb's frontend server logs"
echo "-- Hit Ctrl-c to stop viewing"

sleep 2

echo "-- BEGINNING OF THE JSATOR FRONTEND LOGS --------------------------------------"
# Start to follow the JSatOrb container logs
docker logs --follow jsatorb-frontend-container
