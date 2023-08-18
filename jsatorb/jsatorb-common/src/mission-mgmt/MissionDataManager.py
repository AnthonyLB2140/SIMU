#------------------------------------------------------------------------------
# JSatOrb project
#------------------------------------------------------------------------------
# Mission Data management sub-module
#------------------------------------------------------------------------------

from os.path import join
import pathlib
import json
import glob
import sys

import MissionDataConstants

def logError(errorMsg):
    """
    Log an error to stderr
    
    Parameters:
        errorMsg: The error message to log
    """
    sys.stderr.write(errorMsg + "\n")

def getMissionDataDir():
    """
    Build the Mission Data root directory path
    
    Returns:
        String: The mission data directory absolute path
    """
    home = pathlib.Path.home()
    missionDataDir = join(home, MissionDataConstants.JSATORB_ROOT_DIR, MissionDataConstants.MISSION_DATA_DIR)
    return missionDataDir

def createMissionDataDir():
    """Create the Mission Data directory root folder"""
    missionDataDir = getMissionDataDir()
    pathlib.Path(missionDataDir).mkdir(parents=True, exist_ok=True)

def getMissionFilename(missionName):
    """Build the mission data filename based on the mission name."""
    return missionName + MissionDataConstants.MISSION_DATA_EXT

def getMissionAbsoluteFilename(missionName):
    """Build the mission data absolute filename (path + filename) based on the mission name."""
    return join(getMissionDataDir(), getMissionFilename(missionName))

def writeMissionDataFile(jsonContent, missionName):
    """
    Write JSON mission data into a file named after the mission.

    Returns: 
        Tuple(Boolean, message): 
            True if successfull, no message
            False otherwise with explaining message
    """

    # Create mission data directory if it doesn't exists
    if (not pathlib.Path(getMissionDataDir()).exists()):
        createMissionDataDir();

    absoluteFilename = getMissionAbsoluteFilename(missionName)    
    with open(absoluteFilename, 'w') as file:
        try:
            json.dump(jsonContent, file, indent=2)
        except IOError:
            msg = "Couldn't write file " + absoluteFilename + " !"
            logError(msg)
            return (False, msg)
    return (True, "")

def loadMissionDataFile(missionName):
    """
    Load JSON mission data from a file named after the mission.

    Parameters:
        missionName: The mission to load the data from
    Returns: 
        Tuple(JSON, message): 
            if file exists: The JSON formatted mission data, no message
            else: None with explaining message
    """

    missionFilename = getMissionFilename(missionName)
    absolutePath = join(getMissionDataDir(), missionFilename)
    try:
        with open(absolutePath, 'r') as file:
            try:            
                jsonContent = json.load(file)
                return (jsonContent, "")
            except IOError:
                msg = "Couldn't read file " + absolutePath + " !"
                logError(msg)
                return (None, msg)
    except FileNotFoundError:
        msg = "File " + absolutePath + " doesn't exists !"
        logError(msg)
        return (None, msg)

def listMissionDataFile():
    """
    List all available mission data sets previously stored.

    Returns: 
        List: The List of available mission data sets
    """

    missionDir = getMissionDataDir()
    missionDataFilter = join(missionDir, "*" + MissionDataConstants.MISSION_DATA_EXT)

    # Get list of absolute JSatOrb mission data filenames in the mission data directory.
    filesList = glob.glob(missionDataFilter)

    # Comprehension list to extract the mission name from the absolute filenames.
    missionsList = [e.replace(missionDir, '').replace(MissionDataConstants.MISSION_DATA_EXT,'').replace('/', '') for e in filesList if True]
    return missionsList

def duplicateMissionDataFile(srcMission, destMission):
    """
    Duplicate a mission data set previously stored into a duplicated mission data file.

    Parameters:
        srcMission: The mission to copy the data from
        destMission: The destination mission name (filename being based on the mission name)
    Returns: 
        Tuple(Boolean, message): 
            True if successfull, no message
            False otherwise with explaining message
    """

    # Load mission data
    jsonContent = loadMissionDataFile(srcMission)

    # If data exists
    if (not jsonContent is None):
        # Save it to another name
        return writeMissionDataFile(jsonContent, destMission)

def isMissionDataFileExists(missionName):
    """
    Test if the filename associated to a mission name exists

    Returns:
        Boolean: True if it exists, False otherwise
    """

    missionFile = pathlib.Path(getMissionAbsoluteFilename(missionName))
    return missionFile.exists()

def deleteMissionDataFile(missionName):
    """
    Delete the file associated to a mission

    Parameters:
        missionName: The mission to delete the associated file of
    Returns: 
        Tuple(Boolean, message): 
            True if successfull, no message
            False otherwise with explaining message
    """

    missionFilename = getMissionAbsoluteFilename(missionName)
    missionFile = pathlib.Path(missionFilename)
    if (missionFile.exists()):
        missionFile.unlink()
        return (True, "")
    else:
        msg = "The file " + missionFilename + " to delete doesn't exists !"
        logError(msg)
        return (False, msg)


if __name__ == '__main__':
    print("MissionDataDir=", getMissionDataDir())


