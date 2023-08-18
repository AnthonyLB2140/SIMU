# Original author: ISAE, continued by CS Group

import orekit
vm = orekit.initVM()

import sys
sys.path.append('../jsatorb-common/src/')
from ListCelestialBodies import ListCelestialBodies

from PropagationTimeSettings import PropagationTimeSettings
from OEMAndJSONConverter import OEMAndJSONConverter
import json
from org.hipparchus.geometry.euclidean.threed import Vector3D
from org.orekit.frames import FramesFactory, TopocentricFrame
from org.orekit.bodies import OneAxisEllipsoid, GeodeticPoint, CelestialBodyFactory
from org.orekit.utils import IERSConventions, Constants
from org.orekit.orbits import KeplerianOrbit, PositionAngle
from org.orekit.utils import PVCoordinates
from org.orekit.propagation.analytical import KeplerianPropagator
from org.orekit.propagation.events.handlers import EventHandler
from org.orekit.propagation.analytical.tle import TLE, TLEPropagator
from org.orekit.python import PythonEventHandler, PythonOrekitFixedStepHandler
from math import radians, pi, degrees
from org.orekit.orbits import OrbitType, PositionAngle
from org.orekit.propagation.numerical import NumericalPropagator
from org.hipparchus.ode.nonstiff import DormandPrince853Integrator
from org.hipparchus.ode.nonstiff import ClassicalRungeKuttaIntegrator
from org.orekit.forces.gravity.potential import GravityFieldFactory
from org.orekit.forces.gravity import HolmesFeatherstoneAttractionModel
from org.orekit.forces.gravity import NewtonianAttraction
from org.orekit.propagation import Propagator, SpacecraftState
from org.hipparchus.util import FastMath
from orekit import JArray_double
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

class HAL_MissionAnalysis(PropagationTimeSettings):
    """
    Class that permit to propagate TLE, KEPLERIAN, CARTESIAN Satellite position to RETURN :
    ephemerids (on a JSON format or CCSDS file)
    visibility if ground station has been added
    The visibility is currently not used in JSatOrb but can still be called by the REST API.
    """

    def __init__(self, timeStep, dateEnd, bodyString):
        """Constructor specifies the time settings of the propagation """
        #Heritage Method
        PropagationTimeSettings.__init__(self, int(timeStep), str(dateEnd))

        celestialBody = CelestialBodyFactory.getBody(bodyString.upper())
        self.nameBody = celestialBody.getName()
        if bodyString.upper() == 'EARTH':
            bodyFrame = FramesFactory.getITRF(IERSConventions.IERS_2010, True)
            self.inertialFrame = FramesFactory.getEME2000()
        else:
            bodyFrame = celestialBody.getBodyOrientedFrame()
            #self.inertialFrame = celestialBody.getInertiallyOrientedFrame()
            self.inertialFrame = FramesFactory.getEME2000()

        celestialBodyShape = ListCelestialBodies.getBody(bodyString.upper())
        radiusBody = celestialBodyShape.radius
        flatBody = celestialBodyShape.flattening
        self.body = OneAxisEllipsoid(radiusBody, flatBody, bodyFrame)
        self.mu = celestialBody.getGM()

        #Needed Constant Init
        #self.ae = Constants.WGS84_EARTH_EQUATORIAL_RADIUS
        #self.mu = Constants.WGS84_EARTH_MU

        #Parameter Init
        #self.inertialFrame = FramesFactory.getEME2000()
        self.satelliteList = {} # Satellite List saved like a KeplerianOrbit, Key of Element is satellite Name
        self.tleList = {}
        self.rawEphemeridsList = {} # epoch, x, y, z, vx, vy, vz data sor by satellite Name
        self.groundStationList = {} # GroundStationList
        self.visibilityMatrice = {}

        #lupinArray is storing ground station pointing informations on an array
        # 1 information is represented by the following json
        # {
        # "station": "cayenne",
        # "date": "2019-12-25T17:15:00Z",
        # "azimuth": 53,
        # "elevation": 18
        #     }
        self.lupinArray = []


    def addSatellite(self, satellite):
        """
        Add 1 satellite to the ones to propagate
        :param satellite:
        :return:
        """

        if(satellite["type"] == "keplerian"):
            try:
                orbit = KeplerianOrbit(float(satellite["sma"]), float(satellite["ecc"]),
                                       radians(float(satellite["inc"])),
                                       radians(float(satellite["pa"])), radians(float(satellite["raan"])),
                                       radians(float(satellite["meanAnomaly"])),
                                       PositionAngle.MEAN, self.inertialFrame, self.absoluteStartTime, self.mu)
                self.satelliteList[satellite["name"]] = {
                    "initialState": orbit,
                    "propagator": KeplerianPropagator(orbit),
                    "celestialBody": self.nameBody
                }
            except:
                raise NameError("start time is not defined")

        elif(satellite["type"] == "cartesian"):
            try:
                position = Vector3D(float(satellite["x"]), float(satellite["y"]), float(satellite["z"]))
                velocity = Vector3D(float(satellite["vx"]), float(satellite["vy"]), float(satellite["vz"]))
                orbit = KeplerianOrbit(PVCoordinates(position, velocity), self.inertialFrame,
                                       self.absoluteStartTime, self.mu)
                self.satelliteList[satellite["name"]] = {
                    "initialState": orbit,
                    "propagator": KeplerianPropagator(orbit),
                    "celestialBody": self.nameBody
                }
            except:
                raise NameError("start time is not defined")

        elif(satellite["type"] == "tle"):
            orbit = TLE(satellite["line1"], satellite["line2"])
            #propagator = TLEPropagator.selectExtrapolator(orbit)
            if orbit.getDate().compareTo(self.absoluteStartTime) > 0:
                self.absoluteStartTime = orbit.getDate()
            keplerian = parse_tle(satellite["line1"], satellite["line2"])
            orbitTLE = TLE(satellite["line1"], satellite["line2"])
            
            satellite["initialOrbit"] = KeplerianOrbit(keplerian['semi_major_axis'], keplerian['eccentricity'],
            radians(keplerian['inclination']), radians(keplerian['argument_of_perigee']),
            radians(keplerian['right_ascension']), radians(keplerian['mean_anomaly']),
            PositionAngle.MEAN, self.inertialFrame, orbitTLE.getDate(), self.mu)

            defaultMass = 2.0 # We need for the propagator to define a default mass for the calculation 
            initialOrbit = satellite["initialOrbit"]
            orbitType = OrbitType.KEPLERIAN
            initialState = SpacecraftState(initialOrbit,defaultMass)   # We create an object initial state for the numerical propagator 
            #  integrator = ClassicalRungeKuttaIntegrator(self.timeStep)
            minStep = ((self.timeStep)/1000) # For the variable step minimum we take the fixed step and divide by 100
            maxStep = ((self.timeStep)*1000)# For the variable step maximum we take the fixed step and multiply by 100
            positionTolerance = 0.1 #  for the position tolerance we peek 1 meter
            
            tol = NumericalPropagator.tolerances(positionTolerance, initialOrbit, orbitType) # The methode tolerance it returns 
            #   A two rows array, row 0 being the absolute tolerance error and row 1 being the relative tolerance error

            integrator = DormandPrince853Integrator(minStep, maxStep,JArray_double.cast_(tol[0]),JArray_double.cast_(tol[1]))
            propagator = NumericalPropagator(integrator)
            propagator.addForceModel(NewtonianAttraction(self.mu))

            propagator.setInitialState(initialState)
            
            #propagator = KeplerianPropagator(initialOrbit)
            #self.absoluteEndTime = self.absoluteStartTime.shiftedBy(self.duration)
            self.satelliteList[satellite["name"]] = {
                "isTLE": True,
                "initialState": initialState,
                "propagator": propagator,
                "celestialBody": self.nameBody
            }

        # Check if satellite outside central body
        WarningSMA(satellite["type"], orbit, self.body, self.mu)

    def addGroundStation(self, groundStation):
        """
        Add 1 groundStation to the ones to register
        :param groundStation:
        :return:
        """
        #ITRF = FramesFactory.getITRF(IERSConventions.IERS_2010, True)
        station = GeodeticPoint(radians(float(groundStation["latitude"])),radians(float(groundStation["longitude"])), float(groundStation["altitude"]))
        #earth = OneAxisEllipsoid(Constants.WGS84_EARTH_EQUATORIAL_RADIUS,
        #                         Constants.WGS84_EARTH_FLATTENING,
        #                         ITRF)
    
        stationFrame = TopocentricFrame(self.body, station, groundStation["name"])
        self.groundStationList[groundStation["name"]] = { "station": stationFrame, "passing": False,
                                                          "elev": float(groundStation["elevation"]) }

    def getSatelliteList(self):
        """Return Satellite list to propagate"""
        return self.satelliteList

    def getGroundStationList(self):
        """
        Return ground Station list
        :return:
        """
        return self.groundStationList

    def propagate(self):
        """
        Execute the propagation calculation
        """
        #Initialize lupinArray that will store object
        print("propagate-1")
        
        # TLEs have to catch up to one another
        for satName, sat in self.satelliteList.items():
            initialDateCur = sat["initialState"].getDate()
        #    print("before propa initialstate :",sat["initialState"].getOrbit().getPVCoordinates(),sat["initialState"].getOrbit().getDate())
            if "isTLE" in sat and initialDateCur.compareTo(self.absoluteStartTime) < 0: # if TLE is late 
          #      print("isTLE at date",sat["initialState"].getDate())
                print("the propagator :",sat["propagator"].getFrame(),sat["propagator"].getInitialState())
                sat['propagator'].setOrbitType(OrbitType.KEPLERIAN)
                sat["propagator"].propagate(self.absoluteStartTime)                     # Propagate the TLE to the absolute date the latest TLE 
                print("the propagator :",sat["propagator"].getFrame(),sat["propagator"].getInitialState())
               
                print("the propagator :",sat["propagator"].getFrame(),sat["propagator"].getInitialState())
                
           #     print("the propagation date was ",self.absoluteStartTime)
            #    sat["initialState"] = sat["propagator"].getInitialState()               # set the field initial state to TLE or now to a state 
            #    print("Initialization: TLE of {} was propagated from {} to {} ".format(satName, initialDateCur, self.absoluteStartTime))
               #print("new initialstate :",sat["initialState"].getOrbit().getPVCoordinates(),sat["initialState"].getOrbit().getDate())
           
        # Initialize python array in dictionary
        for key, value in self.satelliteList.items():
            self.rawEphemeridsList[key] = []

        # Initialize matrice of visibility

        for gsKey, gsValue in self.groundStationList.items():
            self.visibilityMatrice[gsKey] = {}
            for satKey, satValue in self.satelliteList.items():
                self.visibilityMatrice[gsKey][satKey] = []
                # Seront Stocker dans la visibilityMatrice les élements suivants
                # startingDate, endingDate, azimuthBegining, azimuthEnd
        print("propagate-2")
        # Propagate  
        limitDate= self.absoluteStartTime.shiftedBy(self.timeStep*15)                   
        extrapDate = self.absoluteStartTime                                 # init the propagation date to very first date 
        while (extrapDate.compareTo(self.absoluteEndTime) <= 0.0):          # until the End Date 
            for satKey, satValue in self.satelliteList.items():     
                #satValue['propagator'].setOrbitType(OrbitType.CARTESIAN)        # For all satellite 
                #satValue['propagator'].addForceModel(NewtonianAttraction(self.mu))
                
                currState = satValue['propagator'].propagate(extrapDate)    # Current state is equal is set to the return of the propagation until the current step 
                
                # Get and Format Ephemerids Informations
                pVCoordinates = currState.getOrbit().getPVCoordinates(FramesFactory.getEME2000())     # Extact the PV 
                position = pVCoordinates.getPosition()     # Extract the position
                velocity= pVCoordinates.getVelocity()   
                if extrapDate.compareTo(limitDate) <= 0.0:print("position :",position)                   # Extract the velocity
                #  print("currState  :",currState.getOrbit().getPVCoordinates(),currState.getDate())
                # Format and Append position propagate to array
                currData = {                                                # Append cartesian coordinates and epoch
                    "epoch": currState.getDate().toString(),
                    "x": round(position.getX(), 7),
                    "y": round(position.getY(), 7),
                    "z": round(position.getZ(), 7),
                    "vx": round(velocity.getX(), 7),
                    "vy": round(velocity.getY(), 7),
                    "vz": round(velocity.getZ(), 7)
                }
                self.rawEphemeridsList[satKey].append(currData)             # rawEphemerids stores the coordinates at each step

                # Calculate and Format visibility Informations
                for gsKey, gsValue in self.groundStationList.items():
                    el_tmp = degrees(gsValue["station"].getElevation(position, self.inertialFrame, extrapDate))
                    az_tmp = degrees(gsValue["station"].getAzimuth(position, self.inertialFrame, extrapDate))
                    temp_data = {}
                    if el_tmp >= gsValue["elev"]:
                        ## LUPIN CODE
                        # self.lupinArray.append({
                        #     "date": self.absDate2ISOString(currState.getDate()),
                        #     "station": gsKey,
                        #     "elevation": el_tmp,
                        #     "azimuth": az_tmp
                        # })

                        ## FIN LUPIN CODE
                        if not self.visibilityMatrice[gsKey][satKey] or self.visibilityMatrice[gsKey][satKey][
                                -1]["passing"] == False:
                            temp_data['startDate'] = currState.getDate().toString()
                            temp_data['startAz'] = az_tmp
                            temp_data['passing'] = True
                            self.visibilityMatrice[gsKey][satKey].append(temp_data)
                    else:
                        ## Si le tableau a dejà commencé à être rempli et que la matrice de visibilitié
                        if  len(self.visibilityMatrice[gsKey][satKey])>0 and self.visibilityMatrice[gsKey][satKey][-1]["passing"] == True:
                            self.visibilityMatrice[gsKey][satKey][-1]["endDate"] = currState.getDate().toString()
                            self.visibilityMatrice[gsKey][satKey][-1]["endAz"] = az_tmp
                            self.visibilityMatrice[gsKey][satKey][-1]["passing"] = False


            extrapDate = extrapDate.shiftedBy(self.timeStep) 
                          # increment  the propagation date with one step
        # Format data Ephemeris data
        self.formatedData = OEMAndJSONConverter(self.rawEphemeridsList)      # format the data in rawEphemeris (cartesian coordinate) into a JSON 



    def getJSONEphemerids(self):
        """
        Get Ephemerids in JSON format
        :param outputFormat:
        :return:
        """
        assert (self.formatedData is not None)
        return self.formatedData.getJSON()

    def _getRawData(self):
        """
        Get Ephemerids data in a weirdo format
        :return:
        """
        assert (self.rawEphemeridsList is not None)
        return self.rawEphemeridsList

    def getOEMEphemerids(self):
        """
        Get Ephemerids in OEM format
        :param outputFormat:
        :return:
        """
        assert (self.formatedData is not None)
        return self.formatedData.getOEM(self.nameBody)

    def getVisibility(self):
        """
        return Visibiity to the asked format
        :return:
        """
        assert (self.visibilityMatrice is not None)
        return self.visibilityMatrice

    def saveJsonFile(self, data, jsonFileName):
        """
        Save a dictionary into a json file
        :param dictTionary:
        :param jsonFile:
        :return:
        """
        with open(jsonFileName + '.json', 'w') as fp:
            json.dump(data, fp, sort_keys=True, indent=4)

if __name__ == "__main__":
    import time
    from pprint import pprint
    # Init orekit

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
    #
    # cayenne = {
    #     "name": "cayenne",
    #     "latitude": 4.5,
    #     "longitude": -52.9,
    #     "altitude": 0,
    #     "elevation": 12
    # }

    # mySuperStation2 = {
    #     "name": "TERRA-INCONITA",
    #     "latitude": 44,
    #     "longitude": 22,
    #     "altitude": 800,
    #     "elevation": 9
    # }

    start = time.time()

    #Init time of the mission analysis ( initial date, step between propagation, and duration)
    myPropagation = HAL_MissionAnalysis(1, "2019-02-22T18:40:00Z", 'EARTH')
    myPropagation.setStartTime("2019-02-22T18:30:00Z")

    #Add my ground station
    myPropagation.addGroundStation(isae)
    #myPropagation.addGroundStation(cayenne)

    #Add Satellites
    # myPropagation.addSatellite(mySatelliteTLE)
    myPropagation.addSatellite(mySatelliteCartesian)
    myPropagation.addSatellite(mySatelliteKeplerian)

    # Propagate
    myPropagation.propagate()

    end = time.time()

    print("Execution time : "+ str(round(end-start, 3)) )

    #Get Result
    #pprint(myPropagation.lupinArray)
    #myPropagation.saveJsonFile(myPropagation.getJSONEphemerids(), 'data')
    pprint(myPropagation.getJSONEphemerids())
    #print(myPropagation.getOEMEphemerids())
    # pprint(myPropagation.getVisibility())
    #myPropagation.getEclipse()
