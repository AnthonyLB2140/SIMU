import orekit
vm = orekit.initVM()

from orekit.pyhelpers import setup_orekit_curdir
setup_orekit_curdir()

from org.hipparchus.geometry.euclidean.threed import Vector3D, RotationOrder
from org.hipparchus.util import FastMath

from org.orekit.attitudes import AttitudeProvider, AttitudesSequence, LofOffset
from org.orekit.bodies import OneAxisEllipsoid, CelestialBodyFactory, GeodeticPoint
from org.orekit.frames import FramesFactory, LOFType, TopocentricFrame
from org.orekit.orbits import CartesianOrbit, KeplerianOrbit, PositionAngle
from org.orekit.propagation import Propagator, SpacecraftState
from org.orekit.propagation.analytical import KeplerianPropagator
from org.orekit.propagation.events import EclipseDetector, ElevationDetector
from org.orekit.time import AbsoluteDate, TimeScalesFactory
from org.orekit.utils import AngularDerivativesFilter, Constants, IERSConventions, PVCoordinates
from org.orekit.propagation.sampling import OrekitFixedStepHandler, PythonOrekitFixedStepHandler

from collections import OrderedDict 

from MEMKeyword import MEMKeyword
from PredefinedUserContent import PredefinedUserContent
from StreamingMemWriter import StreamingMemWriter, MEMSegment, MEMEclipseHandler, MEMStationVisibilityHandler

## Generation du MEM Keplerian

nameFileKep = 'exampleKep.txt'

# Nature du fichier MEM
userContent = PredefinedUserContent.getUserContent("KEPLERIAN")

# Initialisation du corps central Dans cet exemple, il s'agit de la Terre
bodyFrame = FramesFactory.getITRF(IERSConventions.IERS_2010, True)
body = OneAxisEllipsoid(Constants.WGS84_EARTH_EQUATORIAL_RADIUS,
    Constants.WGS84_EARTH_FLATTENING, bodyFrame)

# Initialisation des méta-données
originator  = "CS Group"
objectName  = "Orekit-Sat"
objectID    = "2020-02A"
contentName = userContent.nameType
protocol    = userContent.protocol
dimension   = str(userContent.dimension)
dataType    = userContent.type
dataUnit    = userContent.unit

# Méta-données utilisées pour générer l'en-tête
metadata = OrderedDict()
metadata[MEMKeyword.ORIGINATOR] = originator
metadata[MEMKeyword.OBJECT_NAME] = objectName
metadata[MEMKeyword.OBJECT_ID] = objectID

# Méta-données utilisées pour les informations relatives aux
# valeurs contenues dans le fichier
segmentData = OrderedDict()
segmentData[MEMKeyword.USER_DEFINED_PROTOCOL] = protocol
segmentData[MEMKeyword.USER_DEFINED_CONTENT] = contentName
segmentData[MEMKeyword.USER_DEFINED_SIZE] = dimension
segmentData[MEMKeyword.USER_DEFINED_TYPE] = dataType
segmentData[MEMKeyword.USER_DEFINED_UNIT] = dataUnit

# Initialisation du générateur de fichier MEM
# L'en tête du fichier est écrit durant cette étape.
with open(nameFileKep, 'w') as buffer:
    writer = StreamingMemWriter(buffer, TimeScalesFactory.getUTC(),
        metadata, body)
    writer.writeHeader()
    segment = writer.newSegment(segmentData)

    # Initialisation du propagateur d'orbite. 
    # Dans ce cas, nous utilisons un propagateur d'orbite analytique keplerien.
    date = AbsoluteDate(2020, 3, 2, 14, 42, 28.6, TimeScalesFactory.getUTC())
    position = Vector3D(-29536113.0, 30329259.0, -100125.0)
    velocity = Vector3D(-2194.0, -2141.0, -8.0)
    pvCoordinates = PVCoordinates(position, velocity)
    mu = CelestialBodyFactory.getEarth().getGM()
    
    propagator = KeplerianPropagator(CartesianOrbit(pvCoordinates,
        FramesFactory.getEME2000(), date, mu))

    # Le fichier MEM est généré pendant la propagation d'orbite. Dans le cas 
    # ci-dessous, le pas est de 10 secondes. En d'autres termes, les éléments
    # orbitaux kepleriens seront calculés toutes les 10 secondes.
    step = 10.0
    duration = 86400.

    propagator.setMasterMode(step, segment)
    newDate = date.shiftedBy(duration)
    propagator.propagate(newDate)

## Generation du MEM LLA

nameFileKep = 'exampleLLA.txt'

# Nature du fichier MEM
userContent = PredefinedUserContent.getUserContent("LLA")

# Initialisation du corps central Dans cet exemple, il s'agit de la Terre
bodyFrame = FramesFactory.getITRF(IERSConventions.IERS_2010, True)
body = OneAxisEllipsoid(Constants.WGS84_EARTH_EQUATORIAL_RADIUS,
    Constants.WGS84_EARTH_FLATTENING, bodyFrame)

# Initialisation des méta-données
originator  = "CS Group"
objectName  = "Orekit-Sat"
objectID    = "2020-02A"
contentName = userContent.nameType
protocol    = userContent.protocol
dimension   = str(userContent.dimension)
dataType    = userContent.type
dataUnit    = userContent.unit

# Méta-données utilisées pour générer l'en-tête
metadata = OrderedDict()
metadata[MEMKeyword.ORIGINATOR] = originator
metadata[MEMKeyword.OBJECT_NAME] = objectName
metadata[MEMKeyword.OBJECT_ID] = objectID

# Méta-données utilisées pour les informations relatives aux
# valeurs contenues dans le fichier
segmentData = OrderedDict()
segmentData[MEMKeyword.USER_DEFINED_PROTOCOL] = protocol
segmentData[MEMKeyword.USER_DEFINED_CONTENT] = contentName
segmentData[MEMKeyword.USER_DEFINED_SIZE] = dimension
segmentData[MEMKeyword.USER_DEFINED_TYPE] = dataType
segmentData[MEMKeyword.USER_DEFINED_UNIT] = dataUnit

# Initialisation du générateur de fichier MEM
# L'en tête du fichier est écrit durant cette étape.
with open(nameFileKep, 'w') as buffer:
    writer = StreamingMemWriter(buffer, TimeScalesFactory.getUTC(),
        metadata, body)
    writer.writeHeader()
    segment = writer.newSegment(segmentData)

    # Initialisation du propagateur d'orbite. 
    # Dans ce cas, nous utilisons un propagateur d'orbite analytique keplerien.
    date = AbsoluteDate(2020, 3, 2, 14, 42, 28.6, TimeScalesFactory.getUTC())
    position = Vector3D(-29536113.0, 30329259.0, -100125.0)
    velocity = Vector3D(-2194.0, -2141.0, -8.0)
    pvCoordinates = PVCoordinates(position, velocity)
    mu = CelestialBodyFactory.getEarth().getGM()
    
    propagator = KeplerianPropagator(CartesianOrbit(pvCoordinates,
        FramesFactory.getEME2000(), date, mu))

    # Le fichier MEM est généré pendant la propagation d'orbite. Dans le cas 
    # ci-dessous, le pas est de 10 secondes. En d'autres termes, les éléments
    # orbitaux kepleriens seront calculés toutes les 10 secondes.
    step = 10.0
    duration = 86400.

    propagator.setMasterMode(step, segment)
    newDate = date.shiftedBy(duration)
    propagator.propagate(newDate)


## Generation du MEM Eclipse

nameFileKep = 'exampleEclipse.txt'

# Nature du fichier MEM
userContent = PredefinedUserContent.getUserContent("ECLIPSE")

# Initialisation du corps central Dans cet exemple, il s'agit de la Terre
bodyFrame = FramesFactory.getITRF(IERSConventions.IERS_2010, True)
body = OneAxisEllipsoid(Constants.WGS84_EARTH_EQUATORIAL_RADIUS,
    Constants.WGS84_EARTH_FLATTENING, bodyFrame)

# Initialisation des méta-données
originator  = "CS Group"
objectName  = "Orekit-Sat"
objectID    = "2020-02A"
contentName = userContent.nameType
protocol    = userContent.protocol
dimension   = str(userContent.dimension)
dataType    = userContent.type
dataUnit    = userContent.unit

# Méta-données utilisées pour générer l'en-tête
metadata = OrderedDict()
metadata[MEMKeyword.ORIGINATOR] = originator
metadata[MEMKeyword.OBJECT_NAME] = objectName
metadata[MEMKeyword.OBJECT_ID] = objectID

# Méta-données utilisées pour les informations relatives aux
# valeurs contenues dans le fichier
segmentData = OrderedDict()
segmentData[MEMKeyword.USER_DEFINED_PROTOCOL] = protocol
segmentData[MEMKeyword.USER_DEFINED_CONTENT] = contentName
segmentData[MEMKeyword.USER_DEFINED_SIZE] = dimension
segmentData[MEMKeyword.USER_DEFINED_TYPE] = dataType
segmentData[MEMKeyword.USER_DEFINED_UNIT] = dataUnit

with open('exampleEclipse.txt', 'w') as buffer:
    writer = StreamingMemWriter(buffer, TimeScalesFactory.getUTC(),
        metadata, body)
    writer.writeHeader()
    #segment = writer.newSegment(segmentData)
    class myFixedStepHandler(PythonOrekitFixedStepHandler):
        def init(self, s0, t, step):
            pass
        def handleStep(self, currentState, isLast):
            pass
    segment = myFixedStepHandler()

    # Initialisation du propagateur d'orbite. 
    # Dans ce cas, nous utilisons un propagateur d'orbite analytique keplerien.
    date = AbsoluteDate(2020, 3, 2, 14, 42, 28.6, TimeScalesFactory.getUTC())
    position = Vector3D(-29536113.0, 30329259.0, -100125.0)
    velocity = Vector3D(-2194.0, -2141.0, -8.0)
    pvCoordinates = PVCoordinates(position, velocity)
    #mu = 3.9860047e14
    mu = CelestialBodyFactory.getEarth().getGM()
    initialOrbit = CartesianOrbit(pvCoordinates, FramesFactory.getEME2000(), date, mu)

    '''dayObservationLaw = LofOffset(initialOrbit.getFrame(), 
        LOFType.VVLH, RotationOrder.XYZ, FastMath.toRadians(20.), FastMath.toRadians(40.), 0.0)
    nightRestingLaw = LofOffset(initialOrbit.getFrame(), LOFType.VVLH)
    '''
    sun = CelestialBodyFactory.getSun()
    
    handlerEclipseEvent = MEMEclipseHandler().of_(EclipseDetector)
    #handlerEclipseEvent.addSMWdata(segment.SMW, segment.metadata)
    meta = OrderedDict(writer.metadata)
    meta.update(segmentData)
    handlerEclipseEvent.addSMWdata(writer, meta)
    eclipseEvent = EclipseDetector(sun, Constants.SUN_RADIUS, body)
    eclipseEvent = eclipseEvent.withHandler(handlerEclipseEvent)

    '''attitudesSequence = AttitudesSequence()

    attitudesSequence.addSwitchingCondition(dayObservationLaw, nightRestingLaw,
        eclipseEvent, False, True, 10.0, AngularDerivativesFilter.USE_R, None)
    #attitudesSequence.addSwitchingCondition(nightRestingLaw, dayObservationLaw,
    #    eclipseEvent, True, False, 10.0, AngularDerivativesFilter.USE_R,  None)

    if (eclipseEvent.g(SpacecraftState(initialOrbit)) >= 0):
        # initial position is in daytime
        attitudesSequence.resetActiveProvider(dayObservationLaw)
    else:
        # initial position is in nighttime
        attitudesSequence.resetActiveProvider(nightRestingLaw)'''

    propagator = KeplerianPropagator(initialOrbit)#, attitudesSequence)
    propagator.addEventDetector(eclipseEvent)

    #attitudesSequence.registerSwitchEvents(propagator)

    # Le fichier MEM est généré pendant la propagation d'orbite. Dans le cas 
    # ci-dessous, le pas est de 10 secondes. En d'autres termes, les éléments
    # orbitaux kepleriens seront calculés toutes les 10 secondes.
    step = 10.0
    duration = 86400.
    propagator.setMasterMode(step, segment)
    newDate = date.shiftedBy(duration)
    propagator.propagate(newDate)

## Generation du MEM visibility

nameFileVisi = 'exampleVisibility.txt'

# Nature du fichier MEM
userContent = PredefinedUserContent.getUserContent("VISIBILITY")

# Initialisation du corps central Dans cet exemple, il s'agit de la Terre
bodyFrame = FramesFactory.getITRF(IERSConventions.IERS_2010, True)
body = OneAxisEllipsoid(Constants.WGS84_EARTH_EQUATORIAL_RADIUS,
    Constants.WGS84_EARTH_FLATTENING, bodyFrame)

# Initialisation des méta-données
originator  = "CS Group"
objectName  = "Orekit-Sat"
objectID    = "2020-02A"
contentName = userContent.nameType
protocol    = userContent.protocol
dimension   = str(userContent.dimension)
dataType    = userContent.type
dataUnit    = userContent.unit

# Méta-données utilisées pour générer l'en-tête
metadata = OrderedDict()
metadata[MEMKeyword.ORIGINATOR] = originator
metadata[MEMKeyword.OBJECT_NAME] = objectName
metadata[MEMKeyword.OBJECT_ID] = objectID

# Méta-données utilisées pour les informations relatives aux
# valeurs contenues dans le fichier
segmentData = OrderedDict()
segmentData[MEMKeyword.USER_DEFINED_PROTOCOL] = protocol
segmentData[MEMKeyword.USER_DEFINED_CONTENT] = contentName
segmentData[MEMKeyword.USER_DEFINED_SIZE] = dimension
segmentData[MEMKeyword.USER_DEFINED_TYPE] = dataType
segmentData[MEMKeyword.USER_DEFINED_UNIT] = dataUnit

with open('exampleVisibility.txt', 'w') as buffer:
    writer = StreamingMemWriter(buffer, TimeScalesFactory.getUTC(),
        metadata, body)
    writer.writeHeader()
    #segment = writer.newSegment(segmentData)
    class myFixedStepHandler(PythonOrekitFixedStepHandler):
        def init(self, s0, t, step):
            pass
        def handleStep(self, currentState, isLast):
            pass
    segment = myFixedStepHandler()

    # Initialisation du propagateur d'orbite. 
    # Dans ce cas, nous utilisons un propagateur d'orbite analytique keplerien.
    '''date = AbsoluteDate(2020, 3, 2, 14, 42, 28.6, TimeScalesFactory.getUTC())
    position = Vector3D(-29536113.0, 30329259.0, -100125.0)
    velocity = Vector3D(-2194.0, -2141.0, -8.0)
    pvCoordinates = PVCoordinates(position, velocity)
    #mu = 3.9860047e14
    mu = CelestialBodyFactory.getEarth().getGM()
    initialOrbit = CartesianOrbit(pvCoordinates, FramesFactory.getEME2000(), date, mu)
    
    # Exemple Supaero
    mySatelliteCartesian = {
        "name": "Thibault-Sat",
        "type": "cartesian",
        "x": -6142438.668,
        "y": 3492467.560,
        "z": -25767.25680,
        "vx": 505.8479685,
        "vy": 942.7809215,
        "vz": 7435.922231,
    }
    position = Vector3D(mySatelliteCartesian['x'], mySatelliteCartesian['y'], mySatelliteCartesian['z'])
    velocity = Vector3D(mySatelliteCartesian['vx'], mySatelliteCartesian['vy'], mySatelliteCartesian['vz'])
    pvCoordinates = PVCoordinates(position, velocity)
    mu = CelestialBodyFactory.getEarth().getGM()
    initialOrbit = CartesianOrbit(pvCoordinates, FramesFactory.getEME2000(), date, mu)
    '''
    mySatelliteKeplerian = {
        "name": "Lucien-Sat",
        "type": "keplerian",
        "sma": 7000000.,
        "ecc": 0.007014455530245822,
        "inc": 51.,
        "pa": 0.,
        "raan": 0.,
        "meanAnomaly": 0.,
    }
    
    mu = CelestialBodyFactory.getEarth().getGM()
    date = AbsoluteDate("2019-02-22T18:30:00Z", TimeScalesFactory.getUTC())
    initialOrbit = KeplerianOrbit(mySatelliteKeplerian['sma'], mySatelliteKeplerian['ecc'],
        FastMath.toRadians(mySatelliteKeplerian['inc']), mySatelliteKeplerian['pa'], 
        mySatelliteKeplerian['raan'], mySatelliteKeplerian['meanAnomaly'],
        PositionAngle.MEAN, FramesFactory.getEME2000(), date, mu)

    isae = {
        "name": "ISAE-SUPAERO",
        "latitude": 43,
        "longitude": 1.5,
        "altitude": 150,
        "elevation": 12
    }
    '''
    isae = {
        "name": "ISAE-SUPAERO",
        "latitude": 0.,
        "longitude": 0.,
        "altitude": 0.,
        "elevation": 12
    }'''
    station = GeodeticPoint(FastMath.toRadians(float(isae["latitude"])),FastMath.toRadians(float(isae["longitude"])),
        float(isae["altitude"])) 
    stationFrame = TopocentricFrame(body, station, isae["name"])

    dayObservationLaw = LofOffset(initialOrbit.getFrame(), 
        LOFType.VVLH, RotationOrder.XYZ, FastMath.toRadians(20.), FastMath.toRadians(40.), 0.0)
    nightRestingLaw = LofOffset(initialOrbit.getFrame(), LOFType.VVLH)
    
    handlerElevationEvent = MEMStationVisibilityHandler().of_(ElevationDetector)
    meta = OrderedDict(writer.metadata)
    meta.update(segmentData)
    handlerElevationEvent.addSMWdata(writer, meta)
    elevationEvent = ElevationDetector(stationFrame)
    elevationEvent = elevationEvent.withConstantElevation(FastMath.toRadians(float(isae['elevation'])))
    elevationEvent = elevationEvent.withHandler(handlerElevationEvent)

    propagator = KeplerianPropagator(initialOrbit)
    propagator.resetInitialState(propagator.propagate(date))
    propagator.addEventDetector(elevationEvent)
    # Le fichier MEM est généré pendant la propagation d'orbite. Dans le cas 
    # ci-dessous, le pas est de 10 secondes. En d'autres termes, les éléments
    # orbitaux kepleriens seront calculés toutes les 10 secondes.
    step = 10.0
    duration = 86400.*30.
    propagator.setMasterMode(step, segment)
    newDate = date.shiftedBy(duration)
    propagator.propagate(newDate)



