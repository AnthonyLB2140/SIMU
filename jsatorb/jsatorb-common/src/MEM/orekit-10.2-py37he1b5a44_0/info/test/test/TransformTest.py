# -*- coding: utf-8 -*-

"""

/* Copyright 2002-2019 CS Syst��mes d'Information
 * Licensed to CS Syst��mes d'Information (CS) under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * CS licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

Python version translated from Java by Petrus Hyvönen, SSC 2019

 """

import orekit

orekit.initVM()
from orekit.pyhelpers import setup_orekit_curdir, datetime_to_absolutedate

setup_orekit_curdir()

from org.orekit.time import AbsoluteDate
import unittest
import sys
from datetime import datetime

from java.util import ArrayList
# import java.util.List;
#
# import org.hipparchus.Field;
# import org.hipparchus.geometry.euclidean.threed.FieldVector3D;
# import org.hipparchus.geometry.euclidean.threed.Line;
from org.hipparchus.geometry.euclidean.threed import Rotation;
from org.hipparchus.geometry.euclidean.threed import RotationConvention;
from org.hipparchus.geometry.euclidean.threed import Vector3D
# import org.hipparchus.linear.MatrixUtils;
# import org.hipparchus.linear.RealMatrix;
# import org.hipparchus.random.RandomGenerator;
# import org.hipparchus.random.Well19937a;
# import org.hipparchus.util.Decimal64;
# import org.hipparchus.util.Decimal64Field;
from org.hipparchus.util import FastMath
# import org.junit.Assert;
# import org.junit.Test;
# import org.orekit.Utils;
# import org.orekit.time.AbsoluteDate;
# import org.orekit.time.FieldAbsoluteDate;
# import org.orekit.time.TimeScale;
# import org.orekit.time.TimeScalesFactory;
from org.orekit.utils import CartesianDerivativesFilter
# import org.orekit.utils.Constants;
# import org.orekit.utils.FieldPVCoordinates;
from org.orekit.utils import PVCoordinates
# import org.orekit.utils.TimeStampedFieldPVCoordinates;
from org.orekit.utils import TimeStampedPVCoordinates;
from org.orekit.frames import Transform
from org.orekit.frames import FramesFactory

# # ADDED CODE BEGIN
from org.orekit.data import DataProvidersManager, ZipJarCrawler
from java.io import File
from java.lang import System
# # ADDED CODE END

class TransformTest(unittest.TestCase):

# #### ADDED CODE BEGIN
    def setUp(self):
        DM = DataProvidersManager.getInstance()

        print("Providers in setup, before reset: ")
        for provider in DataProvidersManager.getInstance().getProviders():
            print("-" + provider.toString())
        print("Loaded data names in setup, before reset: ")
        for name in DataProvidersManager.getInstance().getLoadedDataNames():
            print("-" + name)

        datafile = File('orekit-data.zip')
        if not datafile.exists():
            print('File :', datafile.absolutePath, ' not found')

        crawler = ZipJarCrawler(datafile)
        DM.clearProviders()
        DM.addProvider(crawler)
        System.setProperty(DataProvidersManager.OREKIT_DATA_PATH, 'potential/shm-format')

        print("Providers after setup reset: ")
        for provider in DataProvidersManager.getInstance().getProviders():
            print("-" + provider.toString())
        print("Loaded data names after setup reset: ")
        for name in DataProvidersManager.getInstance().getLoadedDataNames():
            print("-" + name)

        print("Setup done")

    def tearDown(self):
        DM = DataProvidersManager.getInstance()

        print("Providers in tearDown: ")
        for provider in DataProvidersManager.getInstance().getProviders():
            print("-" + provider.toString())
        print("Loaded data names in tearDown: ")
        for name in DataProvidersManager.getInstance().getLoadedDataNames():
            print("-" + name)
#### ADDED CODE END

    def testPythonTransformType(self):
        # Create initial TimeStampedPVCoordinates
        pos = Vector3D(10000., 20000., 30000.)
        vel = Vector3D(2000., 1000., 1500.)
        date = datetime_to_absolutedate(datetime(2019, 3, 13))
        pvt1 = TimeStampedPVCoordinates(date, pos, vel)
        print(type(pvt1))

        # Create transform
        eme2000 = FramesFactory.getEME2000()
        icrf = FramesFactory.getICRF()
        transform = eme2000.getTransformTo(icrf, date)

        # Transform the TimeStampedPVCoordinates
        pvt2 = transform.transformPVCoordinates(pvt1)
        print(type(pvt2))
        # TimeStampedPVCoordinates.cast_(pvt2)
        assert type(pvt2) == type(pvt1)

    def evolvingTransform(self, t0, dt):

        # the following transform corresponds to a frame moving along the circle r = 1
        # with its x axis always pointing to the reference frame center
        omega = 0.2;
        date = t0.shiftedBy(dt);
        cos = FastMath.cos(omega * dt);
        sin = FastMath.sin(omega * dt);
        return Transform(date,
                         Transform(date,
                                   Vector3D(-cos, -sin, 0.0),
                                   Vector3D(omega * sin, -omega * cos, 0.0),
                                   Vector3D(omega * omega * cos, omega * omega * sin, 0.0)),
                         Transform(date,
                                   Rotation(Vector3D.PLUS_K, FastMath.PI - omega * dt,
                                            RotationConvention.VECTOR_OPERATOR),
                                   Vector3D(omega, Vector3D.PLUS_K)));

    def checkVector(self, reference, result, relativeTolerance):

        refNorm = reference.getNorm()
        resNorm = result.getNorm()
        tolerance = relativeTolerance * (1 + FastMath.max(refNorm, resNorm))

        assert -tolerance < Vector3D.distance(reference, result) < tolerance

        # uassertEquals("ref = " + reference + ", res = " + result + " -> " +
        #                    (Vector3D.distance(reference, result) / (1 + FastMath.max(refNorm, resNorm))),
        #                    0, Vector3D.distance(reference, result), tolerance);

    def testAcceleration(self):
        initPV = PVCoordinates(Vector3D(9.0, 8.0, 7.0), Vector3D(6.0, 5.0, 4.0), Vector3D(3.0, 2.0, 1.0))
        dt = 0.0
        while dt < 1:
            basePV = initPV.shiftedBy(dt)
            transformedPV = self.evolvingTransform(AbsoluteDate.J2000_EPOCH, dt).transformPVCoordinates(basePV)

            # rebuild transformed acceleration, relying only on transformed position and velocity
            sample = ArrayList().of_(TimeStampedPVCoordinates)
            h = 1.0e-2;
            i = -3
            while i < 4:
                t = self.evolvingTransform(AbsoluteDate.J2000_EPOCH, dt + i * h);
                pv = t.transformPVCoordinates(initPV.shiftedBy(dt + i * h))
                item = TimeStampedPVCoordinates(t.getDate(), pv.getPosition(), pv.getVelocity(), Vector3D.ZERO)
                sample.add(item)
                i = i + 1

            rebuiltPV = TimeStampedPVCoordinates.interpolate(AbsoluteDate.J2000_EPOCH.shiftedBy(dt),
                                                             CartesianDerivativesFilter.USE_PV,
                                                             sample)

            self.checkVector(rebuiltPV.getPosition(), transformedPV.getPosition(), 4.0e-16)
            self.checkVector(rebuiltPV.getVelocity(), transformedPV.getVelocity(), 2.0e-16)
            self.checkVector(rebuiltPV.getAcceleration(), transformedPV.getAcceleration(), 9.0e-11)
            dt += 0.01

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TransformTest)
    ret = not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful()
    sys.exit(ret)
