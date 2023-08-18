package fr.isae.supaero.nanostar;/* Copyright 2002-2018 CS Systèmes d'Information
 * Licensed to CS Systèmes d'Information (CS) under one or more
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

import java.util.*;

import org.hipparchus.geometry.euclidean.threed.RotationOrder;
import org.hipparchus.geometry.euclidean.threed.Vector3D;
import org.hipparchus.util.FastMath;

import org.hipparchus.util.Pair;
import org.orekit.attitudes.AttitudeProvider;
import org.orekit.attitudes.AttitudesSequence;
import org.orekit.attitudes.LofOffset;
import org.orekit.bodies.CelestialBodyFactory;
import org.orekit.errors.OrekitException;
import org.orekit.frames.FramesFactory;
import org.orekit.frames.LOFType;
import org.orekit.orbits.CartesianOrbit;
import org.orekit.orbits.KeplerianOrbit;
import org.orekit.orbits.Orbit;
import org.orekit.orbits.PositionAngle;
import org.orekit.propagation.Propagator;
import org.orekit.propagation.SpacecraftState;
import org.orekit.propagation.analytical.KeplerianPropagator;
import org.orekit.propagation.events.EclipseDetector;
import org.orekit.propagation.events.EventDetector;
import org.orekit.propagation.events.handlers.ContinueOnEvent;
import org.orekit.time.AbsoluteDate;
import org.orekit.time.TimeScalesFactory;
import org.orekit.utils.AngularDerivativesFilter;
import org.orekit.utils.Constants;
import org.orekit.utils.PVCoordinates;
import org.orekit.utils.PVCoordinatesProvider;

/** Orekit tutorial for Earth observation attitude sequence.
 * <p>This tutorial shows how to easily switch between day and night attitude modes.<p>
 * @author Luc Maisonobe
 */
public class EclipseCalculator {

    /** Program entry point.
     * @param args program arguments (unused here)
     */

    private double duration;
    private AbsoluteDate date;
    private Orbit orbit;
    private double mu =  3.986004415e+14;
    private final List<Pair<AbsoluteDate, Boolean>> output = new ArrayList<Pair<AbsoluteDate, Boolean>>();
//    private final SortedSet<String> output;

    /**
     *
     * @param kepOrCartPos position cartesian or keplerian
     * @param initialDate UTC date
     */
    public EclipseCalculator(HAL_SatPos kepOrCartPos, Date initialDate, double duration){ ;
        this.duration = duration;
        this.date = new AbsoluteDate(initialDate.getYear()+1900, initialDate.getMonth()+1,
                initialDate.getDate(), initialDate.getHours(), initialDate.getMinutes(), initialDate.getSeconds(),
                TimeScalesFactory.getUTC());
        if(kepOrCartPos.getType() == "keplerian"){
            this.orbit = new KeplerianOrbit(kepOrCartPos.param1, kepOrCartPos.param2, kepOrCartPos.param3,
                    kepOrCartPos.param4, kepOrCartPos.param5, kepOrCartPos.param6, PositionAngle.MEAN,
                    FramesFactory.getEME2000(), this.date , mu);
        }else if(kepOrCartPos.getType() == "cartesian"){
            Vector3D pos = new Vector3D(kepOrCartPos.param1, kepOrCartPos.param2, kepOrCartPos.param3);
            Vector3D speed = new Vector3D(kepOrCartPos.param4, kepOrCartPos.param5, kepOrCartPos.param6);
            this.orbit = new CartesianOrbit(new PVCoordinates(pos, speed), FramesFactory.getEME2000(), this.date, mu);
        }
    }
    public List<Pair<AbsoluteDate, AbsoluteDate>> getEclipse() throws Exception {

        try {

            // Attitudes sequence definition
            final AttitudeProvider dayObservationLaw = new LofOffset(this.orbit.getFrame(), LOFType.VVLH,
                    RotationOrder.XYZ, FastMath.toRadians(20), FastMath.toRadians(40), 0);
            final AttitudeProvider nightRestingLaw   = new LofOffset(this.orbit.getFrame(), LOFType.VVLH);
            final PVCoordinatesProvider sun = CelestialBodyFactory.getSun();
            final PVCoordinatesProvider earth = CelestialBodyFactory.getEarth();

            // Creation des events trigger
            final EventDetector dayNightEvent =
                    new EclipseDetector(sun, 696000000., earth, Constants.WGS84_EARTH_EQUATORIAL_RADIUS).
                            withHandler(new ContinueOnEvent<EclipseDetector>());
            final EventDetector nightDayEvent =
                    new EclipseDetector(sun, 696000000., earth, Constants.WGS84_EARTH_EQUATORIAL_RADIUS).
                            withHandler(new ContinueOnEvent<EclipseDetector>());

            final AttitudesSequence attitudesSequence = new AttitudesSequence();

            final AttitudesSequence.SwitchHandler switchHandler =
                    new AttitudesSequence.SwitchHandler() {
                        public void switchOccurred(AttitudeProvider preceding, AttitudeProvider following,
                                                   SpacecraftState s) {
                            if (preceding == dayObservationLaw) {
                                output.add(new Pair(s.getDate(), true));
                            } else {
                                output.add(new Pair(s.getDate(), false));
                            }
                        }
                    };

            // Add the switchHandler as callback
            attitudesSequence.addSwitchingCondition(dayObservationLaw, nightRestingLaw, dayNightEvent,
                    false, true, 10.0,
                    AngularDerivativesFilter.USE_R, switchHandler);
            attitudesSequence.addSwitchingCondition(nightRestingLaw, dayObservationLaw, nightDayEvent,
                    true, false, 10.0,
                    AngularDerivativesFilter.USE_R, switchHandler);
            if (dayNightEvent.g(new SpacecraftState(this.orbit)) >= 0) {
                attitudesSequence.resetActiveProvider(dayObservationLaw);
            } else {
                attitudesSequence.resetActiveProvider(nightRestingLaw);
            }

            final Propagator propagator = new KeplerianPropagator(this.orbit, attitudesSequence);

            attitudesSequence.registerSwitchEvents(propagator);

            propagator.propagate(this.date.shiftedBy(this.duration));
        } catch (OrekitException oe) {
            System.err.println(oe.getMessage());
        }

        List<Pair<AbsoluteDate, AbsoluteDate>> result = new ArrayList<Pair<AbsoluteDate, AbsoluteDate>>();
        AbsoluteDate tempTrueDate = null;
        for( Pair<AbsoluteDate, Boolean> el : this.output) {
            if(el.getValue() == true){
                tempTrueDate= el.getKey();
            }else{
                if(tempTrueDate != null ){
                    result.add(new Pair<AbsoluteDate, AbsoluteDate>(tempTrueDate, el.getKey()));
                }
            }
        }
        return result;
    }
}