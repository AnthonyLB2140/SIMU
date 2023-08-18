package fr.isae.supaero.nanostar;

import org.hipparchus.util.Pair;
import org.json.simple.JSONArray;
import org.orekit.data.DataProvidersManager;
import org.orekit.data.DirectoryCrawler;
import org.orekit.time.AbsoluteDate;

import java.io.File;
import java.text.SimpleDateFormat;
import java.util.List;

import org.json.simple.JSONObject;
import org.json.simple.parser.*;

import static spark.Spark.*;

public class
RestifiedEclipseCalculator {
    public static void main(String[] args) {

        options("/*",
                (request, response) -> {

                    String accessControlRequestHeaders = request
                            .headers("Access-Control-Request-Headers");
                    if (accessControlRequestHeaders != null) {
                        response.header("Access-Control-Allow-Headers",
                                accessControlRequestHeaders);
                    }

                    String accessControlRequestMethod = request
                            .headers("Access-Control-Request-Method");
                    if (accessControlRequestMethod != null) {
                        response.header("Access-Control-Allow-Methods",
                                accessControlRequestMethod);
                    }

                    return "OK";
                });
        before((req, res) -> {
            res.header("Access-Control-Allow-Origin", "*");
            res.header("Access-Control-Allow-Headers", "*");
            res.type("application/json");
        });

        File orekitData = new File("./orekit-data");
        DataProvidersManager manager = DataProvidersManager.getInstance();
        manager.addProvider(new DirectoryCrawler(orekitData));

        get("/hello", (req, res)-> {
            return "hello World";
        });

        post("/propagation/eclipses", (req, res) -> {
            String body = req.body();
            SimpleDateFormat formatter = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss");
            try{
                JSONObject jsonInput = (JSONObject)new JSONParser().parse(req.body());
                JSONObject header = (JSONObject)jsonInput.get("header");
                JSONObject sat = (JSONObject)jsonInput.get("satellite");

                String stringDate = header.get("timeStart").toString();
                long duration = (long)header.get("duration");
                String type = sat.get("type").toString();
                if(type.contains("keplerian")){
                    double sma = Double.parseDouble((String) sat.get("sma"));
                    if(sma < 6371000){
                        return error("bad sma value");
                    }
                    double ecc = Double.parseDouble((String) sat.get("ecc"));
                    double inc = Double.parseDouble((String)sat.get("inc"));
                    double pa = Double.parseDouble((String)sat.get("pa"));
                    double raan = Double.parseDouble((String)sat.get("raan"));
                    double lv = Double.parseDouble((String) sat.get("meanAnomaly"));
                    EclipseCalculator calculator = new EclipseCalculator(new HAL_SatPos(sma,ecc,inc,pa,raan,lv, "keplerian"), formatter.parse(stringDate), duration);
                    return (eclipseToJSON(calculator.getEclipse()));
                }else if(type.contains("cartesian")){
                    double x=Double.parseDouble((String) sat.get("x"));
                    double y=Double.parseDouble((String) sat.get("y"));
                    double z=Double.parseDouble((String) sat.get("z"));
                    double vx=Double.parseDouble((String) sat.get("vx"));
                    double vy=Double.parseDouble((String) sat.get("vy"));
                    double vz=Double.parseDouble((String) sat.get("vz"));
                    EclipseCalculator calculator = new EclipseCalculator(new HAL_SatPos(x,y,z,vx,vy,vz, "cartesian"), formatter.parse(stringDate), duration);
                    return (eclipseToJSON(calculator.getEclipse()));
                }else{
                    return error("bad type");
                }
            } catch (Exception e){
                return error(e.toString());
            }
        });
    }

    public static String error(String errorName){
        return "{\"error\": \""+ errorName +"\" }";
    }

    public static JSONArray eclipseToJSON(List<Pair<AbsoluteDate, AbsoluteDate>> eclipse){
        JSONArray eclipseArray = new JSONArray();
//        String result = "[";
        for(Pair<AbsoluteDate, AbsoluteDate> el : eclipse){
//            result+= "{\"start\": \""+el.getKey().toString() + "\"," + "\"end\" :\"" + el.getValue() + "\" },";
            JSONObject obj = new JSONObject();

            obj.put("start", el.getKey().toString());
            obj.put("end", el.getValue().toString());
            eclipseArray.add(obj);
        }
//        result = result.substring(0, result.length() - 1);

//        return result + "]";
        return eclipseArray;
    }
}
