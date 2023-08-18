# Written from gitlab example of the python wrapper of orekit by Petrus Hyvonen
# url:   https://gitlab.orekit.org/orekit-labs/python-wrapper/-/blob/master/examples/Example_EarthObservation_-_Attitude_Sequence.ipynb

import orekit
#orekit = __import__("orekit-10.2")
orekit.initVM()

from orekit.pyhelpers import setup_orekit_curdir
setup_orekit_curdir()

from org.hipparchus.geometry.euclidean.threed import RotationOrder
from org.hipparchus.geometry.euclidean.threed import Vector3D

from org.orekit.attitudes import AttitudeProvider;
from org.orekit.attitudes import AttitudesSequence;
from org.orekit.attitudes import LofOffset;
from org.orekit.bodies import CelestialBodyFactory, OneAxisEllipsoid;
from org.orekit.errors import OrekitException;
#from org.orekit.errors import PropagationException
from org.orekit.frames import FramesFactory
from org.orekit.frames import LOFType;
from org.orekit.orbits import KeplerianOrbit, Orbit, PositionAngle
from org.orekit.propagation import Propagator
from org.orekit.propagation import SpacecraftState
from org.orekit.propagation.analytical import EcksteinHechlerPropagator, KeplerianPropagator
from org.orekit.propagation.events import EclipseDetector
from org.orekit.propagation.events import EventDetector
from org.orekit.propagation.events.handlers import EventHandler, PythonEventHandler
from org.orekit.propagation.sampling import OrekitFixedStepHandler, PythonOrekitFixedStepHandler
from org.orekit.time import AbsoluteDate
from org.orekit.time import TimeScalesFactory
from org.orekit.utils import Constants, IERSConventions, AngularDerivativesFilter
from org.orekit.utils import PVCoordinates
from org.orekit.utils import PVCoordinatesProvider
from org.hipparchus.ode.events import Action

import math

def gitEclipseDetector(param1, param2, param3, param4, param5, param6, typeOrbit, initialDate, duration):
    output = []
    
    if typeOrbit == 'keplerian':
        initialOrbit = KeplerianOrbit(param1, param2, param3, param4, param5,
            param6, PositionAngle.MEAN, FramesFactory.getEME2000(),
            initialDate, Constants.EIGEN5C_EARTH_MU)
    elif typeOrbit == 'cartesian':
        position = Vector3D(param1, param2, param3)
        velocity = Vector3D(param4, param5, param6)
        initialOrbit =  KeplerianOrbit(PVCoordinates(position, velocity),
            FramesFactory.getEME2000(), initialDate, Constants.EIGEN5C_EARTH_MU)

    dayObservationLaw = LofOffset(initialOrbit.getFrame(), 
        LOFType.VVLH, RotationOrder.XYZ, math.radians(20), math.radians(40), 0.0)

    nightRestingLaw = LofOffset(initialOrbit.getFrame(), LOFType.VVLH)

    class myNightEclipseDetector(PythonEventHandler):
        
        def init(self, s, T):
            pass
        
        def eventOccurred(self, s, detector, increasing):
            if not increasing:
                output.append([s.getDate(), 'entering eclipse'])
                #print(s.getDate()," : event occurred, entering eclipse => switching to night law")
            return Action.CONTINUE
        
        def resetState(self, detector, oldState):
            return oldState

    class myDayEclipseDetector(PythonEventHandler):
        
        def init(self, s, T):
            pass
        
        def eventOccurred(self, s, detector, increasing):
            if increasing:
                output.append([s.getDate(), 'exiting eclipse'])
                #print(s.getDate()," : event occurred, exiting eclipse => switching to day law")
            return Action.CONTINUE
        
        def resetState(self, detector, oldState):
            return oldState

    sun = CelestialBodyFactory.getSun()
    #earth = OneAxisEllipsoid(Constants.WGS84_EARTH_EQUATORIAL_RADIUS,
    #    0.0, FramesFactory.getITRF(IERSConventions.IERS_2010, True))
    earth = OneAxisEllipsoid(Constants.WGS84_EARTH_EQUATORIAL_RADIUS,
        Constants.WGS84_EARTH_FLATTENING, FramesFactory.getITRF(IERSConventions.IERS_2010, True))

    dayNightEvent = EclipseDetector(sun, 696000000., earth)
    dayNightEvent = dayNightEvent.withHandler(myNightEclipseDetector().of_(EclipseDetector))
    nightDayEvent = EclipseDetector(sun, 696000000., earth)
    nightDayEvent = nightDayEvent.withHandler(myDayEclipseDetector().of_(EclipseDetector))

    attitudesSequence = AttitudesSequence()

    # Should add something more on Switching

    attitudesSequence.addSwitchingCondition(dayObservationLaw, nightRestingLaw,
                                            dayNightEvent, False, True, 10.0, 
                                            AngularDerivativesFilter.USE_R, None)


    attitudesSequence.addSwitchingCondition(nightRestingLaw, dayObservationLaw, nightDayEvent, True, False, 10.0, AngularDerivativesFilter.USE_R,  None)

    if (dayNightEvent.g(SpacecraftState(initialOrbit)) >= 0):
        # initial position is in daytime
        attitudesSequence.resetActiveProvider(dayObservationLaw)
    else:
        # initial position is in nighttime
        attitudesSequence.resetActiveProvider(nightRestingLaw)

    '''propagator = EcksteinHechlerPropagator(initialOrbit, attitudesSequence,
        Constants.EIGEN5C_EARTH_EQUATORIAL_RADIUS, Constants.EIGEN5C_EARTH_MU, Constants.EIGEN5C_EARTH_C20,
        Constants.EIGEN5C_EARTH_C30, Constants.EIGEN5C_EARTH_C40, Constants.EIGEN5C_EARTH_C50, Constants.EIGEN5C_EARTH_C60)
    '''
    propagator = KeplerianPropagator(initialOrbit, attitudesSequence)


    attitudesSequence.registerSwitchEvents(propagator)
    class mystephandler(PythonOrekitFixedStepHandler):
        
        eclipseAngles = []
        pointingOffsets = []
        dates = []
        
        def init(self,s0, t, step):
            pass
            
        def handleStep(self,currentState, isLast):
            # the Earth position in spacecraft frame should be along spacecraft Z axis
            # during nigthtime and away from it during daytime due to roll and pitch offsets
            earth = currentState.toTransform().transformPosition(Vector3D.ZERO)
            pointingOffset = Vector3D.angle(earth, Vector3D.PLUS_K)

            # the g function is the eclipse indicator, its an angle between Sun and Earth limb,
            # positive when Sun is outside of Earth limb, negative when Sun is hidden by Earth limb
            eclipseAngle = dayNightEvent.g(currentState)
            #print ("%s    %6.3f    %6.1f" % (currentState.getDate(), eclipseAngle, math.degrees(pointingOffset)))
            
            self.eclipseAngles.append(eclipseAngle)
            self.pointingOffsets.append(math.degrees(pointingOffset))
            self.dates.append(currentState.getDate())

    handler = mystephandler()
    propagator.setMasterMode(180.0, handler)

    finalState = propagator.propagate(initialDate.shiftedBy(duration))

    return output

