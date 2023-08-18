import traceback
import unittest
import sys

sys.path.append('src/constellation')
from WalkerConstellation import WalkerConstellation

class TestWalkerConstellation(unittest.TestCase):
    """
    Class that tests if the constellation is correctly generated from the
    given parameters, i.e., if the satellites have the right Keplerian
    coordinates.
    """

    @classmethod
    def setUpClass(cls):
        """
        Generates the constellation before the tests.
        t : number of satellites
        p : number of equally spaced planes
        f : relative spacing between satellites in adjacent planes
        More information can be found on 
        https://en.wikipedia.org/wiki/Satellite_constellation#Walker_Constellation
        """

        argConst = {
            'name': 'myConst',
            'sma': 7000000.,
            'inc': 15.,
            'firstraan': 10.,
            't': 12,
            'p': 3,
            'f': 1
        }

        cls.name = argConst['name']
        cls.sma = argConst['sma']
        cls.inc = argConst['inc']
        cls.firstraan = argConst['firstraan']
        cls.t = argConst['t']
        cls.p = argConst['p']
        cls.f = argConst['f']
        
        walkerConst = WalkerConstellation(argConst)
        cls.satellites = walkerConst.generate()

    def testName(self):
        """
        Checks if the name of each satellite is right
        """

        for i, sat in enumerate(self.satellites):
            self.assertEqual(sat['name'], self.name+'_'+str(i)) 

    def testSMA(self):
        """
        Checks if the semi-major axis of each satellite is the same
        and is right
        """

        for sat in self.satellites:
            self.assertEqual(sat['sma'], self.sma)
    
    def testInc(self):
        """
        Checks if the inclination of each satellite is the same
        and is right
        """

        for sat in self.satellites:
            self.assertEqual(sat['inc'], self.inc)

    def testEcc(self):
        """
        Checks if the eccentricity of each satellite is the same
        and is right
        """

        for sat in self.satellites:
            self.assertEqual(sat['ecc'], 0)

    def testPA(self):
        """
        Checks if the periapsis argument of each satellite is the same
        and is right
        """

        for sat in self.satellites:
            self.assertEqual(sat['pa'], 0)

    def testRAAN(self):
        """
        Checks if the right ascension of the ascending node of each
        satellite is right, given the t and p parameters
        """

        for i, sat in enumerate(self.satellites):
            s = self.t/self.p # Number of sats per plane
            raan = self.firstraan + 360./self.p * (i//s)
            self.assertEqual(sat['raan'], raan)

    def testMeanAnomaly(self):
        """
        Checks if the mean anomaly of each
        satellite is right, given the t, p, and f parameters
        """

        s = self.t/self.p # Number of sats per plane
        for i, sat in enumerate(self.satellites):
            meanAnomaly = self.f*360/self.t*(i//s) + 360./s * (i%s)
            self.assertEqual(sat['meanAnomaly'], meanAnomaly)

if __name__ == '__main__':   
    unittest.main()
