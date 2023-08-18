import orekit
vm = orekit.initVM()

from orekit.pyhelpers import setup_orekit_curdir
setup_orekit_curdir()

from org.orekit.propagation.analytical.tle import TLE
from org.orekit.time import AbsoluteDate, TimeScalesFactory

import os
import sys

sys.path.append('../AEM')
sys.path.append('../MEM')
sys.path.append('../file-conversion')
sys.path.append('../../jsatorb-visibility-service/src')
from AEMGenerator import AEMGenerator
from MEMGenerator import MEMGenerator
from ColorGenerator import ColorGenerator
from MissionAnalysis import HAL_MissionAnalysis
from ccsds2cic import ccsds2cic

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
    if isTLE:
        print("Considered start date: {}".format(dateStart))
    return dateStart

class FileGenerator:
    """ Master class that calls MissionAnalysis.py, MEMGenerator.py, and AEMGenerator.py,
    to generate OEM, AEM, and MEM files for given satellites, time options, and central body.
    It also generates a color file for VTS"""

    def __init__(self, stringDateStart, stringDateEnd, step, stringBody, satellites, groundStations, options):
        self.step = step
        self.body = stringBody
        self.satellites = satellites
        self.groundStations = groundStations
        self.options = options

        utc = TimeScalesFactory.getUTC()
        self.dateStart = findTrueDate(stringDateStart, utc, satellites)
        self.dateEnd = stringDateEnd

        dateStartTest = AbsoluteDate(self.dateStart, utc)
        dateEndTest = AbsoluteDate(self.dateEnd, utc)
        if dateEndTest.compareTo(dateStartTest) < 0:
            raise ValueError("End date before start date")
        
    def generate(self, nameFolder):
        # One file minimum per satellite
        for sat in self.satellites:
            optionsCur = dict(self.options)
            # OEM
            if 'CARTESIAN' in optionsCur:
                nameFileOemCcsds = nameFolder + sat['name'] + '_OEM_POSITION.TXT_ccsds'
                nameFileOem = nameFolder + sat['name'] + '_OEM_POSITION.TXT'
                newMission = HAL_MissionAnalysis(self.step, self.dateEnd, self.body)
                newMission.setStartTime(self.dateStart)
                newMission.addSatellite(sat)
                newMission.propagate()
                with open(nameFileOemCcsds,'w') as file:
                    file.write(newMission.getOEMEphemerids())
                ccsds2cic(nameFileOemCcsds, nameFileOem, self.body)

                del optionsCur['CARTESIAN']
                os.remove(nameFileOemCcsds)

            # AEM
            if 'ATTITUDE' in optionsCur:
                nameFileAemCcsds = nameFolder + sat['name'] + '_AEM_ATTITUDE.TXT_ccsds'
                nameFileAem = nameFolder + sat['name'] + '_AEM_ATTITUDE.TXT'

                aemGenerator = AEMGenerator(self.dateStart, self.step, self.dateEnd, self.body)
                aemGenerator.setSatellite(sat)
                aemGenerator.setFile(nameFileAemCcsds)
                aemGenerator.setAttitudeLaw(optionsCur['ATTITUDE'])
                aemGenerator.propagate()
                ccsds2cic(nameFileAemCcsds, nameFileAem, self.body)

                del optionsCur['ATTITUDE']
                os.remove(nameFileAemCcsds)

            # MEM
            memGenerator = MEMGenerator(self.dateStart, self.step, self.dateEnd, self.body)
            memGenerator.setSatellite(sat)            
            for memType in optionsCur:
                if memType == 'VISIBILITY':
                    for gs in self.groundStations:
                        memGenerator.addMemVisibility(nameFolder + sat['name'] + '_MEM_VISIBILITY_' + gs['name'] + '.TXT', gs)
                else:
                    memGenerator.addMemType(memType, nameFolder + sat['name'] + '_MEM_' + memType + '.TXT')

            memGenerator.propagate()
            
            # Color, unique or changing through the orbit depending on visibility
            nameFileColor = nameFolder + sat['name'] + '_COLOR.TXT'
            colorGenerator = ColorGenerator(self.dateStart, nameFileColor, sat)
            colorGenerator.generate()

            if 'VISIBILITY' in self.options:
                listVisibilities = []
                for gs in self.groundStations:
                    listVisibilities.append(nameFolder+sat['name']+'_MEM_VISIBILITY_'+gs['name']+'.TXT')
                colorGenerator.addVisibilities(listVisibilities)

            
            