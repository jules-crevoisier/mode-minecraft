package com.wayfarers.release;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * A mod version, read the semantic-versioning way: {@code 0.9.0-beta.2+build.84} is the core {@code 0.9.0}, the
 * pre-release {@code beta.2} and the build metadata {@code build.84}. Ordering ignores build metadata (a CI build of
 * 0.9.0-beta is the same release as 0.9.0-beta), and a pre-release comes before its final version
 * (0.9.0-beta &lt; 0.9.0-rc.1 &lt; 0.9.0 &lt; 0.9.1-beta). A leading "v" (a git tag) is accepted.
 */
public final class ModVersion implements Comparable<ModVersion> {
    private final String text;
    private final int[] core;
    private final List<String> pre;
    private final String build;

    private ModVersion(String text, int[] core, List<String> pre, String build) {
        this.text = text;
        this.core = core;
        this.pre = pre;
        this.build = build;
    }

    public static ModVersion parse(String s) {
        String t = s == null ? "" : s.trim();
        if (t.startsWith("v") || t.startsWith("V")) {
            t = t.substring(1);
        }
        String build = "";
        int plus = t.indexOf('+');
        if (plus >= 0) {
            build = t.substring(plus + 1);
            t = t.substring(0, plus);
        }
        List<String> pre = new ArrayList<>();
        int dash = t.indexOf('-');
        if (dash >= 0) {
            for (String p : t.substring(dash + 1).split("[.\\-]")) {
                if (!p.isEmpty()) {
                    pre.add(p.toLowerCase(Locale.ROOT));
                }
            }
            t = t.substring(0, dash);
        }
        String[] parts = t.split("\\.");
        int[] core = new int[Math.max(3, parts.length)];
        for (int i = 0; i < parts.length; i++) {
            core[i] = leadingInt(parts[i]);
        }
        return new ModVersion(s == null ? "" : s.trim(), core, List.copyOf(pre), build);
    }

    private static int leadingInt(String s) {
        int n = 0;
        for (int i = 0; i < s.length() && Character.isDigit(s.charAt(i)) && n < 100_000_000; i++) {
            n = n * 10 + (s.charAt(i) - '0');
        }
        return n;
    }

    /** True for a CI development build (it carries build metadata). */
    public boolean isDevBuild() {
        return !build.isEmpty();
    }

    public boolean isPreRelease() {
        return !pre.isEmpty();
    }

    @Override
    public int compareTo(ModVersion o) {
        int n = Math.max(core.length, o.core.length);
        for (int i = 0; i < n; i++) {
            int a = i < core.length ? core[i] : 0;
            int b = i < o.core.length ? o.core[i] : 0;
            if (a != b) {
                return Integer.compare(a, b);
            }
        }
        if (pre.isEmpty() || o.pre.isEmpty()) {
            return Boolean.compare(pre.isEmpty(), o.pre.isEmpty());
        }
        for (int i = 0; i < Math.min(pre.size(), o.pre.size()); i++) {
            int c = compareIdentifier(pre.get(i), o.pre.get(i));
            if (c != 0) {
                return c;
            }
        }
        return Integer.compare(pre.size(), o.pre.size());
    }

    private static int compareIdentifier(String a, String b) {
        boolean na = !a.isEmpty() && a.chars().allMatch(Character::isDigit);
        boolean nb = !b.isEmpty() && b.chars().allMatch(Character::isDigit);
        if (na && nb) {
            return Long.compare(Long.parseLong(a.length() > 18 ? a.substring(0, 18) : a),
                    Long.parseLong(b.length() > 18 ? b.substring(0, 18) : b));
        }
        if (na != nb) {
            return na ? -1 : 1;
        }
        return a.compareTo(b);
    }

    public boolean isNewerThan(ModVersion o) {
        return compareTo(o) > 0;
    }

    @Override
    public String toString() {
        return text;
    }
}
