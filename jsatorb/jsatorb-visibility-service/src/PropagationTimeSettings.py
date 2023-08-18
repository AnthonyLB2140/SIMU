# Original author: ISAE, continued by CS Group

import orekit
vm = orekit.initVM()

from orekit.pyhelpers import setup_orekit_curdir
setup_orekit_curdir()
from datetime import datetime
from org.orekit.time import TimeScalesFactory, AbsoluteDate, DateComponents, TimeComponents


class PropagationTimeSettings:
    """
    Class that permit to propagate TLE, KEPLERIAN, CARTESIAN Satellite position to RETURN :
    ephemerids (on a JSON format or CCSDS file)
    visibility if ground station has been added
    """

    def __init__(self, timeStep, endDateString):
        #Initiate Date

        self.utc = TimeScalesFactory.getUTC()

        #self.absoluteStartTime = AbsoluteDate(startingTime, self.utc)
        self.timeStep = float(timeStep)
        self.absoluteEndTime = AbsoluteDate(endDateString, self.utc)

    def setStartTime(self, stringUTCDate):
        self.absoluteStartTime = AbsoluteDate(stringUTCDate, self.utc)

    def setEndingDate(self, stringUTCDate):
        """
        Set propagation datetime end
        datetime is in the UTC format
        :param absoluteDate:
        :return:
        """
        self.absoluteEndTime = AbsoluteDate(stringUTCDate, self.utc)

    def setStepTimeBetweenPropagation(self, secNumberStepTime):
        """
        Set time betwen 2 propagations steps
        The time is in seconds
        :param intStepNumber:
        :return:
        """
        self.timeStep = float(secNumberStepTime)

    @staticmethod
    def absDate2datetime(absdate):
        dateTimeComponents = absdate.getComponents(TimeScalesFactory.getUTC())
        dateComp = dateTimeComponents.getDate()
        timeComp = dateTimeComponents.getTime()
        return datetime(dateComp.getYear(), dateComp.getMonth(), dateComp.getDay(), timeComp.getHour(),
                        timeComp.getMinute(), int(timeComp.getSecond()))

    @staticmethod
    def absDate2ISOString(absdate):
        dateTimeComponents = absdate.getComponents(TimeScalesFactory.getUTC())
        dateComp = dateTimeComponents.getDate()
        timeComp = dateTimeComponents.getTime()
        temp = datetime(dateComp.getYear(), dateComp.getMonth(), dateComp.getDay(), timeComp.getHour(),
                        timeComp.getMinute(), int(timeComp.getSecond()))
        return temp.isoformat() + 'Z'

    def setPropagationDuration(self, intDuration):
        """Set propagation duration
        """
        self.absoluteEndTime = self.absoluteStartTime.shiftedBy(float(intDuration))

