from distutils.dir_util import copy_tree
import os
import sys
import io
import zipfile
import pathlib
from bottle import HTTPResponse

#### Give visibility on processing modules called from the REST API
# Add mission analysis module 
sys.path.append('../jsatorb-visibility-service/src')
# Add eclipses module 
sys.path.append('../jsatorb-eclipse-service/src')
# Add Date conversion module 
sys.path.append('../jsatorb-date-conversion/src')
# Add JSatOrb common module: AEM and MEM generators
sys.path.append('../jsatorb-common/src')
sys.path.append('../jsatorb-common/src/AEM')
sys.path.append('../jsatorb-common/src/MEM')
sys.path.append('../jsatorb-common/src/VTS')
# Add file conversion module
sys.path.append('../jsatorb-common/src/file-conversion')
# Add JSatOrb common module: Mission Data management
sys.path.append('../jsatorb-common/src/mission-mgmt')
# Add Constellation generator module
sys.path.append('../jsatorb-common/src/constellation')
# Add Coverage module
sys.path.append('../jsatorb-coverage-service/src')

import bottle
from bottle import request, response
from MissionAnalysis import HAL_MissionAnalysis
from WalkerConstellation import WalkerConstellation
from DateConversion import HAL_DateConversion
from EclipseCalculator import HAL_SatPos, EclipseCalculator
from FileGenerator import FileGenerator
from VTSGenerator import VTSGenerator
from ccsds2cic import ccsds2cic
from MissionDataManager import writeMissionDataFile, loadMissionDataFile, listMissionDataFile, duplicateMissionDataFile, isMissionDataFileExists, deleteMissionDataFile
from CoverageGenerator import CoverageGenerator
from VTSGeneratorCoverage import VTSGeneratorCoverage
from datetime import datetime
import json

app = application = bottle.default_app()

# the decorator
def enable_cors(fn):
    def _enable_cors(*args, **kwargs):
        # set CORS headers
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS, DELETE'
        response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

        if bottle.request.method != 'OPTIONS':
            # actual request; reply with the actual response
            return fn(*args, **kwargs)
    return _enable_cors

# Display received HTTP request on stdout.
def showRequest(req):
    """Display received HTTP request on stdout."""
    print("RECEIVED REQUEST --------------------------------------------------")
    print(req)
    print("END OF RECEIVED REQUEST -------------------------------------------")

# Display sent HTTP response on stdout.
def showResponse(res):
    """Display sent HTTP response on stdout."""
    print("SENT RESPONSE (truncated to 1000 char) ----------------------------")
    print(res[0:1000])
    print("END OF SENT RESPONSE ----------------------------------------------")

# Convert a boolean to a REST status value {"SUCCESS, "FAIL"}.
def boolToRESTStatus(value):
    """Convert a boolean to a REST status value {"SUCCESS, "FAIL"}."""
    if (value == True):
        return "SUCCESS"
    else:
        return "FAIL"

# Build a formatted REST response (SMD= Status, Message, Data) as a dictionary.
def buildSMDResponse(status, message, data):
    """
    Build a formatted REST response as a dictionary: 
    {"status": <operation status: "SUCCESS" or "FAIL">, "message": <error message if "FAIL" is returned>, "data": <response data>}
    """

    return {"status": status, "message": message, "data": data}

# -----------------------------------------------------------------------------
# MODULE        : jsatorb-visibility-service
# ROUTE         : /propagation/satellites
# METHOD        : POST
# FUNCTIONNALITY: Ephemerids processing 
# -----------------------------------------------------------------------------
@app.route('/propagation/satellites', method=['OPTIONS','POST'])
@enable_cors
def satelliteJSON():
    response.content_type = 'application/json'
    data = request.json
    showRequest(json.dumps(data))

    header = data['header']
    satellites = data['satellites']
    step = header['step']
    endDate = header['timeEnd']

    # Assign default value ('EARTH') if celestial body is undefined.
    if 'celestialBody' in header:
        celestialBody=header['celestialBody']
    else:
        celestialBody = 'EARTH'
        
    newMission = HAL_MissionAnalysis(step, endDate, celestialBody)    

    if 'timeStart' in header:
        newMission.setStartTime(header['timeStart'])

    for sat in satellites:
        newMission.addSatellite(sat)

    newMission.propagate()

    res = json.dumps(newMission.getJSONEphemerids())
    showResponse(res)
    return res

# -----------------------------------------------------------------------------
# MODULE        : jsatorb-visibility-service
# ROUTE         : /propagation/visibility
# METHOD        : POST
# FUNCTIONNALITY: Visibility processing
# -----------------------------------------------------------------------------
@app.route('/propagation/visibility', method=['OPTIONS', 'POST'])
@enable_cors
def satelliteOEM():
    response.content_type = 'application/json'
    data = request.json
    showRequest(json.dumps(data))

    header = data['header']
    satellites = data['satellites']
    groundStations = data['groundStations']
    step = header['step']
    endDate = header['timeEnd']

    # Assign default value ('EARTH') if celestial body is undefined.
    if 'celestialBody' in header:
        celestialBody=header['celestialBody']
    else:
        celestialBody = 'EARTH'
        
    newMission = HAL_MissionAnalysis(step, endDate, celestialBody)    
    if 'timeStart' in header:
        newMission.setStartTime(header['timeStart'])

    for sat in  satellites:
        newMission.addSatellite(sat)

    for gs in groundStations:
        newMission.addGroundStation(gs)

    newMission.propagate()

    res = json.dumps(newMission.getVisibility())
    showResponse(res)
    return res

# -----------------------------------------------------------------------------
# MODULE        : jsatorb-eclipse-service
# ROUTE         : /propagation/eclipses
# METHOD        : POST
# FUNCTIONNALITY: Eclipse processing
# -----------------------------------------------------------------------------
@app.route('/propagation/eclipses', method=['OPTIONS','POST'])
@enable_cors
def EclipseCalculatorREST():
    response.content_type = 'application/json'
    
    data = request.json
    showRequest(json.dumps(data))
    
    stringDateFormat = '%Y-%m-%dT%H:%M:%S'

    try:
        header = data['header']
        sat = data['satellite']

        stringDate = str( header['timeStart'] )
        stringDateEnd = str( header['timeEnd'] )

        typeSat = str( sat['type'] )
        if 'keplerian' in typeSat:
            sma = float( sat['sma'] )
            if sma < 6371000:
                res = ValueError('bad sma value')
            else:
                ecc = float( sat['ecc'] )
                inc = float( sat['inc'] )
                pa = float( sat['pa'] )
                raan = float( sat['raan'] )
                lv = float( sat['meanAnomaly'] )
                calculator = EclipseCalculator(HAL_SatPos(sma, ecc, inc, pa, raan, lv, 'keplerian'),
                    datetime.strptime(stringDate, stringDateFormat), datetime.strptime(stringDateEnd, stringDateFormat))
                res = eclipseToJSON( calculator.getEclipse() )

        elif 'cartesian' in typeSat:
            x = float( sat['x'] )
            y = float( sat['y'] )
            z = float( sat['z'] )
            vx = float( sat['vx'] )
            vy = float( sat['vy'] )
            vz = float( sat['vz'] )
            calculator = EclipseCalculator(HAL_SatPos(x, y, z, vx, vy, vz, 'cartesian'), 
                datetime.strptime(stringDate, stringDateFormat), datetime.strptime(stringDateEnd, stringDateFormat))
            res = eclipseToJSON( calculator.getEclipse() )

        else:
            res = error('bad type')

    except Exception as e:
        res = error(type(e).__name__ + str(e.args))

    showResponse(res)
    return res


def error(errorName):
    return '{"error": "' + errorName + '"}'

def eclipseToJSON(eclipse):
    eclipseDictionary = []

    for el in eclipse:
        obj = {}
        obj['start'] = el[0].toString()
        obj['end'] = el[1].toString()
        eclipseDictionary.append(obj)

    return json.dumps(eclipseDictionary)

# -----------------------------------------------------------------------------
# MODULE        : jsatorb-date-conversion
# ROUTE         : /dateconversion
# FUNCTIONNALITY: Date conversion from ISO-8601 to JD and MJD
# -----------------------------------------------------------------------------
@app.route('/dateconversion', method=['OPTIONS', 'POST'])
@enable_cors
def DateConversionREST():
    response.content_type = 'application/json'

    data = request.json
    showRequest(json.dumps(data))

    try:
        header = data['header']
        dateToConvert = header['dateToConvert']
        targetFormat = header['targetFormat']

        newDate = HAL_DateConversion(dateToConvert, targetFormat)

        # Return json with converted date in 'dateConverted'

        result = newDate.getDateTime()
        errorMessage = ''
    except Exception as e:
        result = None
        errorMessage = str(e)

    res = json.dumps(buildSMDResponse(boolToRESTStatus(result!=None), errorMessage, result))
    showResponse(res)
    return res

# -----------------------------------------------------------------------------
# MODULE        : jsatorb-constellation-generator
# ROUTE         : /constellationgenerator
# FUNCTIONNALITY: Generates a satelittes constellation, according to a set
#                 of parameters.
# -----------------------------------------------------------------------------
@app.route('/constellationgenerator', method=['OPTIONS', 'POST'])
@enable_cors
def ConstellationGeneratorREST():
    response.content_type = 'application/json'

    data = request.json
    showRequest(json.dumps(data))

    try:
        header = data['header']

        # Give directly the header part of the request, as the arguments/parameter
        # names are the same that the one expected in the constellation generator.
        generator = WalkerConstellation(header)

        # The generator returned data can be directly put into the JSON data part of the HTTP response.
        result = generator.generate()

        errorMessage = ''
    except Exception as e:
        result = None
        errorMessage = str(e)

    res = json.dumps(buildSMDResponse(boolToRESTStatus(result!=None), errorMessage, result))
    showResponse(res)
    return res

# -----------------------------------------------------------------------------------------
# VTS ZIP FILE BLOB RESPONSE HELPER FUNCTIONS
# -----------------------------------------------------------------------------------------

def getListOfFiles(dirName):
    """
    For the given path, get the List of all files in the directory tree (recursively)

    Parameters:
        dirName The folder to list the files of.
    Returns
        The list of files beginning with the same path given by dirName.
    """
    # create a list of file and sub directories 
    # names in the given directory 
    listOfFile = os.listdir(dirName)
    allFiles = list()
    # Iterate over all the entries
    for entry in listOfFile:
        # Create full path
        fullPath = os.path.join(dirName, entry)
        # If entry is a directory then get the list of files in this directory 
        if os.path.isdir(fullPath):
            allFiles = allFiles + getListOfFiles(fullPath)
        else:
            allFiles.append(fullPath)
                
    return allFiles

def zipped_vts_response(vts_folder, mission):
    """
    Create an HTTP response containing the VTS compressed data structure in its body

    Parameters:
        vts_folder The folder which content has to be compressed and encapsulated into an http response.
        mission The mission name used to give a name to the zip attachment content.
    Returns:
        The HTTP Response containg the VTS compressed content, or None if zipRoot is not child of vts_folder
    """

    buf = io.BytesIO()
    # Get the list of all files in directory tree at given path
    listOfFiles = getListOfFiles(vts_folder)

    with zipfile.ZipFile(buf, 'w') as zipfh:
        for individualFile in listOfFiles:
            fileSegments = individualFile.split('/')
            fileSegmentsTruncated = fileSegments[1:]
            fileFinalFilename = '/'.join(fileSegmentsTruncated)
            dt = datetime.now()
            timeinfo = (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
            info = zipfile.ZipInfo(fileFinalFilename, timeinfo)
            info.compress_type = zipfile.ZIP_DEFLATED
            with open(individualFile, 'rb') as content_file:
                content = content_file.read()
                zipfh.writestr(info, content)
    buf.seek(0)

    filename = 'vts-' + mission + '-content.vz'

    r = HTTPResponse(status=200, body=buf)
    # Set theJSatOrb custom content type (to force the JSatorb GUI Web browser to ask which application to use to manage the received data).
    r.set_header('Content-Type', 'application/vnd+cssi.vtsproject+zip') 
    # Give the recommended filename for the received data (and give the mission name in it, as the filename structure is: vts-<mission-name>-content.vz).
    r.set_header('Content-Disposition', "attachment; filename='" + filename + "'")
    # Expose the ContentDisposition header item (hence the recommended filename).
    r.set_header('Access-Control-Expose-Headers', 'Content-Disposition')
    # Do not restrict the request origin.
    r.set_header('Access-Control-Allow-Origin', '*')
    #New header by EAE to warn nodered that VTS should be restarted
    r.set_header('vtsFlag', 'ready') 
    print(r)
    
    
    return r

# -----------------------------------------------------------------------------------------
# END OF VTS ZIP FILE BLOB RESPONSE HELPER FUNCTIONS
# -----------------------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# MODULE        : jsatorb-file-generation
# ROUTE         : /propagation/eclipses
# METHOD        : POST
# FUNCTIONNALITY: Eclipse processing
# -----------------------------------------------------------------------------
@app.route('/vts', method=['OPTIONS', 'POST'])
@enable_cors
def FileGenerationREST():
    #response.content_type = 'application/json'
    data = request.json
    showRequest(json.dumps(data))
  #  print(data)
    try:
        header = data['header']
        print(header)
        satellites = data['satellites']
        groundStations = data['groundStations']
        options = data['options']
        
        if 'celestialBody' not in header: header['celestialBody'] = 'EARTH'
        celestialBody = str( header['celestialBody'] )

        if 'mission' not in header: header['mission'] = 'default_' + satellites[0]['name']

        if "COVERAGE" in options:
            optionsCoverage = options["COVERAGE"]

            projectFolder = 'files/' + header['mission'] + '_coverage/'
            dataFolder = projectFolder + 'Data/'
            modelFolder = projectFolder + 'Models/'
            if not os.path.isdir(projectFolder):
                os.mkdir(projectFolder)
                os.mkdir(dataFolder)
            elif not os.path.isdir(dataFolder):
                os.mkdir(dataFolder)
            copy_tree('files/Models', modelFolder)

            covGen = CoverageGenerator(celestialBody, satellites)
            covGen.compute(optionsCoverage)
            covGen.saveTypeData(modelFolder)

            nameVtsFile = projectFolder + '/' + header['mission'] + '_coverage.vts'
            vtsGenerator = VTSGeneratorCoverage(nameVtsFile, 'mainModelCoverage.vts', '../jsatorb-coverage-service/src/')
            vtsGenerator.generate(header, options, groundStations)

        else:
            step = float( header['step'] )
            startDate = str( header['timeStart'] )
            endDate = str( header['timeEnd'] )
            print("startDate")
            print(startDate)
            projectFolder = 'files/' + header['mission'] + '/'
            dataFolder = projectFolder + 'Data/'
            if not os.path.isdir(projectFolder):
                os.mkdir(projectFolder)
                os.mkdir(dataFolder)
            elif not os.path.isdir(dataFolder):
                os.mkdir(dataFolder)
            copy_tree('files/Models', projectFolder+'Models')

            fileGenerator = FileGenerator(startDate, endDate, step, celestialBody, satellites, groundStations, options)
            fileGenerator.generate(dataFolder)
            header['timeStart'] = startDate # 180723 Trying to force the start date in config 
            nameVtsFile = projectFolder + '/' + header['mission'] + '.vts'
            vtsGenerator = VTSGenerator(nameVtsFile, 'mainModel.vts', '../jsatorb-common/src/VTS/')
            vtsGenerator.generate(header, options, satellites, groundStations)
            
            print("No Coverage")
            print(header)
            
        result = ""
        errorMessage = 'Files generated'

        # Success response
        res = zipped_vts_response(projectFolder, header['mission'])
        if (not res == None):
            print('Returning compressed VTS data structure as Response')
        else:
            result = "FAIL"
            message = "REST API internal error while creating the VTS archive !"

            res = json.dumps(buildSMDResponse(boolToRESTStatus(result!=None), errorMessage, result))            
            showResponse(res)

    except Exception as e:
        result = None
        errorMessage = str(e)

        # Error response
        print('An error occured while producing the compressed VTS data structure !')
        res = json.dumps(buildSMDResponse(boolToRESTStatus(result!=None), errorMessage, result))
        showResponse(res)

    return res

# -----------------------------------------------------------------------------
# MODULE        : jsatorb-common
# ROUTE         : /missiondata/<missionName>
# METHOD        : POST
# FUNCTIONNALITY: Store mission data into a file
# -----------------------------------------------------------------------------
@app.route('/missiondata/<missionName>', method=['OPTIONS', 'POST'])
@enable_cors
def MissionDataStoreREST(missionName):
    response.content_type = 'application/json'
    data = request.json
    showRequest(json.dumps(data))

    result = writeMissionDataFile(data, missionName)

    # Return a JSON formatted response containing the REST operation result: status, message and data.
    res = json.dumps(buildSMDResponse(boolToRESTStatus(result[0]), result[1], ""))
    showResponse(res)
    return res

# -----------------------------------------------------------------------------
# MODULE        : jsatorb-common
# ROUTE         : /missiondata/<missionName>
# METHOD        : GET
# FUNCTIONNALITY: Load mission data previously stored
# -----------------------------------------------------------------------------
@app.route('/missiondata/<missionName>', method=['OPTIONS', 'GET'])
@enable_cors
def MissionDataLoadREST(missionName):
    response.content_type = 'application/json'
    data = request.json
    showRequest(json.dumps(data))

    result = loadMissionDataFile(missionName)

    # Return a JSON formatted response containing the REST operation result: status, message and data.
    res = json.dumps(buildSMDResponse(boolToRESTStatus(not result[0]==None), result[1], result[0]))
    showResponse(res)
    return res

# -----------------------------------------------------------------------------
# MODULE        : jsatorb-common
# ROUTE         : /missiondata/list
# METHOD        : GET
# FUNCTIONNALITY: Get a list of mission data previously stored
# -----------------------------------------------------------------------------
@app.route('/missiondata/list', method=['OPTIONS', 'GET'])
@enable_cors
def MissionDataListREST():
    response.content_type = 'application/json'
    data = request.json
    showRequest(json.dumps(data))

    result = listMissionDataFile()

    # Return a JSON formatted response containing the REST operation result: status, message and data.
    res = json.dumps(buildSMDResponse("SUCCESS", "List of available mission data sets", result))
    showResponse(res)
    return res

# -----------------------------------------------------------------------------
# MODULE        : jsatorb-common
# ROUTE         : /missiondata/duplicate
# METHOD        : POST
# FUNCTIONNALITY: Duplicate mission data to another mission file
# -----------------------------------------------------------------------------
@app.route('/missiondata/duplicate', method=['OPTIONS', 'POST'])
@enable_cors
def MissionDataDuplicateREST():
    response.content_type = 'application/json'
    data = request.json
    showRequest(json.dumps(data))

    header = data['header']
    srcMissionName = header['srcMission']
    destMissionName = header['destMission']

    result = duplicateMissionDataFile(srcMissionName, destMissionName)

    # Return a JSON formatted response containing the REST operation result: status, message and data.
    res = json.dumps(buildSMDResponse(boolToRESTStatus(result[0]), result[1], ""))
    showResponse(res)
    return res

# -----------------------------------------------------------------------------
# MODULE        : jsatorb-common
# ROUTE         : /missiondata/check/<missionName>
# METHOD        : GET
# FUNCTIONNALITY: Check if a mission data file exists
# -----------------------------------------------------------------------------
@app.route('/missiondata/check/<missionName>', method=['OPTIONS', 'GET'])
@enable_cors
def CheckMissionDataREST(missionName):
    response.content_type = 'application/json'
    data = request.json
    showRequest(json.dumps(data))

    result = isMissionDataFileExists(missionName)

    # Return a JSON formatted response containing the REST operation result: status, message and data.
    res = json.dumps(buildSMDResponse("SUCCESS", "Check if a mission data set exists", result))
    showResponse(res)
    return res

# -----------------------------------------------------------------------------
# MODULE        : jsatorb-common
# ROUTE         : /missiondata/<missionName>
# METHOD        : DELETE
# FUNCTIONNALITY: Delete a mission data file
# -----------------------------------------------------------------------------
@app.route('/missiondata/<missionName>', method=['OPTIONS', 'DELETE'])
@enable_cors
def DeleteMissionDataREST(missionName):
    response.content_type = 'application/json'
    data = request.json
    showRequest(json.dumps(data))

    result = deleteMissionDataFile(missionName)

    # Return a JSON formatted response containing the REST operation result: status, message and data.
    res = json.dumps(buildSMDResponse(boolToRESTStatus(result[0]), result[1], ""))
    showResponse(res)
    return res


if __name__ == '__main__':
    bottle.run(host = '0.0.0.0', port = 8000)
