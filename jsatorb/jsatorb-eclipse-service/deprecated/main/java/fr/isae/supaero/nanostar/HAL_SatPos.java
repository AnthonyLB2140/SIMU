package fr.isae.supaero.nanostar;

public class HAL_SatPos {
    String type;
    double param1, param2, param3, param4, param5, param6;

    /**
     *
     * @param param1 sma/position x
     * @param param2 ecc/position y
     * @param param3 inc/position z
     * @param param4 omega / speed x
     * @param param5 raan / speed y
     * @param param6 meanAnomaly / speed z
     * @param type 'keplerian' / 'cartesian'
     */
    HAL_SatPos(double param1, double param2, double param3, double param4, double param5, double param6, String type){
        this.param1 = param1; this.param2 = param2; this.param3 = param3; this.param4 = param4; this.param5= param5;
        this.param6 = param6;
        this.type = type;
    }

    public String getType() {
        return type;
    }

    public void setType(String type) {
        this.type = type;
    }

    public double getParam1() {
        return param1;
    }

    public void setParam1(double param1) {
        this.param1 = param1;
    }

    public double getParam2() {
        return param2;
    }

    public void setParam2(double param2) {
        this.param2 = param2;
    }

    public double getParam3() {
        return param3;
    }

    public void setParam3(double param3) {
        this.param3 = param3;
    }

    public double getParam4() {
        return param4;
    }

    public void setParam4(double param4) {
        this.param4 = param4;
    }

    public double getParam5() {
        return param5;
    }

    public void setParam5(double param5) {
        this.param5 = param5;
    }

    public double getParam6() {
        return param6;
    }

    public void setParam6(double param6) {
        this.param6 = param6;
    }
}
