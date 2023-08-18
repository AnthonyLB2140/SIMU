import unittest
import sys

# Add mission analysis module
sys.path.append('src')
from DateConversion import HAL_DateConversion

class TestDateConversion(unittest.TestCase):
    def testDateJD(self):

        # First date test with Julian days
        exampleDateISO = '1977-04-22T01:00:00Z'
        
        expectedDateJD = 2443255.5416667

        newDateJD = HAL_DateConversion(exampleDateISO, 'JD')
        self.assertAlmostEqual(float(newDateJD.getDateTime()['dateConverted']), expectedDateJD)

    def testDateMJD(self):
        # First date test with Modified Julian days
        exampleDateISO = '1977-04-22T01:00:00Z'

        expectedDateMJD = 51544.5 - 8289.4583333

        newDateMJD = HAL_DateConversion(exampleDateISO, 'MJD')
        self.assertAlmostEqual(float(newDateMJD.getDateTime()['dateConverted']), expectedDateMJD)

    def testDateJD2(self):
        # Second date test with Julian days
        exampleDateISO_2 = '2020-08-13T15:05:00'

        expectedDateJD_2 = 2459075.1284722

        newDateJD_2 = HAL_DateConversion(exampleDateISO_2, 'JD')
        self.assertAlmostEqual(float(newDateJD_2.getDateTime()['dateConverted']), expectedDateJD_2)

    def testDateMJD2(self):
        # Second date test with Modified Julian days
        exampleDateISO_2 = '2020-08-13T15:05:00'
    
        expectedDateMJD_2 = 51544.5 + 7530.1284722

        newDateMJD_2 = HAL_DateConversion(exampleDateISO_2, 'MJD')
        self.assertAlmostEqual(float(newDateMJD_2.getDateTime()['dateConverted']), expectedDateMJD_2)

if __name__ == '__main__':
    unittest.main()
