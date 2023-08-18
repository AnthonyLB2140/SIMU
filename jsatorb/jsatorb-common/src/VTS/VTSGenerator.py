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

def read(switcher, listLines, newFile, general, satellites, groundStations, folderData, folderModels, level):
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
                switcher[detectedKey](newFile, general, satellites, groundStations, folderData, folderModels, level+1)
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

def generalBlock(newFile, general, satellites, groundStations, folderData, folderModels, level):
    """
    Function that writes initial and end dates in the first line of vts file
    """
    
    startLine = ' '*level
    line = '<General Name="" StartDateTime="[INITDATE]" EndDateTime="[ENDDATE]"/>\n'
    # Initial and end dates
    utc = TimeScalesFactory.getUTC()
    initDate = AbsoluteDate(general['timeStart'], utc)
    initDateString = dateToString(initDate, utc)
    
    endDate = AbsoluteDate(general['timeEnd'], utc)
    endDateString = dateToString(endDate, utc)
    
    line = line.replace('[INITDATE]', initDateString)
    line = line.replace('[ENDDATE]', endDateString)

    newFile.write(startLine+line)

def timeLineBlock(newFile, general, satellites, groundStations, folderData, folderModels, level):
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
    
    line = ' <TimelineFile Name="[NAMEFILE]" Pos="[NUMBER]" Size="18" Badges="" Mode="Interval" Overlay="false"/>\n'

    idx = 1
    for sat in satellites:
        if 'ECLIPSE' in general['options']:
            nameFile = sat['name'] + '_MEM_ECLIPSE.TXT'
            lineModified = line.replace('[NAMEFILE]', nameFile).replace('[NUMBER]', str(idx))
            newFile.write(startLine+lineModified)
            idx = idx + 1
        elif 'VISIBILITY' in general['options']:
            for gs in groundStations:
                nameFile = sat['name'] + '_MEM_VISIBILITY_' + gs['name'] + '.TXT'
                lineModified = line.replace('[NAMEFILE]', nameFile).replace('[NUMBER]', str(idx))
                newFile.write(startLine+lineModified)
                idx = idx + 1 

    line = '</TimelineOptions>\n'
    newFile.write(startLine+line)   

def entityBlock(newFile, general, satellites, groundStations, folderData, folderModels, level):
    """
    Function that writes all entity-related lines, i.e., central body and satellites,
    by calling the corresponding functions, using a switcher
    """
    
    lines = [
        '<Entities>\n',
        '[BODY]',
        '[SATELLITES]',
        '</Entities>\n'
    ]
    switcherEntity = {
        '[BODY]': bodyBlock,
        '[SATELLITES]': satellitesBlock
    }
    read(switcherEntity, lines, newFile, general, satellites, groundStations, folderData, folderModels, level)

def bodyBlock(newFile, general, satellites, groundStations, folderData, folderModels, level):
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
    
    startLine = ' '*level
    with open(folderModels+'bodyModel.vts') as bodyModel:
        for line in bodyModel:
            if '[GROUNDSTATIONS]' in line:
                for groundStation in groundStations:
                    gsBlock(newFile, groundStation, centralBody, satellites, folderModels, level+1)
            elif '[CENTRALBODY]' in line:
                lineModified = line.replace('[CENTRALBODY]', centralBody).replace(
                    '[PARENTPATH]', parentpath)
                newFile.write(startLine+lineModified)
            else:
                newFile.write(startLine+line)

def gsBlock(newFile, groundStation, centralBody, satellites, folderModels, level):
    """
    Function that writes ground-stations-related lines and calls a function for lines
    related to the ground station sensors
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
                sensorGSBlock(newFile, groundStation, centralBody, satellites, folderModels, level+1)
            elif '[LATSTATION]' in line:
                lineModified = line.replace('[LATSTATION]', latitude).replace(
                    '[LONGSTATION]', longitude).replace('[ALTSTATION]', altitude)
                newFile.write(startLine+lineModified)
            else:
                newFile.write(startLine+line)

def sensorGSBlock(newFile, groundStation, centralBody, satellites, folderModels, level):
    """
    Function that writes lines related to the ground station sensors
    """
    
    if 'range' in groundStation:
        altSensorStation = str(groundStation['range']) # in km
    else:
        # Central body radius and GM in m, to have an average value of the 
        # altitude for the display of station sensors
        radiusBody = ListCelestialBodies.getBody(centralBody.upper()).radius
        muBody = CelestialBodyFactory.getBody(centralBody.upper()).getGM()
        listRadius = []
        for sat in satellites:
            typeSat = sat['type']
            if typeSat == 'keplerian':
                radiusCur = float(sat['sma'])
            elif typeSat == 'cartesian':
                radiusCur = (float(sat['x'])**2+float(sat['y'])**2+float(sat['z'])**2)**0.5
            elif typeSat == 'tle':
                satTLE = TLE(sat['line1'], sat['line2'])
                nCur = satTLE.getMeanMotion() # in rad/s
                radiusCur = muBody**(1./3.) / nCur**(2./3.)
            else:
                raise TypeError("Unknown satellite type")
            listRadius.append(radiusCur)
        altSensorStation = str( (sum(listRadius)/len(listRadius) - radiusBody) * 1e-3 ) # in km

    elevation = float(groundStation['elevation']) # in degrees
    halfAngleStation = str(radians(90. - elevation))

    startLine = ' '*level
    with open(folderModels+'sensorGSModel.vts') as sensorGSModel:
        for line in sensorGSModel:
            if '[ALTSENSORSTATION]' in line:
                lineModified = line.replace('[ALTSENSORSTATION]', altSensorStation)
                newFile.write(startLine+lineModified)
            elif '[HALFANGLESTATION]' in line:
                lineModified = line.replace('[HALFANGLESTATION]', halfAngleStation)
                newFile.write(startLine+lineModified)
            else:
                newFile.write(startLine+line)

def satellitesBlock(newFile, general, satellites, groundStations, folderData, folderModels, level):
    """
    Function that writes satellite-related lines by calling for each satellite 
    a function that writes lines for one satellite
    """
    
    for sat in satellites:
        satBlock(newFile, general, sat, folderData, folderModels, level)

def satBlock(newFile, general, satellite, folderData, folderModels, level):
    """
    Function that writes lines for one satellite and calls another function
    for writing satellite-sensor-related lines
    """

    if general['celestialBody'].upper() == 'SUN':
        parentPath = 'Sol'
    elif general['celestialBody'].upper() == 'MOON':
        parentPath = 'Sol/Earth/Moon'
    else:
        parentPath = 'Sol/' + general['celestialBody'].lower().capitalize()

    nameOemSat = folderData + satellite['name'] + '_OEM_POSITION.TXT'
    nameColorSat = folderData + satellite['name'] + '_COLOR.TXT'
    nameAemSat = folderData + satellite['name'] + '_AEM_ATTITUDE.TXT'

    startLine = ' '*level
    with open(folderModels+'satelliteModel.vts') as satModel:
        for line in satModel:
            if '[PARENTPATH]' in line:
                lineModified = line.replace('[PARENTPATH]', parentPath).replace(
                    '[NAMESAT]', satellite['name'])
                newFile.write(startLine+lineModified)
            elif '[NAMESAT]' in line:
                lineModified = line.replace('[NAMESAT]', satellite['name'])
                newFile.write(startLine+lineModified)
            elif '[SAT_POSITION_FILE]' in line:
                lineModified = line.replace('[SAT_POSITION_FILE]', nameOemSat)
                newFile.write(startLine+lineModified)
            elif '[SAT_ATTITUDE_FILE]' in line:
                if 'ATTITUDE' in general['options']:
                    linesAttitude = [
                        ' <Value>\n',
                        '  <File Name="[ATTITUDE_FILE]"/>\n'.replace('[ATTITUDE_FILE]', nameAemSat),
                        ' </Value>\n'
                    ]
                    for lineAttitude in linesAttitude:
                        newFile.write(startLine+lineAttitude)
            elif '[SAT_COLOR_FILE]' in line:
                lineModified = line.replace('[SAT_COLOR_FILE]', nameColorSat)
                newFile.write(startLine+lineModified)
            elif '[SENSORSAT]' in line:
                # Considering no satellite sensor
                sensorSatBlock(newFile, satellite, folderModels, level+1)
                pass
            else:
                newFile.write(startLine+line)
    
def sensorSatBlock(newFile, satellite, folderModels, level):
    """
    Function that writes lines related to the satellite sensors
    """

    sensorNameSat = 'sensor_' + satellite['name']
    if 'halfAngle' in satellite:
        halfAngleSat = float(satellite['halfAngle'])
    else:
        halfAngleSat = 60. # in deg
    halfAngleSat = str(radians(halfAngleSat))

    startLine = ' '*level
    with open(folderModels+'sensorSatModel.vts') as sensorSatModel:
        for line in sensorSatModel:
            if '[SENSORNAMESAT]' in line:
                lineModified = line.replace('[SENSORNAMESAT]', sensorNameSat)
                newFile.write(startLine+lineModified)
            elif '[HALFANGLESAT]' in line:
                lineModified = line.replace('[HALFANGLESAT]', halfAngleSat)
                newFile.write(startLine+lineModified)
            else:
                newFile.write(startLine+line)

def addFilesBlock(newFile, general, satellites, groundStations, folderData, folderModels, level):
    """
    Function that write lines for files that have to be added to VTS even though they are
    not used by VTS to generate the 3D and 2D views
    """
    
    line = '<File Name="[NAMEFILE]"/>\n'

    startLine = ' '*level
    for sat in satellites:
        for option in general['options']:
            if option not in ('CARTESIAN', 'ATTITUDE'):
                if option == 'VISIBILITY':
                    for gs in groundStations:
                        nameFile = folderData + sat['name'] + '_MEM_VISIBILITY_' + \
                            gs['name'] + '.TXT'
                        lineModified = line.replace('[NAMEFILE]', nameFile)
                        newFile.write(startLine+lineModified)

                else:
                    nameFile = folderData + sat['name'] + '_MEM_' + option + '.TXT'
                    lineModified = line.replace('[NAMEFILE]', nameFile)
                    newFile.write(startLine+lineModified)

def celestiaBlock(newFile, general, satellites, groundStations, folderData, folderModels, level):
    """
    Function that write lines to configurate Celestia (3D visualization)
    """

    startLine = ' '*(level+3)

    if general['celestialBody'].upper() == 'SUN':
        parentPath = 'Sol'
    elif general['celestialBody'].upper() == 'MOON':
        parentPath = 'Sol/Earth/Moon'
    else:
        parentPath = 'Sol/' + general['celestialBody'].lower().capitalize()

    # Geometry of window (in left top corner) and camera
    lines = [
        '<Command Str="CMD PROP WindowGeometry 0 0 800 640"/>\n',
        '<Command Str="CMD PROP CameraDesc ecliptic [PARENTPATH] nil 0.007283254636522 0.001179635528706 0.000231526022466 0.712167126874237 0.198544959469513 -0.667006536346601 0.092196328234123 0.279252678155899"/>\n'
    ]
    for line in lines:
        newFile.write(startLine+line.replace('[PARENTPATH]', parentPath))

    # Show satellite path 1 hour before and after,
    # and remove satellite sensor visaulization
    linesSat = [
        '<Command Str="CMD STRUCT TrackWindow &quot;[PARENTPATH]/[NAMESAT]&quot; 1 1"/>\n',
        '<Command Str="CMD STRUCT AimContourVisible &quot;[PARENTPATH]/[NAMESAT]/[SENSORNAMESAT]&quot; false"/>\n',
        '<Command Str="CMD STRUCT AimVolumeVisible &quot;[PARENTPATH]/[NAMESAT]/[SENSORNAMESAT]&quot; false"/>\n'
    ]
    for line in linesSat:
        for sat in satellites:
            nameSat = sat['name']
            nameSensorSat = 'sensor_' + sat['name']
            lineModified = line.replace('[NAMESAT]', nameSat).replace('[SENSORNAMESAT]', nameSensorSat).replace('[PARENTPATH]', parentPath)
            newFile.write(startLine+lineModified)

def surfaceViewBlock(newFile, general, satellites, groundStations, folderData, folderModels, level):
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

    # Geometry of window (top, on the right of Celestia window)
    line = '<Command Str="CMD PROP WindowGeometry 800 0 800 640"/>\n'
    newFile.write(startLine+line)

    # Show satellite path 1 hour before and after,
    # and remove satellite sensor visaulization
    lineSat = [
        '<Command Str="CMD STRUCT TrackWindow &quot;[PARENTPATH]/[NAMESAT]&quot; 1 1"/>\n',
        '<Command Str="CMD STRUCT AimContourVisible &quot;[PARENTPATH]/[NAMESAT]/[SENSORNAMESAT]&quot; false"/>\n',
        '<Command Str="CMD STRUCT AimTraceVisible &quot;[PARENTPATH]/[NAMESAT]/[SENSORNAMESAT]&quot; false"/>\n'
    ]
    for line in lineSat:
        for sat in satellites:
            nameSat = sat['name']
            nameSensorSat = 'sensor_' + sat['name']
            lineModified = line.replace('[NAMESAT]', nameSat).replace('[SENSORNAMESAT]', nameSensorSat).replace('[PARENTPATH]', parentPath)
            newFile.write(startLine+lineModified)

def findTrueDate(dateString, timeScale, satellites):
    """
    Function that computes the actual used starting date, being the latest between
    the given starting date and the TLE dates
    """

    listTypes = [sat['type'] for sat in satellites]

    isTLE = False
    for sat in satellites:
        typeSat = sat['type']
        if typeSat == 'tle':
            satTLE = TLE(sat['line1'], sat['line2'])
            if isTLE == False:
                latestDate = satTLE.getDate()
                isTLE = True
            else:
                if satTLE.getDate().compareTo(latestDate) > 0:
                    latestDate = satTLE.getDate()
    
    dateStart = latestDate.toString(timeScale) if isTLE else dateString
    return dateStart

class VTSGenerator:
    """
    Class that generates the VTS configuration file for the given mission, using different models
    """

    def __init__(self, nameNewFile, nameModel, folderModels):
        self.nameNewFile =  nameNewFile
        self.nameModel = folderModels + nameModel
        self.folderModels = folderModels

    def generate(self, general, options, satellites, groundStations):
        """
        Generates the file by calling each function in the switcher,
        each function using a .vts model or pre-written lines they represent
        only a few lines
        """

        general['options'] = options
        level = 0
        switcherFile = {
            '[GENERAL]': generalBlock,
            '[TIMELINE]': timeLineBlock,
            '[ENTITIES]': entityBlock,
            '[ADDITIONAL_FILES]': addFilesBlock,
            '[CELESTIA]': celestiaBlock,
            '[SURFACEVIEW]': surfaceViewBlock,
        }
        folderData = 'Data/'

        utc = TimeScalesFactory.getUTC()
        #general['timeStart'] = findTrueDate(general['timeStart'], utc, satellites)
        # 180723 we force JSATORB to ignore de True Start Date as we append the OEMS
        dateStart = AbsoluteDate(general['timeStart'], utc)
        dateEnd = AbsoluteDate(general['timeEnd'], utc)
        if dateEnd.compareTo(dateStart) < 0:
            raise ValueError("End date before start date")

        with open(self.nameNewFile,'w') as newFile, open(self.nameModel,'r') as model:
            read(switcherFile, model, newFile, general, satellites, groundStations, folderData, self.folderModels, level)

if __name__ == "__main__":
    # Test that can be launched by running this file

    options = [
        "CARTESIAN",
        "KEPLERIAN",
        "ATTITUDE",
        "ECLIPSE"
    ]

    general = {
        'timeStart': "2011-12-01T16:43:45",
        'timeEnd': "2011-12-02T16:43:45",
        'celestialBody': 'EARTH'
    }

    groundStations = [
        {"name": "isae",
        "latitude": 43,
        "longitude": 1.5,
        "altitude": 150,
        "elevation": 12
        },
        {"name": "cayenne",
        "latitude": 4.5,
        "longitude": -52.9,
        "altitude": 0,
        "elevation": 12
        }
    ]

    satellites = [
        {"name": "KepSat",
        "type": "keplerian",
        "sma": 7000000,
        "ecc": 0.007014455530245822,
        "inc": 51,
        "pa": 0,
        "raan": 0,
        "meanAnomaly": 0
        },
        {"name": "CartSat",
        "type": "cartesian",
        "x": -6142438.668,
        "y": 3492467.560,
        "z": -25767.25680,
        "vx": 505.8479685,
        "vy": 942.7809215,
        "vz": 7435.922231
        }
    ]

    # Path to new file
    nameNewFile = 'newFile.vts'
    # Folders where models are and name of main model
    folderModels = './'
    nameModel = 'mainModel.vts'

    generator = VTSGenerator(nameNewFile, nameModel, folderModels)
    generator.generate(general, options, satellites, groundStations)





    
