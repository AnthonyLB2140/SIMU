#!/usr/bin/env python3.7
import orekit
vm = orekit.initVM()

from orekit.pyhelpers import setup_orekit_curdir
setup_orekit_curdir()

import sys
sys.path.append('src/')
from ListCelestialBodies import ListCelestialBodies

from collections import OrderedDict 
from copy import deepcopy
from math import radians

from org.hipparchus.geometry.euclidean.threed import Vector3D, RotationOrder
from org.hipparchus.util import FastMath
# Need to add these because of the array casting
from java.util import Arrays
from orekit import JArray_double

from org.orekit.bodies import OneAxisEllipsoid, CelestialBodyFactory, GeodeticPoint
from org.orekit.frames import FramesFactory, LOFType, TopocentricFrame, Predefined
from org.orekit.orbits import CartesianOrbit, KeplerianOrbit, PositionAngle
from org.orekit.propagation import Propagator, SpacecraftState
from org.orekit.propagation.analytical import KeplerianPropagator
from org.orekit.propagation.analytical.tle import TLE, TLEPropagator
from org.orekit.propagation.events import EclipseDetector, ElevationDetector
from org.orekit.time import AbsoluteDate, TimeScalesFactory
from org.orekit.utils import AngularDerivativesFilter, Constants, IERSConventions, PVCoordinates
from org.orekit.propagation.sampling import OrekitFixedStepHandler, OrekitFixedStepHandlerMultiplexer, PythonOrekitFixedStepHandler

from MEMKeyword import MEMKeyword
from PredefinedUserContent import PredefinedUserContent
from StreamingMemWriter import StreamingMemWriter, MEMSegment, MEMEclipseHandler, MEMStationVisibilityHandler

# We need to add some imports because of the NumericalPropagator 
from org.orekit.orbits import OrbitType, PositionAngle
from org.orekit.propagation.numerical import NumericalPropagator
from org.hipparchus.ode.nonstiff import DormandPrince853Integrator
from org.hipparchus.ode.nonstiff import ClassicalRungeKuttaIntegrator
from org.orekit.forces.gravity.potential import GravityFieldFactory
from org.orekit.forces.gravity import HolmesFeatherstoneAttractionModel
from org.orekit.forces.gravity import NewtonianAttraction
from org.orekit.utils import IERSConventions
# We need to add some import because of the drag 
from org.orekit.forces.drag import IsotropicDrag
from org.orekit.forces.drag import DragForce
from org.orekit.models.earth.atmosphere import DTM2000
from org.orekit.models.earth.atmosphere import NRLMSISE00
from org.orekit.models.earth.atmosphere.data import MarshallSolarActivityFutureEstimation
from org.orekit.models.earth.atmosphere import HarrisPriester

def parse_tle(line1, line2):
    
    keplerian = {}
    
    keplerian['mean_motion'] = float(line2[52:63])
    keplerian['eccentricity'] = float('0.' + line2[26:33])
    keplerian['inclination'] = float(line2[8:16])
    keplerian['right_ascension'] = float(line2[17:25])
    keplerian['argument_of_perigee'] = float(line2[34:42])
    keplerian['mean_anomaly'] = float(line2[43:51])
        # Calculate semi-major axis (a) using mean motion (n) and Earth's gravitational constant (mu)
    mu = 398600.4418  # Earth's gravitational constant in km^3/s^2
    n = keplerian['mean_motion'] * 2 * FastMath.PI / 86400  # Convert mean motion to radians/minute
    a = (mu / (n ** 2)) ** (1 / 3)  # Calculate semi-major axis in kilometers
    keplerian['semi_major_axis'] = a
    
    
    return keplerian

def WarningSMA(satType, satOrbit, centralBody, mu):
    """
    Function that issues a simple warning if the satellite's SMA is smaller
    than the equatorial radius of the body.
    For a TLE, the considered distance is the one deducted from the mean
    motion.
    It does not necessarily means the orbit will intersect the body.
    """

    if satType == 'cartesian' or satType == 'keplerian':
        if satOrbit.getA() < centralBody.getEquatorialRadius():
            print("WARNING: semi-major axis smaller than Equatorial Radius!")
    elif satType == 'TLE':
        nCur = satOrbit.getMeanMotion() # in rad/s
        radiusCur = mu**(1./3.) / nCur**(2./3.)
        if radiusCur < centralBody.getEquatorialRadius():
            print("WARNING: initial semi-major axis smaller than Equatorial Radius!")

class myFixedStepHandler(PythonOrekitFixedStepHandler):
    """
    Customed fixed step handler that sets up the propagation step
    """
    def init(self, s0, t, step):
        pass
    def handleStep(self, currentState, isLast):
        pass

class MEMGenerator:
    """ Generates MEM files (eclipse, visibility, keplerian coordinates or 
    LLA coordinates), for given satellites, time options, and a central body. """

    # Assuming that central body is Earth
    def __init__(self, stringDateStart, timeStep, stringDateEnd, bodyString):
        self.initialDate = AbsoluteDate(stringDateStart, TimeScalesFactory.getUTC())
        self.timeStep = timeStep
        self.endDate = AbsoluteDate(stringDateEnd, TimeScalesFactory.getUTC())

        celestialBody = CelestialBodyFactory.getBody(bodyString.upper())
        if bodyString.upper() == 'EARTH':
            #bodyFrame = FramesFactory.getITRF(IERSConventions.IERS_2010, True)
            bodyFrame = FramesFactory.getEME2000()
            self.inertialFrame = FramesFactory.getEME2000()
        else:
            bodyFrame = celestialBody.getBodyOrientedFrame()
            self.inertialFrame = celestialBody.getInertiallyOrientedFrame()
            #self.inertialFrame = FramesFactory.getEME2000()

        celestialBodyShape = ListCelestialBodies.getBody(bodyString.upper())
        radiusBody = celestialBodyShape.radius
        flatBody = celestialBodyShape.flattening
        self.body = OneAxisEllipsoid(radiusBody, flatBody, bodyFrame)
        self.mu = celestialBody.getGM()
            
        self.listFiles = []
        self.multiplexer = OrekitFixedStepHandlerMultiplexer()
        self.nbMultiplexer = 0

    # Set satellite from JSON, and create orbit and propagator
    def setSatellite(self, sat):
        if(sat["type"] == "keplerian"):
            orbit = KeplerianOrbit(float(sat["sma"]), float(sat["ecc"]),
                radians(float(sat["inc"])), radians(float(sat["pa"])),
                radians(float(sat["raan"])), radians(float(sat["meanAnomaly"])),
                PositionAngle.MEAN, self.inertialFrame, self.initialDate, self.mu)

            self.satellite = {
                "name": sat["name"],
                "initialOrbit": orbit,
                "propagator": KeplerianPropagator(orbit)
            }

        elif(sat["type"] == "cartesian"):
            position = Vector3D(float(sat["x"]), float(sat["y"]), float(sat["z"]))
            velocity = Vector3D(float(sat["vx"]), float(sat["vy"]), float(sat["vz"]))
            orbit = KeplerianOrbit(PVCoordinates(position, velocity), self.inertialFrame,
                self.initialDate, self.mu)

            self.satellite = {
                "name": sat["name"],
                "initialOrbit": orbit,
                "propagator": KeplerianPropagator(orbit)
            }

        elif(sat["type"] == "tle"):
            line1 = sat["line1"]
            line2 = sat["line2"]
            
            orbitTLE = TLE(line1, line2) # Here is a little problem TLE() doesn't create an objet of class orbit but of class TLE
           # propagator = TLEPropagator.selectExtrapolator(orbit)
            
            self.initialDate = orbitTLE.getDate()
            keplerian = parse_tle(line1, line2)
            orbit = KeplerianOrbit(keplerian['semi_major_axis'], keplerian['eccentricity'],
            radians(keplerian['inclination']), radians(keplerian['argument_of_perigee']),
            radians(keplerian['right_ascension']), radians(keplerian['mean_anomaly']),
            PositionAngle.MEAN, self.inertialFrame, self.initialDate, self.mu)
            propagator = KeplerianPropagator(orbit)
            self.satellite = {
                "name": sat["name"],
                "initialOrbit": orbit,  
                "propagator": propagator
            }

        else:
            raise TypeError("Unknown satellite type")

        # Check if satellite outside central body
        WarningSMA(sat["type"], orbit, self.body, self.mu)


    def addMemVisibility(self, nameFile, groundStation):
        # Specific function for visibility that requires a ground station,

        station = GeodeticPoint(radians(float(groundStation["latitude"])),
            radians(float(groundStation["longitude"])),
            float(groundStation["altitude"]))

        station = {
            "name": groundStation["name"],
            "frame": TopocentricFrame(self.body, station, groundStation["name"]),
            "elev": radians(float(groundStation["elevation"]))
        }

        stringType = 'VISIBILITY'
        userContent = PredefinedUserContent.getUserContent(stringType)

        # Metadata init
        originator  = "CS Group"
        objectName  = self.satellite["name"]
        objectID    = self.satellite["name"]
        contentName = userContent.nameType
        protocol    = userContent.protocol
        dimension   = str(userContent.dimension)
        dataType    = userContent.type
        dataUnit    = userContent.unit

        # Header metadata
        metadata = OrderedDict()
        metadata[MEMKeyword.ORIGINATOR] = originator
        metadata[MEMKeyword.OBJECT_NAME] = objectName
        metadata[MEMKeyword.OBJECT_ID] = objectID

        # Metadata relative to values in file
        segmentData = OrderedDict()
        segmentData[MEMKeyword.USER_DEFINED_PROTOCOL] = protocol
        segmentData[MEMKeyword.USER_DEFINED_CONTENT] = contentName
        segmentData[MEMKeyword.USER_DEFINED_SIZE] = dimension
        segmentData[MEMKeyword.USER_DEFINED_TYPE] = dataType
        segmentData[MEMKeyword.USER_DEFINED_UNIT] = dataUnit

        self.listFiles.append(open(nameFile, 'w'))
        writer = StreamingMemWriter(self.listFiles[-1], TimeScalesFactory.getUTC(),
            deepcopy(metadata), self.body)
        writer.writeHeader()

        self.handlerVisibility(deepcopy(segmentData), writer, station)

    # Set MEM type and init metadata
    def addMemType(self, stringType, nameFile):
        self.type = stringType
        userContent = PredefinedUserContent.getUserContent(stringType)

        # Metadata init
        originator  = "CS Group"
        objectName  = self.satellite["name"]
        objectID    = self.satellite["name"]
        contentName = userContent.nameType
        protocol    = userContent.protocol
        dimension   = str(userContent.dimension)
        dataType    = userContent.type
        dataUnit    = userContent.unit

        # Header metadata
        metadata = OrderedDict()
        metadata[MEMKeyword.ORIGINATOR] = originator
        metadata[MEMKeyword.OBJECT_NAME] = objectName
        metadata[MEMKeyword.OBJECT_ID] = objectID

        # Metadata relative to values in file
        segmentData = OrderedDict()
        segmentData[MEMKeyword.USER_DEFINED_PROTOCOL] = protocol
        segmentData[MEMKeyword.USER_DEFINED_CONTENT] = contentName
        segmentData[MEMKeyword.USER_DEFINED_SIZE] = dimension
        segmentData[MEMKeyword.USER_DEFINED_TYPE] = dataType
        segmentData[MEMKeyword.USER_DEFINED_UNIT] = dataUnit

        self.listFiles.append(open(nameFile, 'w'))
        writer = StreamingMemWriter(self.listFiles[-1], TimeScalesFactory.getUTC(),
            deepcopy(metadata), self.body)
        writer.writeHeader()

        # Execute different function depending on chosen option
        switcher = {
            'KEPLERIAN': self.handlerOrbit,
            'LLA': self.handlerOrbit,
            'ECLIPSE': self.handlerEclipse
        }
        switcher[stringType](deepcopy(segmentData), writer)

    def propagate(self):
    
        defaultMass = 2.0 # We need for the propagator to define a default mass for the calculation 
        initialOrbit = self.satellite["initialOrbit"]
        initialState = SpacecraftState(initialOrbit,defaultMass)   # We create an object initial state for the numerical propagator 
        integrator = ClassicalRungeKuttaIntegrator(self.timeStep)
        propagator = NumericalPropagator(integrator)
	    
        if self.nbMultiplexer == 0:
            self.multiplexer.add(myFixedStepHandler())
        propagator.setOrbitType(initialOrbit.getType())
        propagator.setInitialState(initialState) #Set the initial state
   
        print("Mean Anomaly :",FastMath.toDegrees(initialOrbit.getMeanAnomaly()))
        print("RAAN  :",FastMath.toDegrees(initialOrbit.getRightAscensionOfAscendingNode()))
        print("Eccentricity  :",(initialOrbit.getE()))
        print("Date  :",(initialOrbit.getDate()))
        print("AOP:",FastMath.toDegrees(initialOrbit.getPerigeeArgument()));
        print("Mean Motion :",initialState.getOrbit().getKeplerianMeanMotion()/(2*FastMath.PI));
        print("Incli :",FastMath.toDegrees(initialState.getI()));
        

        
        propagator.setMasterMode(self.timeStep, self.multiplexer) 

        propagator.addForceModel(NewtonianAttraction(self.mu))

        propagator.propagate(self.endDate)
        
        for fileCur in self.listFiles:
            fileCur.close()

    def handlerOrbit(self, segmentData, writer):
        self.multiplexer.add(writer.newSegment(segmentData))
        self.nbMultiplexer =+ 1

    def handlerEclipse(self, segmentData, writer):
        sun = CelestialBodyFactory.getSun()
        handlerEclipseEvent = MEMEclipseHandler().of_(EclipseDetector)
        meta = OrderedDict(writer.metadata)
        meta.update(segmentData)
        handlerEclipseEvent.addSMWdata(writer, meta)

        eclipseEvent = EclipseDetector(sun, ListCelestialBodies.getBody("SUN").radius,
            self.body)
        eclipseEvent = eclipseEvent.withHandler(handlerEclipseEvent)

        self.satellite["propagator"].addEventDetector(eclipseEvent)

    def handlerVisibility(self, segmentData, writer, station):
        handlerElevationEvent = MEMStationVisibilityHandler().of_(ElevationDetector)
        meta = OrderedDict(writer.metadata)
        meta.update(segmentData)
        handlerElevationEvent.addSMWdata(writer, meta)

        elevationEvent = ElevationDetector(station["frame"])
        elevationEvent = elevationEvent.withConstantElevation(station["elev"])
        elevationEvent = elevationEvent.withHandler(handlerElevationEvent)

        self.satellite["propagator"].addEventDetector(elevationEvent)
        
if __name__ == "__main__":
    mySatelliteKeplerian = {
        "name": "Lucien-Sat",
        "type": "keplerian",
        "sma": 7000000,
        "ecc": 0.007014455530245822,
        "inc": 51,
        "pa": 0,
        "raan": 0,
        "meanAnomaly": 0,
    }

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

    mySatelliteTLE = {
        "name": "ISS (ZARYA)",
        "type": "tle",
        "line1": "1 25544U 98067A   08264.51782528 -.00002182  00000-0 -11606-4 0  2927",
        "line2": "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391563537"
    }

    isae = {
        "name": "ISAE-SUPAERO",
        "latitude": 43,
        "longitude": 1.5,
        "altitude": 150,
        "elevation": 12
    }

    cayenne = {
        "name": "cayenne",
        "latitude": 4.5,
        "longitude": -52.9,
        "altitude": 0,
        "elevation": 12
    }

    step = 10.0
    stringDateStart = "2020-03-02T14:42:28.6Z"
    stringDateEnd = "2020-03-03T14:42:28.6Z"
    bodyString = 'EARTH'

    memGenerator = MEMGenerator(stringDateStart, step, stringDateEnd, bodyString)
    memGenerator.setSatellite(mySatelliteCartesian)

    memGenerator.addMemType('KEPLERIAN', 'exampleKep.MEM')
    memGenerator.addMemType('LLA', 'exampleLLA.MEM')
    memGenerator.addMemType('ECLIPSE', 'exampleEclipse.MEM')

    memGenerator.addMemVisibility('exampleVisibilityIsae.MEM', isae)
    memGenerator.addMemVisibility('exampleVisibilityCayenne.MEM', cayenne)

    memGenerator.propagate()
