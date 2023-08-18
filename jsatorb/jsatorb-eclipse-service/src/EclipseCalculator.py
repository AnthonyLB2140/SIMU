from datetime import datetime

import orekit
vm = orekit.initVM()

from orekit.pyhelpers import setup_orekit_curdir
setup_orekit_curdir()

from org.hipparchus.geometry.euclidean.threed import RotationOrder, Vector3D
from org.hipparchus.ode.events import Action
from org.hipparchus.util import FastMath, Pair

from org.orekit.attitudes import AttitudeProvider, AttitudesSequence, LofOffset
from org.orekit.bodies import CelestialBodyFactory, OneAxisEllipsoid
from org.orekit.errors import OrekitException
from org.orekit.frames import FramesFactory, LOFType
from org.orekit.orbits import CartesianOrbit, KeplerianOrbit, Orbit, PositionAngle
from org.orekit.propagation import Propagator, SpacecraftState
from org.orekit.propagation.analytical import KeplerianPropagator
from org.orekit.propagation.events import EclipseDetector, EventDetector
from org.orekit.propagation.events.handlers import ContinueOnEvent, EventHandler, PythonEventHandler
from org.orekit.time import AbsoluteDate, TimeScalesFactory
from org.orekit.utils import AngularDerivativesFilter, Constants, IERSConventions, PVCoordinates, PVCoordinatesProvider

from org.orekit.propagation.sampling import OrekitFixedStepHandler, PythonOrekitFixedStepHandler

'''
This class is currently not used in JSatOrb but can still be called by the REST API.
'''

class HAL_SatPos:

    def __init__(self, param1, param2, param3, param4, param5, param6, typeSat):
        self.param1, self.param2, self.param3 = float(param1), float(param2), float(param3)
        self.param4, self.param5, self.param6 = float(param4), float(param5), float(param6)
        self.typeSat = typeSat

class myNightEclipseDetector(PythonEventHandler):
    
    def init(self, s, T):
        pass
    
    def addOutput(self, output):
        self.output = output

    def eventOccurred(self, s, detector, increasing):
        if not increasing:
            self.output.append([s.getDate()])
            #print(s.getDate()," : event occurred, entering eclipse => switching to night law")
        return Action.CONTINUE
    
    def resetState(self, detector, oldState):
        return oldState

class myDayEclipseDetector(PythonEventHandler):
    
    def init(self, s, T):
        pass
    
    def addOutput(self, output):
        self.output = output

    def eventOccurred(self, s, detector, increasing):
        if increasing:
            if len(self.output) > 0:
                self.output[-1].append(s.getDate())
            else:
                self.output.append([s.getDate()])
            #print(s.getDate()," : event occurred, exiting eclipse => switching to day law")
        return Action.CONTINUE
    
    def resetState(self, detector, oldState):
        return oldState


class EclipseCalculator:
    
    # Attributes: init and end dates, orbit, mu, output
    mu =  3.986004415e+14

    '''
    Initiate with a HAL_SatPos kepOrCartPos, an initial date and an end date
    '''
    def __init__(self, kepOrCartPos, initialDateTime, endDateTime):
        self.initDate = AbsoluteDate(initialDateTime.year, initialDateTime.month,
            initialDateTime.day, initialDateTime.hour, initialDateTime.minute,
            float(initialDateTime.second), TimeScalesFactory.getUTC())

        self.endDate = AbsoluteDate(endDateTime.year, endDateTime.month,
            endDateTime.day, endDateTime.hour, endDateTime.minute,
            float(endDateTime.second), TimeScalesFactory.getUTC())

        if self.endDate.compareTo(self.initDate) < 0:
            raise ValueError("End date before start date")

        if kepOrCartPos.typeSat == 'keplerian':
            self.orbit = KeplerianOrbit(kepOrCartPos.param1, 
                kepOrCartPos.param2, kepOrCartPos.param3, kepOrCartPos.param4,
                kepOrCartPos.param5, kepOrCartPos.param6, PositionAngle.MEAN,
                FramesFactory.getEME2000(), self.initDate, self.mu)
        elif kepOrCartPos.typeSat == 'cartesian':
            pos = Vector3D(kepOrCartPos.param1, kepOrCartPos.param2, kepOrCartPos.param3)
            speed = Vector3D(kepOrCartPos.param4, kepOrCartPos.param5, kepOrCartPos.param6)
            self.orbit = CartesianOrbit(PVCoordinates(pos, speed),
                FramesFactory.getEME2000(), self.initDate, self.mu)

        # Output will be a list of tuples
        self.output = []

    def getEclipse(self):
        try:
            # Attitudes sequence definition
            dayObservationLaw = LofOffset(self.orbit.getFrame(), LOFType.VVLH,
                RotationOrder.XYZ, FastMath.toRadians(20.), FastMath.toRadians(40.),
                0.)
            nightRestingLaw = LofOffset(self.orbit.getFrame(), LOFType.VVLH)

            sun = CelestialBodyFactory.getSun()
            ITRF = FramesFactory.getITRF(IERSConventions.IERS_2010, True)
            earth = OneAxisEllipsoid(Constants.WGS84_EARTH_EQUATORIAL_RADIUS,
                Constants.WGS84_EARTH_FLATTENING, ITRF)
            #earth = OneAxisEllipsoid(Constants.WGS84_EARTH_EQUATORIAL_RADIUS,
            #    0., ITRF)

            # Creation of trigger events
            dayNightEvent = EclipseDetector(sun, 696000000., earth)
            handlerDayNightEvent = myNightEclipseDetector().of_(EclipseDetector)
            handlerDayNightEvent.addOutput(self.output)
            dayNightEvent = dayNightEvent.withHandler(handlerDayNightEvent)

            nightDayEvent = EclipseDetector(sun, 696000000., earth)
            handlerNightDayEvent = myDayEclipseDetector().of_(EclipseDetector)
            handlerNightDayEvent.addOutput(self.output)
            nightDayEvent = nightDayEvent.withHandler(handlerNightDayEvent)

            attitudesSequence = AttitudesSequence()
            #switchHandler = SwitchHandlerPython(self.output)
            
            # Add the swithchHandler as callback
            attitudesSequence.addSwitchingCondition(dayObservationLaw, 
                nightRestingLaw, dayNightEvent, False, True, 10.0,
                AngularDerivativesFilter.USE_R, None)
            attitudesSequence.addSwitchingCondition(nightRestingLaw,
                dayObservationLaw, nightDayEvent, True, False, 10.0,
                AngularDerivativesFilter.USE_R, None)

            if dayNightEvent.g(SpacecraftState(self.orbit)) >= 0.:
                attitudesSequence.resetActiveProvider(dayObservationLaw)
            else:
                attitudesSequence.resetActiveProvider(nightRestingLaw)

            propagator = KeplerianPropagator(self.orbit, attitudesSequence)

            attitudesSequence.registerSwitchEvents(propagator)

            propagator.propagate(self.endDate)
            #print("Propagation ended at " + finalState.getDate().toString())
        
        except OrekitException as oe:
            print(oe.getMessage())

        if len(self.output[0]) == 1:
            self.output[0].insert(0, self.initDate)

        if len(self.output[-1]) == 1:
            self.output[-1].append(self.endDate)

        return self.output
        
