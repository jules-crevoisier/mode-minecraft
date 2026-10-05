package harness;
public final class Climate {
    public static long quantizeCoord(float c) { return (long) (c * 10000.0F); }
    public static float unquantizeCoord(long c) { return (float) c / 10000.0F; }
    public record Parameter(long min, long max) {
        public static Parameter point(float v) { return span(v, v); }
        public static Parameter span(float a, float b) { return new Parameter(quantizeCoord(a), quantizeCoord(b)); }
        public static Parameter span(Parameter a, Parameter b) { return new Parameter(a.min(), b.max()); }
    }
    public record ParameterPoint(Parameter temperature, Parameter humidity, Parameter continentalness, Parameter erosion,
                                 Parameter depth, Parameter weirdness, long offset) {}
    public static ParameterPoint parameters(Parameter t, Parameter h, Parameter c, Parameter e, Parameter d, Parameter w, float o) {
        return new ParameterPoint(t, h, c, e, d, w, quantizeCoord(o));
    }
}
