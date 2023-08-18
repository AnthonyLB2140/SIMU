import orekit
vm = orekit.initVM()

from datetime import datetime
import traceback
import unittest
import sys

from org.hipparchus.util import FastMath

from org.orekit.time import AbsoluteDate
from org.orekit.time import TimeScalesFactory

sys.path.append('../src')
sys.path.append('src')
from EclipseCalculator import HAL_SatPos, EclipseCalculator
from GitEclipseDetector import gitEclipseDetector

class TestDateConversion(unittest.TestCase):

    tolerance = 1. # in s

    def testEclipseKeplerian(self):
        # Test Keplerian Supaero
        sma, ecc, inc = 7128137.0, 0.007014455530245822, FastMath.toRadians(98.55)
        pa, raan, lv = FastMath.toRadians(90.0), FastMath.toRadians(5.191699999999999), FastMath.toRadians(359.93)
        typeOrbit = 'keplerian'
        dateTimeStringStart = '2011-12-01T16:43:45'
        duration = 86400.
        dateTimeStringEnd = '2011-12-02T16:43:45'

        if typeOrbit == 'keplerian':
            param1, param2, param3 = sma, ecc, inc
            param4, param5, param6 = pa, raan, lv
        elif typeOrbit == 'cartesian':
            param1, param2, param3 = x, y, z
            param4, param5, param6 = vx, vy, vz

        datetimeStart = datetime.fromisoformat(dateTimeStringStart)
        datetimeEnd = datetime.fromisoformat(dateTimeStringEnd)

        try:
            # Git Eclipse
            initialDate =  AbsoluteDate(dateTimeStringStart,TimeScalesFactory.getUTC())
            gitEclipse = gitEclipseDetector(param1, param2, param3, param4, param5,
                param6, typeOrbit, initialDate, duration)

            # JSatOrb Eclipse
            satellite = HAL_SatPos(param1, param2, param3, param4, param5, param6, typeOrbit)
            eclipseCalculator = EclipseCalculator(satellite, datetimeStart, datetimeEnd)
            eclipse = eclipseCalculator.getEclipse()

            listEclipse = []
            for idxElement, element in enumerate(eclipse):
                enteringDate = element[0]
                exitingDate = element[1]
                if idxElement != 0 or not enteringDate.isEqualTo(initialDate):
                    listEclipse.append([enteringDate, 'entering eclipse'])
                if idxElement != len(eclipse)-1 or not exitingDate.isEqualTo(initialDate.shiftedBy(duration)):
                    listEclipse.append([exitingDate, 'exiting eclipse'])

            utcTimeScale = TimeScalesFactory.getUTC()
            maxOffset = 0.
            listOffset = []

            for idxElement, elEclipse in enumerate(listEclipse):
                elGitEclipse = gitEclipse[idxElement]
                self.assertTrue(elEclipse[0].isCloseTo(elGitEclipse[0], self.tolerance))
                self.assertEqual(elEclipse[1], elGitEclipse[1])
            
                offsetCur = abs(elEclipse[0].offsetFrom(elGitEclipse[0], utcTimeScale))
                maxOffset = max(maxOffset, offsetCur)
                listOffset.append(offsetCur)

            #print('Max offset: {} s'.format(maxOffset))
            #print('List of offsets: {}'.format(listOffset))

        except Exception:
            traceback.print_exc()

    def testEclipseCartesian(self):
        # Test Cartesian Supaero
        x, y, z = -6142438.668, 3492467.560, -25767.25680
        vx, vy, vz = 505.8479685, 942.7809215, 7435.922231
        typeOrbit = 'cartesian'
        dateTimeStringStart = '2020-04-03T12:26:11.000'
        duration = 86400.
        dateTimeStringEnd = '2020-04-04T12:26:11.000'


        if typeOrbit == 'keplerian':
            param1, param2, param3 = sma, ecc, inc
            param4, param5, param6 = pa, raan, lv
        elif typeOrbit == 'cartesian':
            param1, param2, param3 = x, y, z
            param4, param5, param6 = vx, vy, vz

        datetimeStart = datetime.fromisoformat(dateTimeStringStart)
        datetimeEnd = datetime.fromisoformat(dateTimeStringEnd)
        try:
            # Git Eclipse
            initialDate =  AbsoluteDate(dateTimeStringStart,TimeScalesFactory.getUTC())
            gitEclipse = gitEclipseDetector(param1, param2, param3, param4, param5,
                param6, typeOrbit, initialDate, duration)

            # JSatOrb Eclipse
            satellite = HAL_SatPos(param1, param2, param3, param4, param5, param6, typeOrbit)
            eclipseCalculator = EclipseCalculator(satellite, datetimeStart, datetimeEnd)
            eclipse = eclipseCalculator.getEclipse()

            listEclipse = []
            for idxElement, element in enumerate(eclipse):
                enteringDate = element[0]
                exitingDate = element[1]
                if idxElement != 0 or not enteringDate.isEqualTo(initialDate):
                    listEclipse.append([enteringDate, 'entering eclipse'])
                if idxElement != len(eclipse)-1 or not exitingDate.isEqualTo(initialDate.shiftedBy(duration)):
                    listEclipse.append([exitingDate, 'exiting eclipse'])

            utcTimeScale = TimeScalesFactory.getUTC()
            maxOffset = 0.
            listOffset = []

            for idxElement, elEclipse in enumerate(listEclipse):
                elGitEclipse = gitEclipse[idxElement]
                self.assertTrue(elEclipse[0].isCloseTo(elGitEclipse[0], self.tolerance))
                self.assertEqual(elEclipse[1], elGitEclipse[1])
            
                offsetCur = abs(elEclipse[0].offsetFrom(elGitEclipse[0], utcTimeScale))
                maxOffset = max(maxOffset, offsetCur)
                listOffset.append(offsetCur)

            #print('Max offset: {} s'.format(maxOffset))
            #print('List of offsets: {}'.format(listOffset))
            
        except Exception:
            traceback.print_exc()


if __name__ == '__main__':
    unittest.main()
