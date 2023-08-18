import orekit
vm = orekit.initVM()

from orekit.pyhelpers import setup_orekit_curdir
setup_orekit_curdir()

from org.orekit.propagation.analytical.tle import TLE
from org.orekit.time import AbsoluteDate, TimeScalesFactory

import numpy as np
import sys
sys.path.append('../jsatorb-common/src')
from ListCelestialBodies import ListCelestialBodies

from CoverageAnalysis import CoverageAnalysis

#from time import time

def findTrueDate(dateString, timeScale, satellites):
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

class CoverageGenerator:
    """ Class that reads the coverage options and calls CoverageAnalysis.py to compute 
    coverage for each satellite """
    def __init__(self, strBody, satellites):
        self.body = strBody
        self.satellites = satellites
        
    def compute(self, optionsCoverage):
        utc = TimeScalesFactory.getUTC()
        timeStep = float( optionsCoverage['step'] )
        timeStart = findTrueDate(optionsCoverage["timeStart"], utc, self.satellites)
        timeEnd = optionsCoverage["timeEnd"]
        minElev = float( optionsCoverage["elevation"] )
        nbNeededSats = int( optionsCoverage["nbSatsToCover"] )

        # If not defined, the whole surface is considered
        if "regionLatitudes" in optionsCoverage:
            minLat, maxLat = optionsCoverage["regionLatitudes"]
        else:
            minLat, maxLat = [-90., 90.]
        if "regionLongitudes" in optionsCoverage:
            minLong, maxLong = optionsCoverage["regionLongitudes"]
        else:
            minLong, maxLong = [-180., 180.]

        limitsZone = [np.floor(minLat), np.ceil(maxLat), np.floor(minLong), np.ceil(maxLong)]
        nbLat = int( np.ceil(maxLat) - np.floor(minLat) )
        nbLong = int( np.ceil(maxLong) - np.floor(minLong) )

        self.plotType = optionsCoverage["plotType"]

        self.coverageAnalysis = CoverageAnalysis(timeStart, timeEnd, timeStep, minElev, nbNeededSats)
        self.coverageAnalysis.setBody(self.body)
        self.coverageAnalysis.setLimitZone(limitsZone, nbLat, nbLong)
        for sat in self.satellites:
            print("Satellite: {}".format(sat['name']))
            self.coverageAnalysis.propagate(sat)
    
    def getTypeData(self):
        return self.coverageAnalysis.getTypeData(self.plotType)

    def saveTypeData(self, pathFile):
        return self.coverageAnalysis.saveTypeData(self.plotType, pathFile)

if __name__ == "__main__":
    # Example

    header = {
        "mission": "test-VTS",
        "celestialBody": "EARTH",
        "timeStart": "2011-12-01T16:43:45",
        "timeEnd": "2011-12-02T16:43:45",
        "step": "10"
    }
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
    groundStations = [
        {"name": "sydney",
        "latitude": -33.8678500,
        "longitude": 151.2073200,
        "altitude": 58,
        "elevation": 12
        }
    ]
    optionsCov = {
        "timeStart": "2011-12-01T16:43:45",
        #"timeEnd": "2011-12-02T16:43:45",
        "timeEnd": "2011-12-02T00:00:00",
        "step": 600,
        "elevation": 0,
        "nbSatsToCover": 1,
        #"regionLatitudes": [-90, 90],
        #"regionLongitudes": [-180, 180],
        "regionLatitudes": [-70, 30],
        "regionLongitudes": [-40, 100],
        "plotType": "MEAN_RESP_TIME" #"PERCENT_COV"
    }
    
    covGen = CoverageGenerator(header['celestialBody'], satellites)

    #timeStart = time()
    covGen.compute(optionsCov)
    #timeEnd = time()
    #print("Computation time: {} s".format(timeEnd-timeStart))
    data = covGen.getTypeData()
    covGen.saveTypeData('test')
    print(np.min(data), np.max(data), np.mean(data))
    '''
    optionsCov["plotType"] = "MEAN_GAP"
    result = covGen.getTypeData(optionsCov)
    print(result.shape)
    print(result[0,:])

    optionsCov["plotType"] = "MEAN_RESP_TIME"
    result = covGen.getTypeData(optionsCov)
    print(result.shape)
    print(result[0,:])'''
