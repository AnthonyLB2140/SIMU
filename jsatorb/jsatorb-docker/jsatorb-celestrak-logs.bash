#!/bin/bash

# -----------------------------------------------------------------------------
# JSatOrb project: JSatOrb Celestrak server logs viewing script
# -----------------------------------------------------------------------------
# This script enables the JSatOrb user to get a look at the JSatOrb 
# Celestrak server logs live.
# -----------------------------------------------------------------------------

# Show the message to stop the logs view
echo "-- Launching the display of JSatOrb's Celestrak server logs"
echo "-- Hit Ctrl-c to stop viewing"

sleep 2

echo "-- BEGINNING OF THE JSATOR CELESTRAK LOGS --------------------------------------"
# Start to follow the JSatOrb container logs
docker logs --follow celestrak-json-proxy-container
