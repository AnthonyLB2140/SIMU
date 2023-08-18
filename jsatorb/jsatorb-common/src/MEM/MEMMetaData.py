import orekit
vm = orekit.initVM()

from org.orekit.files.ccsds import CcsdsTimeScale
from org.orekit.time import TimeScale

from MEMFile import MEMFile

'''
This class gathers the meta-data present in the Mission Ephemeris Message (MEM).

This class gathers the static metadata of the MEM file (i.e. the invariant data).
'''
class MEMMetaData:

    def __init__(self, memFile):
        self.memFile = memFile
        self.comment = []

    def getTimeScale(self):
        return self.timeSystem.getTimeScale(self.memFile.conventions,
            self.memFile.dataContext.getTimeScales())
