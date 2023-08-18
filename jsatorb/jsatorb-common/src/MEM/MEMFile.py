import orekit
vm = orekit.initVM()

from org.orekit.data import DataContext
from org.orekit.errors import OrekitException, OrekitMessages
from org.orekit.time import AbsoluteDate, TimeScale
from org.orekit.utils import IERSConventions

from MEMMetaData import MEMMetaData

'''
This class stocks all the information of the Mission Ephemeris Message (MEM) file.
The MEM file type allows description of arbitrary time-dependent data.
It contains the header the metadata and a list of arbitrary time-dependent data.

The MEM file follows the CIC-CCSDS format.
'''
class MEMFile:

    def __init__(self):
        self.dataBlocks = []

    def addDataBlock(self):
        self.dataBlocks.append(Datablock(self))

'''
The DataBlock class contains metadata and the list of data lines
''' 
class Datablock:

    def __init__(self, memFile):
        self.dataLines = []
        self.metaData = MEMMetaData(memFile)

    def getTimeScaleString(self):
        return self.metaData.timeSystem.toString()

    def getTimeScale(self):
        return self.metaData.getTimeScale()



