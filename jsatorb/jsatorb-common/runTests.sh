#!/bin/bash

# -----------------------------------------------------------------------------
# JSatOrb Project: JSatOrb common module
# -----------------------------------------------------------------------------
# JSatorb Tests running script
# -----------------------------------------------------------------------------
# Arguments:
#  -a: auto mode (if set, the script is not asking confirmation to run tests)
# -----------------------------------------------------------------------------
# Exit codes:
#   0: No problem occured.
#   1: The user aborted the tests launch.
#   2: Orekit data archive is unavailable (but necessary for the tests).
# -----------------------------------------------------------------------------

LIGHT_GREEN="\e[92m"
LIGHT_RED="\e[91m"
YELLOW="\e[33m"
RESET_COLORS="\e[0m"

currentModule=$(basename `pwd`)

# Function that reset output text colors
function resetColors()
{
	\echo -e "$RESET_COLORS"
}

# Script usage
function usage()
{
	\echo "Usage: $0 [-a]"
	\echo ""
	\echo "    Where optional argument '-a' means 'automatic mode (non-interactive mode)"
	\echo "           so the script doesn't asks for confirmation to run the tests."
	\echo "    Examples: "
	\echo "        $0    : Asks the user to confirm before running the module tests."
	\echo "        $0 -a : Runs the module tests without asking for confirmation."
}

# Function that traps the Program interrupt and Program terminate signals
function trapSignals()
{
    echo -e "$YELLOW"
    echo "The program termination has been asked. Exiting"
    resetColors
    exit 2
}

# Activate the trap
trap trapSignals SIGINT SIGTERM

auto=false
# Test if the auto mode is set
if [ $# -eq 1 ]
then
    if [ $1 = "-a" ]
    then
        auto=true
    else
        echo -e "$YELLOW"
        echo "An invalid parameter has been provided to the script"
        resetColors
        usage
        exit 1
    fi
fi

# If not in automatic mode, ask the user for confirmation
if [ "$auto" = false ]; then
    echo "Please confirm that you want to run all the current JSatOrb module tests (Y/n):"
    read confirm

    if [ "$confirm" != "Y" ]; then
        echo "OK, aborting the tests run."
        exit 1
    fi
fi

echo -e "$LIGHT_GREEN"
echo "-------------------------------------------------------------------------------"
echo "Run the $currentModule module tests: START"
echo "-------------------------------------------------------------------------------"
resetColors

# Check if the Orekit data archive is available in the module's folder.
if [ ! -f ./orekit-data.zip ];then
    echo -e "$YELLOW"
    echo "Orekit data archive file (orekit-data.zip) not found in current directory."
    resetColors
    distantArchive="../jsatorb-rest-api/orekit-data.zip"
    if [ -f "$distantArchive" ];then
        echo "Trying to copy it from the JSatOrb REST API module folder."
        cp "$distantArchive" .
    else
        echo -e "$LIGHT_RED"
        echo "The Orekit data archive file is not available in the REST API module as well."
        echo "We have to stop the tests as this archive is necessary for the JSatOrb tests."
        resetColors
        exit 2
    fi
fi

# It is necessary to export anaconda functions 
# (see https://github.com/conda/conda/issues/7980)
source ~/JSatOrb/Tools/Anaconda3/etc/profile.d/conda.sh
conda activate JSatOrbEnv

echo -e "$LIGHT_GREEN"
echo "--- Running the tests ---"
resetColors

recap="$LIGHT_GREEN ---- JSatOrb module: $currentModule ----\n ---- Tests results summary:\n"
for f in ./test/Test*.py
do
    echo -e "$LIGHT_GREEN"
    echo "Running test module: $f"
    resetColors
    # Run the current test.
    python "$f"
    exitCode=$?

    # Add information to the tests results summary
    if [ "$exitCode" -eq 0 ]; then
        recap="$recap\n$LIGHT_GREEN\tSUCCESS (exit code $exitCode)\tTest $f"
    else
        recap="$recap\n$LIGHT_RED\tFAILED  (exit code $exitCode)\tTest $f"
    fi    
done
recap="$recap\n\nSee logs above for more details about possible failures.$RESET_COLORS"

echo -e "$recap"

echo -e "$LIGHT_GREEN"
echo "-------------------------------------------------------------------------------"
echo "Run the $currentModule module tests: END"
echo "-------------------------------------------------------------------------------"
resetColors