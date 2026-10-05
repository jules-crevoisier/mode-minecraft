package com.brasshaven.release;

import com.brasshaven.Brasshaven;
import net.minecraftforge.fml.ModList;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.Properties;

/**
 * What this jar is: the mod version (gradle.properties {@code mod_version}, plus {@code +build.N} on a CI development
 * build), the network protocol (gradle.properties {@code network_protocol}, bumped only when packets change) and where
 * players download the mod. Gradle writes them into META-INF/brasshaven/build.properties (see build.gradle and
 * docs/PUBLISHING.md).
 */
public final class BuildInfo {
    /** GitHub repository whose releases the update check reads. */
    public static final String REPOSITORY = "jules-crevoisier/mode-minecraft";
    public static final String RELEASES_URL = "https://github.com/" + REPOSITORY + "/releases";

    private static final Properties PROPS = load();

    /** Network protocol of the mod's channel: clients and servers with a different one cannot talk. */
    public static final int PROTOCOL = parseInt(PROPS.getProperty("protocol"), 1);
    /** Where players get the mod (CurseForge page once it exists, else the GitHub releases). */
    public static final String DOWNLOAD_URL = property("download_url", RELEASES_URL);

    private static String version;

    private BuildInfo() {}

    /**
     * The version of the running jar, exactly as Forge reports it to the other side of a connection (mods.toml), so
     * that it compares with the remote mod list.
     */
    public static String version() {
        if (version == null) {
            version = ModList.getModContainerById(Brasshaven.MODID)
                    .map(c -> c.getModInfo().getVersion().toString())
                    .orElseGet(() -> property("version", "0.0.0"));
        }
        return version;
    }

    private static Properties load() {
        Properties p = new Properties();
        try (InputStream in = BuildInfo.class.getResourceAsStream("/META-INF/brasshaven/build.properties")) {
            if (in != null) {
                p.load(new InputStreamReader(in, StandardCharsets.UTF_8));
            }
        } catch (java.io.IOException | RuntimeException e) {
            Brasshaven.LOGGER.debug("Brasshaven: no build info ({})", e.getMessage());
        }
        return p;
    }

    private static String property(String key, String fallback) {
        String v = PROPS.getProperty(key);
        // an unexpanded template (a run straight from the sources) keeps its ${...} placeholder
        return v == null || v.isBlank() || v.contains("${") ? fallback : v.trim();
    }

    private static int parseInt(String s, int fallback) {
        try {
            return s == null ? fallback : Integer.parseInt(s.trim());
        } catch (NumberFormatException e) {
            return fallback;
        }
    }
}
