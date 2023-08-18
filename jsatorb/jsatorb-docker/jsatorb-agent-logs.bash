#!/bin/bash

# -----------------------------------------------------------------------------
# JSatOrb project: JSatOrb agent logs viewing script
# -----------------------------------------------------------------------------
# This script enables the JSatOrb user to get a look at the JSatOrb 
# agent logs live.
# -----------------------------------------------------------------------------

# Show the message to stop the logs view
echo "-- Launching the display of JSatOrb's agent logs"
echo "-- Hit Ctrl-c to stop viewing"

sleep 2

# Follow the live feed of the JSatOrb Agent log file
tail -F JSatOrbAgent/jsatorb-agent.log
