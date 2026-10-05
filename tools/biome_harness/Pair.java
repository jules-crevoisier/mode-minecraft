package harness;
public record Pair<A, B>(A getFirst, B getSecond) {
    public static <A, B> Pair<A, B> of(A a, B b) { return new Pair<>(a, b); }
}
