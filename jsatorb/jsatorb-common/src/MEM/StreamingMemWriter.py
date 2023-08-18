import orekit
vm = orekit.initVM()

from org.hipparchus.exception import LocalizedCoreFormats
from org.hipparchus.ode.events import Action
from org.hipparchus.util import FastMath

from org.orekit.bodies import GeodeticPoint, OneAxisEllipsoid
from org.orekit.errors import OrekitException
from org.orekit.orbits import KeplerianOrbit, OrbitType
from org.orekit.propagation import SpacecraftState
from org.orekit.propagation.events import EclipseDetector, ElevationDetector
from org.orekit.propagation.events.handlers import EventHandler, PythonEventHandler
from org.orekit.propagation.sampling import OrekitFixedStepHandler, PythonOrekitFixedStepHandler
from org.orekit.time import AbsoluteDate, DateComponents, DateTimeComponents, TimeComponents, TimeScale

from collections import OrderedDict 
from datetime import datetime
#import pytz   

from MEMKeyword import MEMKeyword 
from TimeStampedMEMData import TimeStampedMEMData     
from PredefinedUserContent import PredefinedUserContent                                                                                                                                    

def conversion(string):
    # If string is float, return string with US separators
    # If not, return string
    try:
        return "{:,}".format(float(string))
    except ValueError:
        return string

'''
 A writer for MEM files.
 
Each instance corresponds to a single MEM file.
 
Metadata

The MEM metadata used by this writer is described in the following table. Many
metadata items are optional or have default values so they do not need to be specified.
At a minimum the user must supply those values that are required and for which no
default exits: {@link MEMKeyword#OBJECT_NAME}, and {@link MEMKeyword#OBJECT_ID}. The usage
column in the table indicates where the metadata item is used, either in the MEM header
or in the metadata section at the start of an MEM data.

The MEM metadata for the whole MEM file is set in the {@link
#StreamingMemWriter(Appendable, TimeScale, Map) constructor}.

<table summary="MEM metadata">
    <thead>
        <tr>
            <th>Keyword
            <th>Usage
            <th>Obligatory
            <th>Default
            <th>Reference
    </thead>
    <tbody>
        <tr>
            <td>CIC_MEM_VERS
            <td>Header
            <td>Yes
            <td>{@link #CIC_MEM_VERS}
            <td>Section 4.3.1
        <tr>
            <td>COMMENT
            <td>Header
            <td>No
            <td>
            <td>Section 4.3.1
        <tr>
            <td>CREATION_DATE
            <td>Header
            <td>Yes
            <td>
            <td>Section 4.3.1
        <tr>
            <td>ORIGINATOR
            <td>Header
            <td>Yes
            <td>{@link #DEFAULT_ORIGINATOR}
            <td>Section 4.3.1
        <tr>
            <td>OBJECT_NAME
            <td>Metadata
            <td>Yes
            <td>
            <td>Section 4.3.2
        <tr>
            <td>OBJECT_ID
            <td>Metadata
            <td>Yes
            <td>
            <td>Section 4.3.2
        <tr>
            <td>TIME_SYSTEM
            <td>Metadata
            <td>Yes
            <td>
            <td>Section 4.3.2
        <tr>
            <td>USER_DEFINED_PROTOCOL
            <td>Metadata
            <td>Yes
            <td>
            <td>Section 4.3.2
        <tr>
            <td>USER_DEFINED_CONTENT
            <td>Metadata
            <td>Yes
            <td>
            <td>Section 4.3.2
        <tr>
            <td>USER_DEFINED_SIZE
            <td>Metadata
            <td>No
            <td>
            <td>Section 4.3.2
        <tr>
            <td>USER_DEFINED_TYPE
            <td>Metadata
            <td>No
            <td>
            <td>Section 4.3.2
        <tr>
            <td>USER_DEFINED_UNIT
            <td>Metadata
            <td>No
            <td>
            <td>Section 4.3.2
    </tbody>
</table>

The {@link MEMKeyword#TIME_SYSTEM} must be constant for the whole file and is used
to interpret all dates except {@link MEMKeyword#CREATION_DATE}. </p>

Standardized values for {@link MEMKeyword#TIME_SYSTEM} are GMST, GPS, MET, MRT, SCLK,
TAI, TCB, TDB, TT, UT1, and UTC.
'''
class StreamingMemWriter:

    # Version number implemented
    CIC_MEM_VERS = "1.0"

    # Default value for {@link MEMKeyword#ORIGINATOR}
    DEFAULT_ORIGINATOR = "ISAE"

    # Default value for {@link MEMKeyword#OBJECT_NAME} and {@link MEMKeyword#OBJECT_ID}.
    DEFAULT_SATELLITE = "ISAE-Sat"

    # New line separator for output file.
    NEW_LINE = "\n"

    # Factor for converting meters to km.
    M_TO_KM = 1e-3

    # Space separator.
    SPACE = " "

    # Standardized locale to use, to ensure files can be exchanged without internationalization issues.
    #STANDARDIZED_LOCALE = Locale.US

    # String format used for all key/value pair lines.
    KV_FORMAT = "{} = {}\n" #"%s = %s%n"

    # Create an AEM writer that streams data to the given output stream.
    def __init__(self, writer, timeScale, metadata, body):
        self.writer = writer
        self.timeScale = timeScale
        self.body = body
        self.metadata = OrderedDict(metadata)

        # Set default metadata
        if MEMKeyword.CIC_MEM_VERS not in self.metadata:
            self.metadata[MEMKeyword.CIC_MEM_VERS] = self.CIC_MEM_VERS

        # Creation date is informational only
        if MEMKeyword.CREATION_DATE not in self.metadata:
            #self.metadata[MEMKeyword.CREATION_DATE] = datetime.now(pytz.utc).isoformat()
            self.metadata[MEMKeyword.CREATION_DATE] = datetime.utcnow().isoformat()
        if MEMKeyword.ORIGINATOR not in self.metadata:
            self.metadata[MEMKeyword.ORIGINATOR] = self.DEFAULT_ORIGINATOR
        if MEMKeyword.TIME_SYSTEM not in self.metadata:
            self.metadata[MEMKeyword.TIME_SYSTEM] = timeScale.getName()

    # Write the standard MEM header for the file.
    def writeHeader(self):
        self.writeKeyValue(MEMKeyword.CIC_MEM_VERS, self.metadata[MEMKeyword.CIC_MEM_VERS])
        if MEMKeyword.COMMENT in self.metadata:
            self.writeKeyValue(MEMKeyword.COMMENT, self.metadata[MEMKeyword.COMMENT])
        self.writeKeyValue(MEMKeyword.CREATION_DATE, self.metadata[MEMKeyword.CREATION_DATE])
        self.writeKeyValue(MEMKeyword.ORIGINATOR, self.metadata[MEMKeyword.ORIGINATOR])
        self.writer.write(self.NEW_LINE)

    # Write the MEM segment metadata
    def writeMetadata(self, data):
        self.writer.write("META_START")
        self.writer.write(self.NEW_LINE)

        # Section 4.3.2 - Mandatory keys
        self.writeKeyValue(MEMKeyword.OBJECT_NAME, data[MEMKeyword.OBJECT_NAME])
        self.writeKeyValue(MEMKeyword.OBJECT_ID, data[MEMKeyword.OBJECT_ID])
        self.writeKeyValue(MEMKeyword.USER_DEFINED_PROTOCOL, data[MEMKeyword.USER_DEFINED_PROTOCOL])
        self.writeKeyValue(MEMKeyword.USER_DEFINED_CONTENT, data[MEMKeyword.USER_DEFINED_CONTENT])

        # Section 4.3.2 - Optional keys
        if MEMKeyword.USER_DEFINED_SIZE in data:
            self.writeKeyValue(MEMKeyword.USER_DEFINED_SIZE, str(data[MEMKeyword.USER_DEFINED_SIZE]))
        if MEMKeyword.USER_DEFINED_TYPE in data:
            self.writeKeyValue(MEMKeyword.USER_DEFINED_TYPE, data[MEMKeyword.USER_DEFINED_TYPE])
        if MEMKeyword.USER_DEFINED_UNIT in data:
            self.writeKeyValue(MEMKeyword.USER_DEFINED_UNIT, data[MEMKeyword.USER_DEFINED_UNIT])

        self.writeKeyValue(MEMKeyword.TIME_SYSTEM, data[MEMKeyword.TIME_SYSTEM])

        # Stop metadata
        self.writer.write("META_STOP")
        self.writer.write(self.NEW_LINE)
        self.writer.write(self.NEW_LINE)

    # Write a single key and value to the stream using Key Value Notation (KVN).
    def writeKeyValue(self, key, value):
        convertedValue = conversion(value)
        self.writer.write(self.KV_FORMAT.format(key.name, convertedValue))

    # Write a single data line
    def writeDataLine(self, tsmd):
        # Epoch
        epoch = self.dateToString(tsmd.epoch.getComponents(self.timeScale))
        self.writer.write(epoch)
        self.writer.write(self.SPACE)

        # Data
        data = tsmd.data
        for dataCur in data:
            self.writer.write(dataCur)
            self.writer.write(self.SPACE)

        # Finish line
        self.writer.write(self.NEW_LINE)

    '''
    Create a writer for a new MEM segment.
    It is recommended to use the {@link PredefinedUserContent} enumerate to
    initialize the user content keys.
    '''
    def newSegment(self, segmentMetadata):
        meta = OrderedDict(self.metadata)
        meta.update(segmentMetadata)
        segment = MEMSegment()
        segment.addSMWdata(self, meta)
        return segment
        #return MEMSegment(self, meta)

    # Convert a date to a string
    @classmethod
    def dateToString(cls, components):
        date = components.getDate()
        time = components.getTime()
        mjd = date.getMJD()
        second = time.getSecondsInLocalDay()
        return str(mjd) + cls.SPACE + str(second)
        
# A writer for a segment of a MEM file
#class MEMSegment(OrekitFixedStepHandler):
class MEMSegment(PythonOrekitFixedStepHandler):

    '''
    # Create a new segment writer from metadata
    def __init__(self, streamingMemWriter, metadata):
        self.SMW = streamingMemWriter
        self.metadata = metadata'''

    # Override
    def init(self, s0, t, step):
        self.SMW.writeMetadata(self.metadata)

    def addSMWdata(self, streamingMemWriter, metadata):
        self.SMW = streamingMemWriter
        self.metadata = metadata

    # Override
    def handleStep(self, currentState, isLast):
        name = self.metadata[MEMKeyword.USER_DEFINED_CONTENT]
        userContent = PredefinedUserContent.getUserContent(name)
        switcher = {
            PredefinedUserContent.LLA : self.writeLLAData,
            PredefinedUserContent.KEPLERIAN : self.writeKeplerianData
        }
        if userContent in switcher:
            switcher[userContent](currentState)

    # Write Latitude/Longitude/Altitude data line.
    def writeLLAData(self, currentState):
        # Epoch
        epoch = StreamingMemWriter.dateToString(currentState.getDate(
            ).getComponents(self.SMW.timeScale))
        self.SMW.writer.write(epoch)
        self.SMW.writer.write(self.SMW.SPACE)

        # Transform the current orbital parameters to geodetic coordinates
        point = self.SMW.body.transform(currentState.getPVCoordinates().getPosition(),
            currentState.getFrame(), currentState.getDate())
        
        # Output are in [deg] for the latitude and longitude and in [km] for the altitude
        self.SMW.writer.write(str(FastMath.toDegrees(point.getLatitude())))
        self.SMW.writer.write(self.SMW.SPACE)
        self.SMW.writer.write(str(FastMath.toDegrees(point.getLongitude())))
        self.SMW.writer.write(self.SMW.SPACE)
        self.SMW.writer.write(str(point.getAltitude() * self.SMW.M_TO_KM))
        self.SMW.writer.write(self.SMW.NEW_LINE)

    # Writer keplerian parameters data line
    def writeKeplerianData(self, currentState):
        # Epoch
        epoch = StreamingMemWriter.dateToString(currentState.getDate(
            ).getComponents(self.SMW.timeScale))
        self.SMW.writer.write(epoch)
        self.SMW.writer.write(self.SMW.SPACE)

        # Keplerian orbit
        kepler = KeplerianOrbit(OrbitType.KEPLERIAN.convertType(currentState.getOrbit()))
        self.SMW.writer.write(str(kepler.getA() * self.SMW.M_TO_KM))
        self.SMW.writer.write(self.SMW.SPACE)
        self.SMW.writer.write(str(kepler.getE()))
        self.SMW.writer.write(self.SMW.SPACE)
        self.SMW.writer.write(str(FastMath.toDegrees(kepler.getI())))
        self.SMW.writer.write(self.SMW.SPACE)
        self.SMW.writer.write(str(FastMath.toDegrees(kepler.getRightAscensionOfAscendingNode(
            ))))
        self.SMW.writer.write(self.SMW.SPACE)
        self.SMW.writer.write(str(FastMath.toDegrees(kepler.getPerigeeArgument(
            ))))
        self.SMW.writer.write(self.SMW.SPACE)
        self.SMW.writer.write(str(FastMath.toDegrees(kepler.getMeanAnomaly())))
        self.SMW.writer.write(self.SMW.NEW_LINE)

# A writer for an eclipse segment of a MEM file
class MEMEclipseHandler(PythonEventHandler):

    '''def __init__(self,streamingMemWriter, metadata):
        self.SMW = streamingMemWriter
        self.metadata = metadata'''

    # Override
    def init(self, s0, t):
        self.SMW.writeMetadata(self.metadata)

    def addSMWdata(self,streamingMemWriter, metadata):
        self.SMW = streamingMemWriter
        self.metadata = metadata

    # Override
    def eventOccurred(self, s, detector, increasing):
        # Epoch
        epoch = StreamingMemWriter.dateToString(s.getDate().getComponents(self.SMW.timeScale))
        self.SMW.writer.write(epoch)
        self.SMW.writer.write(self.SMW.SPACE)

        # DAY or NIGHT
        dayOrNight = "DAY" if increasing else "NIGHT"
        self.SMW.writer.write(dayOrNight)
        self.SMW.writer.write(self.SMW.NEW_LINE)

        # Continue after event detection
        return Action.CONTINUE

# A writer for an eclipse segment of a MEM file
class MEMStationVisibilityHandler(PythonEventHandler):

    '''# Constructor
    def __init__(self, streamingMemWriter, metadata):
        self.SMW.streamingMemWriter
        self.metadata = metadata'''

    # Override
    def init(self, s0, t):
        self.SMW.writeMetadata(self.metadata)

    def addSMWdata(self, streamingMemWriter, metadata):
        self.SMW = streamingMemWriter
        self.metadata = metadata

    # Override
    def eventOccurred(self, s, detector, increasing):
        # Epoch
        epoch = StreamingMemWriter.dateToString(s.getDate().getComponents(self.SMW.timeScale))
        self.SMW.writer.write(epoch)
        self.SMW.writer.write(self.SMW.SPACE)

        # Visibility
        visibility = "START" if increasing else "END"
        self.SMW.writer.write(visibility)
        self.SMW.writer.write(self.SMW.NEW_LINE)

        # Continue after event detection
        return Action.CONTINUE
    