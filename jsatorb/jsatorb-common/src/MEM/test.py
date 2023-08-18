import orekit
vm = orekit.initVM()

from orekit.pyhelpers import setup_orekit_curdir
setup_orekit_curdir()

import sys
sys.path.append('src/')


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
def propagate(self):

    propagatorBis = self.satellite["propagator"]  # We keep the old propagator for now
    defaultMass = 2.0 # We need for the propagator to define a default mass for the calculation 
   # minStep = ((self.timeStep)/10.0) # For the variable step minimum we take the fixed step and divide by 100
#      maxStep = ((self.timeStep)*10.0) # For the variable step maximum we take the fixed step and multiply by 100
 #   positionTolerance = 1.0 # For the position tolerance we peek 1 meter
    orbitType = OrbitType.KEPLERIAN # It seems that this value should be the suitable type of the propagated coordinates 
    initialState = propagatorBis.getInitialState()
    initialOrbit = initialState.getOrbit()
  # tol = NumericalPropagator.tolerances(positionTolerance, initialOrbit, orbitType) # The methode tolerance it returns 
    # A two rows array, row 0 being the absolute tolerance error and row 1 being the relative tolerance error
    initialState = SpacecraftState(initialOrbit,defaultMass)   # We create an object initial state for the numerical propagator 
    integrator = ClassicalRungeKuttaIntegrator(self.timeStep)
   # integrator = DormandPrince853Integrator(minStep, maxStep, # We register the integrator
#   JArray_double.cast_(tol[0]),  # Double array of doubles needs to be casted in Python
#    JArray_double.cast_(tol[1]))

    propagator = NumericalPropagator(integrator)

    if self.nbMultiplexer == 0:
        self.multiplexer.add(myFixedStepHandler())
    propagator.setOrbitType(orbitType)
    propagator.setInitialState(initialState) #Set the initial state
    propagator.setMasterMode(self.timeStep, self.multiplexer) 
    # Don't forget to add forces
    #itrf = FramesFactory.getITRF(IERSConventions.IERS_2010, False) # International Terrestrial Reference Frame, earth fixed
    gcrf = FramesFactory.getEME2000();
    earth = OneAxisEllipsoid(Constants.WGS84_EARTH_EQUATORIAL_RADIUS,Constants.WGS84_EARTH_FLATTENING,gcrf)
   # gravityProvider = GravityFieldFactory.getNormalizedProvider(8, 8)
   #msafe = MarshallSolarActivityFutureEstimation(
#MarshallSolarActivityFutureEstimation.DEFAULT_SUPPORTED_NAMES,
#MarshallSolarActivityFutureEstimation.StrengthLevel.AVERAGE)
    #cswl = CssiSpaceWeatherData("SpaceWeather-All-v1.2.txt")
  #  sun = CelestialBodyFactory.getSun()
  #  atmosphere = DTM2000(msafe, sun, earth)
  #  atmosphere = HarrisPriester(sun, earth)    
#    cross_section=0.01
#    cd=2.0
 #   isotropic_drag = IsotropicDrag(cross_section, cd)
   # drag_force = DragForce(atmosphere, isotropic_drag)
   # propagator.addForceModel(HolmesFeatherstoneAttractionModel(earth.getBodyFrame(), gravityProvider))
    propagator.addForceModel(NewtonianAttraction(self.mu))
  #  propagator.addForceModel(drag_force)
    propagator.propagate(self.endDate)

    for fileCur in self.listFiles:
        fileCur.close()
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
