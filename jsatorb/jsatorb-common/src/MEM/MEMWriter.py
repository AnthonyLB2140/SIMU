import orekit
vm = orekit.initVM()

from org.orekit.bodies import OneAxisEllipsoid
from org.orekit.errors import OrekitIllegalArgumentException, OrekitMessages
from org.orekit.time import TimeScale

from collections import OrderedDict 

from MEMFile import MEMFile, Datablock
from StreamingMemWriter import StreamingMemWriter
from MEMKeyword import MEMKeyword

# A writer for Mission Ephemeris Message (MEM) files, currently not used in JSatOrb
class MEMWriter:

    # Constructor used to create a new MEM writer configured with the necessary
    # parameters to successfully fill in all required fields that aren't part
    # of a standard object.
    def __init__(self, originator, spaceObjectId, spaceObjectName, body):
        self.originator = originator
        self.spaceObjectId = spaceObjectId
        self.spaceObjectName = spaceObjectName
        # Expected OneAxisEllipsoid body
        self.body = body

    # Standard default constructor that creates a writer with default configurations.
    # Default values are:
    # originator = StreamingMemWriter.DEFAULT_ORIGINATOR
    # paceObjectId = StreamingMemWriter.DEFAULT_ORIGINATOR
    # spaceObjectName = StreamingMemWriter.DEFAULT_ORIGINATOR
    @classmethod
    def initFromBody(cls, body):
        originator = StreamingMemWriter.DEFAULT_ORIGINATOR
        spaceObjectId = StreamingMemWriter.DEFAULT_SATELLITE
        spaceObjectName = StreamingMemWriter.DEFAULT_SATELLITE
        return cls(originator, spaceObjectId, spaceObjectName, body)

    # Write the passed in {@link MEMFile} to a file at the output path specified.
    def writePath(self, outputFilePath, memFile):
        with open(outputFilePath, 'w') as writer:
            self.write(writer, memFile)
    
    # Write the passed in {@link MEMFile} using the passed in {@link Appendable}.
    def write(self, writer, memFile):
        if memFile == None:
            return
        
        # List of data blocks
        segments = memFile.dataBlocks
        if len(segments) == 0:
            return

        # First segment
        firstSegment = segments[0]
        objectName = self.spaceObjectName
        timeScale = firstSegment.getTimeScale()
        # Metadata that are constants for the whole MEM file
        metadata = OrderedDict()
        metadata[MEMKeyword.TIME_SYSTEM] = firstSegment.getTimeScaleString()
        metadata[MEMKeyword.ORIGINATOR] = self.originator
        metadata[MEMKeyword.OBJECT_NAME] = objectName
        metadata[MEMKeyword.OBJECT_ID] = self.spaceObjectId

        # Writer for MEM files
        memWriter = StreamingMemWriter(writer, timeScale, metadata, self.body)
        memWriter.writeHeader()

        # Loop on segments
        for segment in segments:
            # Segment specific metadata (only the required ones)
            metadata.clear()
            metadata[MEMKeyword.USER_DEFINED_PROTOCOL] = segment.userDefinedProtocol
            metadata[MEMKeyword.USER_DEFINED_CONTENT] = segment.userDefinedContent

            # Write metadata
            memWriter.writeMetadata(metadata)
            # Loop on attitude data
            for data in segment.dataLines:
                memWriter.writeDataLine(data)
    
