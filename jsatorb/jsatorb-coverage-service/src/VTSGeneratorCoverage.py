import orekit
vm = orekit.initVM()

from orekit.pyhelpers import setup_orekit_curdir
setup_orekit_curdir()

import sys
sys.path.append('../')
from ListCelestialBodies import ListCelestialBodies

from copy import deepcopy
from math import pi, radians

from org.orekit.bodies import CelestialBodyFactory
from org.orekit.propagation.analytical.tle import TLE
from org.orekit.time import AbsoluteDate, TimeScalesFactory

def read(switcher, listLines, newFile, general, groundStations, folderData, folderModels, level):
    """
    Function that reads lines in model and when detects a key in given switcher, run
    corresponding function
    """
    startLine = ' '*level
    for line in listLines:
        isKeyDetected = False
        for key in switcher:
            if key in line:
                isKeyDetected = True
                detectedKey = key
                break
        if isKeyDetected:
                switcher[detectedKey](newFile, general, groundStations, folderData, folderModels, level+1)
        else:
            newFile.write(startLine+line)

def dateToString(date, timeScale):
    """
    Function that convert date into string modified julian days and seconds in day
    """
    components = date.getComponents(timeScale)
    mjd = components.getDate().getMJD()
    second = components.getTime().getSecondsInLocalDay()
    return ' '.join([str(mjd), str(second)])

def generalBlock(newFile, general, groundStations, folderData, folderModels, level):
    """
    Function that writes initial and end dates in the first line of vts file
    """
    optionsCoverage = general['options']['COVERAGE']
    startLine = ' '*level
    line = '<General Name="" StartDateTime="[INITDATE]" EndDateTime="[ENDDATE]"/>\n'
    # Initial and end dates
    utc = TimeScalesFactory.getUTC()
    initDate = AbsoluteDate(optionsCoverage['timeStart'], utc)
    initDateString = dateToString(initDate, utc)

    endDate = AbsoluteDate(optionsCoverage['timeEnd'], utc)
    endDateString = dateToString(endDate, utc)

    line = line.replace('[INITDATE]', initDateString)
    line = line.replace('[ENDDATE]', endDateString)

    newFile.write(startLine+line)

def timeLineBlock(newFile, general, groundStations, folderData, folderModels, level):
    """
    Function that writes timeline lines related to the VTS broker
    """
    startLine = ' '*level

    lines = [
        '<TimelineOptions ProjectLocked="1" CursorLocked="0" CursorRatio="0" ViewStart="33282 0.000000" ViewSpan="0" DateFormat="ISODate" NoBadgeFiltered="0" BadgeFiltered="">\n',
        ' <TimelineScenario Name="Scenario" Pos="0" Size="23"/>\n',
    ]
    for line in lines:
        newFile.write(startLine+line)
    
    line = '</TimelineOptions>\n'
    newFile.write(startLine+line)   

def entityBlock(newFile, general, groundStations, folderData, folderModels, level):
    """
    Function that writes all entity-related lines, i.e., central body and satellites,
    by calling the corresponding functions, using a switcher
    """
    lines = [
        '<Entities>\n',
        '[BODY]',
        '</Entities>\n'
    ]
    switcherEntity = {
        '[BODY]': bodyBlock,
    }
    read(switcherEntity, lines, newFile, general, groundStations, folderData, folderModels, level)

def bodyBlock(newFile, general, groundStations, folderData, folderModels, level):
    """
    Function that writes central-body-related lines, and calls a function for writing lines related to
    ground stations
    """
    if 'celestialBody' in general:
        centralBody = general['celestialBody'].lower().capitalize()
    else:
        centralBody = 'Earth'
    if centralBody.upper() == 'SUN':
        parentpath = ''
    elif centralBody.upper() == 'MOON':
        parentpath = 'Sol/Earth'
    else:
        parentpath = 'Sol'
    
    options = general["options"]

    startLine = ' '*level
    with open(folderModels+'bodyModelCoverage.vts') as bodyModel:
        for line in bodyModel:
            if '[GROUNDSTATIONS]' in line:
                for groundStation in groundStations:
                    gsBlock(newFile, groundStation, centralBody, folderModels, level+1)
            elif '[CENTRALBODY]' in line:
                lineModified = line.replace('[CENTRALBODY]', centralBody).replace(
                    '[PARENTPATH]', parentpath)
                newFile.write(startLine+lineModified)
            elif '[NAMELAYER]' in line:
                optionsCoverage = options["COVERAGE"]
                plotType = optionsCoverage["plotType"]
                nameFile = plotType
                lineModified = line.replace('[NAMELAYER]', nameFile)
                newFile.write(startLine+lineModified)
            else:
                newFile.write(startLine+line)

def gsBlock(newFile, groundStation, centralBody, folderModels, level):
    """
    Function that writes ground-stations-related lines
    """
    latitude = str(groundStation['latitude']) # in degrees
    longitude = str(groundStation['longitude']) # in degrees
    altitude = str(groundStation['altitude']) # in m

    startLine = ' '*level
    with open(folderModels+'gsModel.vts') as gsModel:
        for line in gsModel:
            if '[NAMESTATION]' in line:
                lineModified = line.replace('[NAMESTATION]', groundStation['name'])
                newFile.write(startLine+lineModified)
            elif '[SENSORGS]' in line:
                pass
            elif '[LATSTATION]' in line:
                lineModified = line.replace('[LATSTATION]', latitude).replace(
                    '[LONGSTATION]', longitude).replace('[ALTSTATION]', altitude)
                newFile.write(startLine+lineModified)
            else:
                newFile.write(startLine+line)

def surfaceViewBlock(newFile, general, groundStations, folderData, folderModels, level):
    """
    Function that write lines to configurate SurfaceView (2D visualization)
    """
    startLine = ' '*(level+3)

    if general['celestialBody'].upper() == 'SUN':
        parentPath = 'Sol'
    elif general['celestialBody'].upper() == 'MOON':
        parentPath = 'Sol/Earth/Moon'
    else:
        parentPath = 'Sol/' + general['celestialBody'].lower().capitalize()

    optionsCoverage = general['options']['COVERAGE']
    plotType = optionsCoverage['plotType']

    lineVisu = [
        '<Command Str="CMD PROP WindowGeometry 0 0 1100 640"/>\n',
        '<Command Str="CMD STRUCT SubEntityPointVisible &quot;Sol&quot; false"/>\n',
        '<Command Str="CMD STRUCT VisibilityCircleVisible &quot;Sol&quot; false"/>\n',
        '<Command Str="CMD STRUCT TrackVisible &quot;Sol&quot; false"/>\n',
        '<Command Str="CMD STRUCT AllStationVisible &quot;[PARENTPATH]&quot; false"/>\n',
        '<Command Str="CMD STRUCT AllStationTextVisible &quot;[PARENTPATH]&quot; false"/>\n',
        '<Command Str="CMD STRUCT AllSensorStationContourVisible &quot;[PARENTPATH]&quot; false"/>\n',
        '<Command Str="CMD STRUCT AllSensorStationSurfaceVisible &quot;[PARENTPATH]&quot; false"/>\n',
        '<Command Str="CMD STRUCT LayerOpacity &quot;[PARENTPATH]/[PLOTTYPE]&quot; 0.8"/>\n'
        ]

    for line in lineVisu:
        if '[PARENTPATH]' in line:
            lineModified = line.replace('[PARENTPATH]', parentPath).replace('[PLOTTYPE]', plotType)
            newFile.write(startLine+lineModified)
        else:
            newFile.write(startLine+line)

class VTSGeneratorCoverage:
    """
    Class that generates the VTS configuration file for the given mission, for coverage
    visualization, using different models
    """
    def __init__(self, nameNewFile, nameModel, folderModels):
        self.nameNewFile =  nameNewFile
        self.nameModel = folderModels + nameModel
        self.folderModels = folderModels

    def generate(self, general, options, groundStations):
        general['options'] = options
        level = 0
        switcherFile = {
            '[GENERAL]': generalBlock,
            '[TIMELINE]': timeLineBlock,
            '[ENTITIES]': entityBlock,
            '[SURFACEVIEW]': surfaceViewBlock,
        }
        folderData = 'Data/'

        utc = TimeScalesFactory.getUTC()

        with open(self.nameNewFile,'w') as newFile, open(self.nameModel,'r') as model:
            read(switcherFile, model, newFile, general, groundStations, folderData, self.folderModels, level)
