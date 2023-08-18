#!/bin/sh
# -----------------------------------------------------------------------------
# launcherMinimalClient.sh
#
# This is an example of an application launcher (script).
#
# See README.txt for more information.
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# 1. Read input arguments (see README.txt)
# -----------------------------------------------------------------------------
# * $1 is the path to the VTS project file
# * $2 is the client application ID
# * ...
appid="$1"

# -----------------------------------------------------------------------------
# 2. Do any pre-process work as neeeded
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# 3. Output application arguments (used by the Broker to launch the application)
#    NOTE: launchers must always output the application ID first
# -----------------------------------------------------------------------------

# Launcher allows us to adapt Broker arguments to our application arguments
# Here we only use the application ID and ignore all other arguments

echo "$appid" --appid "$appid"

# End of file
