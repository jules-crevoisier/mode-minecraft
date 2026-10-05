package harness;
public class Dump {
    static String p(Climate.Parameter x) { return "[" + Climate.unquantizeCoord(x.min()) + "," + Climate.unquantizeCoord(x.max()) + "]"; }
    public static void main(String[] a) {
        StringBuilder sb = new StringBuilder("[\n");
        new OverworldBiomeBuilder().addBiomes(pair -> {
            Climate.ParameterPoint q = pair.getFirst();
            sb.append("{\"b\":\"").append(pair.getSecond()).append("\",\"t\":").append(p(q.temperature()))
              .append(",\"h\":").append(p(q.humidity())).append(",\"c\":").append(p(q.continentalness()))
              .append(",\"e\":").append(p(q.erosion())).append(",\"d\":").append(p(q.depth()))
              .append(",\"w\":").append(p(q.weirdness())).append(",\"o\":").append(Climate.unquantizeCoord(q.offset())).append("},\n");
        });
        sb.setLength(sb.length() - 2);
        System.out.print(sb.append("\n]\n"));
    }
}
