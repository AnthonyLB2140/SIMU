import orekit
vm = orekit.initVM()

from orekit.pyhelpers import setup_orekit_curdir
setup_orekit_curdir()

import itertools
import numpy as np
from time import time
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import os
import sys

from org.hipparchus.ode.events import Action
from org.hipparchus.util import FastMath
from org.hipparchus.geometry.euclidean.threed import Vector3D

from org.orekit.bodies import OneAxisEllipsoid, CelestialBodyFactory
from org.orekit.frames import FramesFactory
from org.orekit.orbits import KeplerianOrbit, PositionAngle
from org.orekit.propagation import Propagator
from org.orekit.propagation.analytical import KeplerianPropagator
from org.orekit.propagation.analytical.tle import TLE, TLEPropagator
from org.orekit.propagation.events import EventsLogger, GeographicZoneDetector
from org.orekit.propagation.events.handlers import ContinueOnEvent
from org.orekit.propagation.events.handlers import EventHandler, PythonEventHandler
from org.orekit.time import AbsoluteDate, TimeScalesFactory
from org.orekit.utils import IERSConventions, PVCoordinates
from org.orekit.propagation.sampling import OrekitFixedStepHandler, PythonOrekitFixedStepHandler

import sys
sys.path.append('src/')
from ListCelestialBodies import ListCelestialBodies

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


def addTimeRec(timeInterval, timeTable):
    """ Reccursive function to insert a time interval in the time table made of all the 
    previously considered time intervals"""
    if timeInterval[0].compareTo(timeInterval[1]) == 0:
        return timeTable
    for idxCur, timeCur in enumerate(timeTable):
        if timeInterval[0].isBefore(timeCur[0]):
            if timeInterval[1].isBeforeOrEqualTo(timeCur[0]):
                timeTable.insert(idxCur, [timeInterval[0], timeInterval[1], 1])
                return timeTable
            else:
                timeTable.insert(idxCur, [timeInterval[0], timeCur[0], 1])
                return addTimeRec([timeCur[0], timeInterval[1]], timeTable)
        else:
            if timeInterval[0].isBefore(timeCur[1]):
                del timeTable[idxCur]
                timeTable.insert(idxCur, [timeCur[0], timeInterval[0], timeCur[2]])
                if timeInterval[1].isBefore(timeCur[1]):
                    timeTable.insert(idxCur+1,
                        [timeInterval[0], timeInterval[1], timeCur[2]+1])
                    timeTable.insert(idxCur+2,
                        [timeInterval[1], timeCur[1], timeCur[2]])
                    return timeTable
                else:
                    timeTable.insert(idxCur+1,
                        [timeInterval[0], timeCur[1], timeCur[2]+1])
                    return addTimeRec([timeCur[1], timeInterval[1]], timeTable)
    else:
        timeTable.append([timeInterval[0], timeInterval[1], 1])
        return timeTable

class myFixedStepHandler(PythonOrekitFixedStepHandler):
    """ Define custom fixed step handler that calculates which region sees the satellite
    at the current date""" 
    def init(self, s0, t, step):
        pass

    def addData(self, marginAngle, logger, timeStart, timeEnd):
        self.covMatrixOld = np.full(np.shape(logger), False)
        self.marginAngle = marginAngle # in rad
        self.logger = logger
        self.timeStart = timeStart
        self.duration = timeEnd.durationFrom(timeStart)
        self.progressStep = 10
        self.threshold = self.progressStep

    def addBody(self, body, limitsZone, nbLat, nbLong):
        self.body = body
        self.a = body.getEquatorialRadius() # in m
        self.b = self.a*(1-body.getFlattening()) # in m

        latMin, latMax, longMin, longMax = limitsZone # in deg
        stepLat = (latMax-latMin)/nbLat # in deg
        stepLong = (longMax-longMin)/nbLong # in deg

        # Mesh the ellipsoid in latitudes and longitudes
        self.listLatMin = np.deg2rad([[i for j in np.arange(longMin, longMax, stepLong)] for i in np.arange(latMin, latMax, stepLat)])
        self.listLatMax = np.deg2rad([[i+stepLat for j in np.arange(longMin, longMax, stepLong)] for i in np.arange(latMin, latMax, stepLat)])
        self.listLongMin = np.deg2rad([[j for j in np.arange(longMin, longMax, stepLong)] for i in np.arange(latMin, latMax, stepLat)])
        self.listLongMax = np.deg2rad([[j+stepLong for j in np.arange(longMin, longMax, stepLong)] for i in np.arange(latMin, latMax, stepLat)])

    def handleStep(self, currentState, isLast):
        dateCur = currentState.getDate()

        point = self.body.transform(currentState.getPVCoordinates().getPosition(),
            currentState.getFrame(), dateCur)
        satLat = point.getLatitude() # in rad
        satLong = point.getLongitude() # in rad
        satAlt = point.getAltitude() # in m
        
        # Sat coordinates
        ## NLat prime vertical radius of curvature
        NLatSat = self.a**2 / ((self.a*np.cos(satLat))**2 + (self.b*np.sin(satLat))**2)**0.5
        xSat = (NLatSat + satAlt) * np.cos(satLat) * np.cos(satLong)
        ySat = (NLatSat + satAlt) * np.cos(satLat) * np.sin(satLong)
        zSat = ((self.b/self.a)**2*NLatSat + satAlt) * np.sin(satLat)

        # Determine best longitudes, i.e., the closest to the sat longitude
        dLongMin = np.abs(satLong - self.listLongMin)
        dLongMin[dLongMin > np.pi] = 2.*np.pi - dLongMin[dLongMin > np.pi]
        dLongMax = np.abs(satLong - self.listLongMax)
        dLongMax[dLongMax > np.pi] = 2.*np.pi - dLongMin[dLongMax > np.pi]
        ## Find where the sat longitude is in the region
        testLong = np.logical_and(self.listLongMin<satLong, satLong<self.listLongMax)
        ## Choose longitude depending on closest to sat longitude
        Long = np.logical_and(np.logical_not(testLong), dLongMin<dLongMax)*self.listLongMin + testLong*satLong + np.logical_and(np.logical_not(testLong), dLongMin>=dLongMax)*self.listLongMax

        # Determine best latitudes, i.e., the ones where the observer is 
        # closest to the sat
        NLatMin = self.a**2 / ((self.a*np.cos(self.listLatMin))**2 + (self.b*np.sin(self.listLatMin))**2)**0.5
        x0LatMin = NLatMin * np.cos(self.listLatMin) * np.cos(Long)
        y0LatMin = NLatMin * np.cos(self.listLatMin) * np.sin(Long)
        z0LatMin = (self.b/self.a)**2*NLatMin * np.sin(self.listLatMin)
        distLatMin = (xSat-x0LatMin)**2 + (ySat-y0LatMin)**2 + (zSat-z0LatMin)**2

        NLatMax = self.a**2 / ((self.a*np.cos(self.listLatMax))**2 + (self.b*np.sin(self.listLatMax))**2)**0.5
        x0LatMax = NLatMax * np.cos(self.listLatMax) * np.cos(Long)
        y0LatMax = NLatMax * np.cos(self.listLatMax) * np.sin(Long)
        z0LatMax = (self.b/self.a)**2*NLatMax * np.sin(self.listLatMax)
        distLatMax = (xSat-x0LatMax)**2 + (ySat-y0LatMax)**2 + (zSat-z0LatMax)**2

        ## Find where the sat latitude is in the region
        testLat = np.logical_and(self.listLatMin<satLat, satLat<self.listLatMax)
        ## Choose latitude depending on closest distance
        Lat = np.logical_and(np.logical_not(testLat), distLatMin<=distLatMax)*self.listLatMin + testLat*satLat + np.logical_and(np.logical_not(testLat), distLatMin>distLatMax)*self.listLatMax

        # Compute positions
        NLat = self.a**2 / ((self.a*np.cos(Lat))**2 + (self.b*np.sin(Lat))**2)**0.5
        x0 = NLat * np.cos(Lat) * np.cos(Long)
        y0 = NLat * np.cos(Lat) * np.sin(Long)
        z0 = (self.b/self.a)**2*NLat * np.sin(Lat)

        # Find alpha angle between normal vector and satellite direction
        scalar_product = (x0*xSat + y0*ySat + (self.a/self.b)**2 * z0*zSat - self.a**2) / NLat
        norms = ((xSat-x0)**2 + (ySat-y0)**2 + (zSat-z0)**2)**0.5
        
        ## Considers only minimum between 1 and cos(alpha) to avoid cos slightly greater
        ## than 1 due to rounding
        alpha = np.arccos(np.minimum(np.ones(np.shape(Lat)), scalar_product / norms))

        # Compute coverage matrix
        covMatrixCur = alpha<self.marginAngle

        # Compare with previous state
        idxsStart = np.nonzero(np.logical_and(np.logical_not(self.covMatrixOld), covMatrixCur))
        idxsEnd = np.nonzero(np.logical_and(np.logical_not(covMatrixCur), self.covMatrixOld))

        for idxLat, idxLong in np.column_stack(idxsStart):
            self.logger[idxLat, idxLong].append([True, dateCur])

        for idxLat, idxLong in np.column_stack(idxsEnd):
            self.logger[idxLat, idxLong].append([False, dateCur])

        self.covMatrixOld = covMatrixCur

        # Print progress
        percentProgress = 1e2 * dateCur.durationFrom(self.timeStart) / self.duration
        if percentProgress > self.threshold:
            progress = percentProgress//self.progressStep*self.progressStep
            #sys.stdout.write("\r")
            #sys.stdout.write("Propagation: {}%".format(progress))
            print("Propagation: {}%".format(progress))
            self.threshold = progress + self.progressStep
            #sys.stdout.flush()

class CoverageAnalysis:
    """ Class that generates the handler to compute coverage and propagate. 
    One propagation has to be done for each satellite, and coverage data are 
    updated each propagation."""

    def __init__(self, timeStart, timeEnd, step, minElev, nbNeededSats):
        utc = TimeScalesFactory.getUTC()
        self.initialDate = AbsoluteDate(timeStart, utc)
        self.endDate = AbsoluteDate(timeEnd, utc)
        if self.endDate.compareTo(self.initialDate) < 0:
            raise ValueError("End date before start date")

        self.timeStep = step 
        self.marginAngle = FastMath.toRadians(90. - minElev)
        self.nbNeededSats = nbNeededSats

    def setBody(self, bodyString):
        # Body Frame and Body
        celestialBody = CelestialBodyFactory.getBody(bodyString.upper())
        if bodyString.upper() == 'EARTH':
            bodyFrame = FramesFactory.getITRF(IERSConventions.IERS_2010, True)
            self.inertialFrame = FramesFactory.getEME2000()
        else:
            bodyFrame = celestialBody.getBodyOrientedFrame()
            self.inertialFrame = celestialBody.getInertiallyOrientedFrame()

        celestialBodyShape = ListCelestialBodies.getBody(bodyString.upper())
        radiusBody = celestialBodyShape.radius
        flatBody = celestialBodyShape.flattening
        self.body = OneAxisEllipsoid(radiusBody, flatBody, bodyFrame)
        self.mu = celestialBody.getGM()
    
    def setLimitZone(self, limitsZone, nbLat, nbLong):
        self.limitsZone = limitsZone
        self.nbLat = nbLat
        self.nbLong = nbLong

        self.timeTables = np.empty([self.nbLat, self.nbLong], object)
        for idxs in itertools.product(range(self.nbLat), range(self.nbLong)):
            self.timeTables[idxs] = []

    def propagate(self, sat):
        # Set satellite
        if(sat["type"] == "keplerian"):
            orbit = KeplerianOrbit(float(sat["sma"]), float(sat["ecc"]),
                FastMath.toRadians(float(sat["inc"])), FastMath.toRadians(float(sat["pa"])),
                FastMath.toRadians(float(sat["raan"])), FastMath.toRadians(float(sat["meanAnomaly"])),
                PositionAngle.MEAN, self.inertialFrame, self.initialDate, self.mu)
            propagator = KeplerianPropagator(orbit)

        elif(sat["type"] == "cartesian"):
            position = Vector3D(float(sat["x"]), float(sat["y"]), float(sat["z"]))
            velocity = Vector3D(float(sat["vx"]), float(sat["vy"]), float(sat["vz"]))
            orbit = KeplerianOrbit(PVCoordinates(position, velocity), self.inertialFrame,
                self.initialDate, self.mu)
            propagator = KeplerianPropagator(orbit)

        elif(sat["type"] == "tle"):
            orbit = TLE(sat["line1"], sat["line2"])
            propagator = TLEPropagator.selectExtrapolator(orbit)

        # Check if satellite outside central body
        WarningSMA(sat["type"], orbit, self.body, self.mu)
                
        handlerCov = myFixedStepHandler()
        self.logger = np.empty([self.nbLat, self.nbLong], object)
        for idxs in itertools.product(range(self.nbLat), range(self.nbLong)):
            self.logger[idxs] = []

        handlerCov.addData(self.marginAngle, self.logger, self.initialDate,
            self.endDate)
        handlerCov.addBody(self.body, self.limitsZone, self.nbLat, self.nbLong)
        propagator.setMasterMode(self.timeStep, handlerCov)
    
        # Propagation with the custom handler
        #sys.stdout.write("Propagation: 0.0%")
        print("Propagation: 0.0%")
        propagator.propagate(self.initialDate, self.endDate)
        #sys.stdout.write("\r")
        #sys.stdout.write("Propagation: 100.0%\n")
        print("Propagation: 100.0%")
        #sys.stdout.flush()
        
        # Fill the time tables with the events in the logger
        for idxs in itertools.product(range(self.nbLat), range(self.nbLong)):
            for i, event in enumerate(self.logger[idxs]):
                if event[0]:
                    startTime = event[1]
                    if i == len(self.logger[idxs])-1:
                        stopTime = self.endDate
                        self.timeTables[idxs] = addTimeRec([startTime, stopTime], self.timeTables[idxs])
                else:
                    stopTime = event[1]
                    if i == 0: startTime = self.initialDate
                    self.timeTables[idxs] = addTimeRec([startTime, stopTime], self.timeTables[idxs])
        #time_end = time()
        #print("After time management: duration {}".format(time_end-time_start))

    def getTypeData(self, typeData):
        switcher = {
            "PERCENT_COV": self.percentCoverage,
            "TIME_AV_GAP": self.timeAverageGap,
            "MAX_GAP": self.maxGap,
            "MEAN_GAP": self.meanGap,
            "MEAN_RESP_TIME": self.meanResponseTime
        }
        return switcher[typeData]()

    def saveTypeData(self, typeData, pathFile):
        data = self.getTypeData(typeData)
        
        minData, maxData = (np.min(data), np.max(data))

        typeProperties = {
            "PERCENT_COV": {"name": "Percent Coverage", "min": "{} %".format(np.around(100*minData,2)), "max": "{} %".format(np.around(100*maxData,2))},
            "TIME_AV_GAP":{"name": "Time Average Gap", "min": "{} s".format(np.around(minData,2)), "max": "{} s".format(np.around(maxData,2))},
            "MAX_GAP": {"name": "Maximum Gap", "min": "{} s".format(np.around(minData,2)), "max": "{} s".format(np.around(maxData,2))},
            "MEAN_GAP": {"name": "Mean Coverage Gap", "min": "{} s".format(np.around(minData,2)), "max": "{} s".format(np.around(maxData,2))},
            "MEAN_RESP_TIME": {"name": "Mean Response Time", "min": "{} s".format(np.around(minData,2)), "max": "{} s".format(np.around(maxData,2))}
        }
        properties = typeProperties[typeData]

        if np.any(np.isnan(data)):
            raise ValueError("NaN elements in array")

        latMin, latMax, longMin, longMax = self.limitsZone # in deg
        stepLat = (latMax-latMin)/self.nbLat # in deg
        stepLong = (longMax-longMin)/self.nbLong # in deg

        ## Latitudes and longitudes of middles of regions, for histogram
        listLatMid = np.array([[i+stepLat/2 for j in np.arange(-180, 180, stepLong)] for i in np.arange(-90, 90, stepLat)])
        listLongMid = np.array([[j+stepLong/2 for j in np.arange(-180, 180, stepLong)] for i in np.arange(-90, 90, stepLat)])

        dataLarge = np.full(np.shape(listLatMid), -np.inf)
        idxLatMin, idxLatMax = ( int((latMin+90)/stepLat), int((latMax+90)/stepLat) )
        idxLongMin, idxLongMax = ( int((longMin+180)/stepLat), int((longMax+180)/stepLong) ) 

        dataLarge[idxLatMin:idxLatMax, idxLongMin:idxLongMax] = data

        nbBinsHist = (360, 180)
        rangeHist = ((-180, 180), (-90, 90))

        nameFile = pathFile + typeData + '.png'

        fig = plt.figure(0, frameon=False)
        fig.set_size_inches(10,5)
        ax = plt.Axes(fig, [0., 0., 1., 1.])
        ax.set_axis_off()
        fig.add_axes(ax)

        plt.hist2d(listLongMid.flatten(), listLatMid.flatten(), bins=nbBinsHist, range=rangeHist, weights=dataLarge.flatten(), cmin=minData)
        plt.axis('scaled')
        # Write colorbar inside the image
        plt.text(-180, 84, properties["name"], bbox=dict(facecolor = 'white', linewidth=0))
        plt.text(-85, -85, properties["min"], bbox=dict(facecolor = 'white', linewidth=0))
        plt.text(60, -85, properties["max"], bbox=dict(facecolor='white', linewidth=0))

        cbaxes = inset_axes(ax, width="30%", height="4%", loc='lower center') 
        plt.colorbar(cax=cbaxes, ticks=[0.,1], orientation='horizontal')
        
        # Remove file if exits, before saving
        if os.path.isfile(nameFile):
            os.remove(nameFile)
        
        fig.savefig(nameFile, bbox_inches=0, transparent=True, pad_inches=0)
        plt.close()
        

    def percentCoverage(self):
        percentTime = np.zeros([self.nbLat, self.nbLong])
        for idxs in itertools.product(range(self.nbLat), range(self.nbLong)):
            for timeInterval in self.timeTables[idxs]:
                if timeInterval[2] >= self.nbNeededSats:
                    percentTime[idxs] += timeInterval[1].durationFrom(timeInterval[0])
            percentTime[idxs] /= self.endDate.durationFrom(self.initialDate)

        return percentTime
    
    def timeAverageGap(self):
        timeAverageGaps = np.zeros([self.nbLat, self.nbLong])
        duration = self.endDate.durationFrom(self.initialDate)
        for idxs in itertools.product(range(self.nbLat), range(self.nbLong)):
            squareGapList = []
            startGap = self.initialDate
            for i, timeInterval in enumerate(self.timeTables[idxs]):
                if timeInterval[2] >= self.nbNeededSats:
                    endGap = timeInterval[0]
                    durationGap = endGap.durationFrom(startGap)
                    if durationGap > 0.:
                        squareGapList.append(durationGap**2)
                    startGap = timeInterval[1]
            durationGap = self.endDate.durationFrom(startGap)
            if durationGap > 0.:
                squareGapList.append(durationGap**2)
            timeAverageGaps[idxs] = sum(squareGapList)/duration

        return timeAverageGaps
    
    def maxGap(self):
        maxGaps = np.zeros([self.nbLat, self.nbLong])
        for idxs in itertools.product(range(self.nbLat), range(self.nbLong)):
            startGap = self.initialDate
            for i, timeInterval in enumerate(self.timeTables[idxs]):
                if timeInterval[2] >= self.nbNeededSats:
                    endGap = timeInterval[0]
                    durationGap = endGap.durationFrom(startGap)
                    if durationGap > maxGaps[idxs]: maxGaps[idxs] = durationGap
                    startGap = timeInterval[1]
            durationGap = self.endDate.durationFrom(startGap)
            if durationGap > maxGaps[idxs]: maxGaps[idxs] = durationGap

        return maxGaps

    def meanGap(self):
        meanGaps = np.zeros([self.nbLat, self.nbLong])
        for idxs in itertools.product(range(self.nbLat), range(self.nbLong)):
            meanGapList = []
            startGap = self.initialDate
            for i, timeInterval in enumerate(self.timeTables[idxs]):
                if timeInterval[2] >= self.nbNeededSats:
                    endGap = timeInterval[0]
                    durationGap = endGap.durationFrom(startGap)
                    if durationGap > 0.:
                        meanGapList.append(durationGap)
                    startGap = timeInterval[1]
            durationGap = self.endDate.durationFrom(startGap)
            if durationGap > 0.:
                meanGapList.append(durationGap)
            meanGaps[idxs] = sum(meanGapList)/len(meanGapList)

        return meanGaps

    def meanResponseTime(self):
        meanRespTimes = np.zeros([self.nbLat, self.nbLong])
        duration = self.endDate.durationFrom(self.initialDate)
        """
        nbIte = int(2e3)
        #nbIte = int(10)
    
        respTimeArray = np.empty([self.nbLat, self.nbLong], object)
        for idxs in itertools.product(range(self.nbLat), range(self.nbLong)):
            respTimeArray[idxs] = []

        for i in range(nbIte):
            dateEmission = self.initialDate.shiftedBy(np.random.rand()*duration)
            for idxs in itertools.product(range(self.nbLat), range(self.nbLong)):
                for timeInterval in self.timeTables[idxs]:
                    if timeInterval[2] >= self.nbNeededSats:
                        if dateEmission.isBeforeOrEqualTo(timeInterval[0]):
                            respTimeArray[idxs].append(timeInterval[0].durationFrom(dateEmission))
                            break
                        elif dateEmission.isBeforeOrEqualTo(timeInterval[1]):
                            respTimeArray[idxs].append(0.)
                            break
                else:
                    respTimeArray[idxs].append(self.endDate.durationFrom(dateEmission))
        
        for idxs in itertools.product(range(self.nbLat), range(self.nbLong)):
            meanRespTimes[idxs] = np.mean(respTimeArray[idxs])
        """

        # Alternative mean response time
        for idxs in itertools.product(range(self.nbLat), range(self.nbLong)):
            meanRespTimeList = []
            startGap = self.initialDate
            for i, timeInterval in enumerate(self.timeTables[idxs]):
                if timeInterval[2] >= self.nbNeededSats:
                    endGap = timeInterval[0]
                    durationGap = endGap.durationFrom(startGap)
                    if durationGap > 0.:
                        meanRespTimeList.append(0.5*durationGap**2)
                    startGap = timeInterval[1]
            durationGap = self.endDate.durationFrom(startGap)
            if durationGap > 0.:
                meanRespTimeList.append(0.5*durationGap**2)
            meanRespTimes[idxs] = sum(meanRespTimeList)/duration

        return meanRespTimes
        