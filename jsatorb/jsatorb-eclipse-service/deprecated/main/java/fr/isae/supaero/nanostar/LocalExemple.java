package fr.isae.supaero.nanostar;

import org.hipparchus.util.FastMath;
import org.orekit.data.DataProvidersManager;
import org.orekit.data.DirectoryCrawler;

import java.io.File;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Date;

public class LocalExemple {

    public static void main(String[] args) throws ParseException {
        File orekitData = new File("./orekit-data");
        DataProvidersManager manager = DataProvidersManager.getInstance();
        manager.addProvider(new DirectoryCrawler(orekitData));

        /*EclipseCalculator eclipseCalculator = new EclipseCalculator(     new HAL_SatPos(7128137,  0.007014455530245822, FastMath.toRadians(98.55),
                FastMath.toRadians(90.0), FastMath.toRadians( 5.191699999999999), 359.93, "keplerian" ), new Date(),86400);
        */
        EclipseCalculator eclipseCalculator = new EclipseCalculator(     new HAL_SatPos(7128137,  0.007014455530245822, FastMath.toRadians(98.55),
                FastMath.toRadians(90.0), FastMath.toRadians( 5.191699999999999), 359.93, "keplerian" ), new Date(2011,12,01,16,43,45),86400);

        try {

            System.out.println(eclipseCalculator.getEclipse());
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

}
