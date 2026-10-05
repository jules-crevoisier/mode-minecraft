package com.brasshaven.release;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.brasshaven.Brasshaven;
import com.brasshaven.config.BrasshavenConfig;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.event.server.ServerStartedEvent;
import net.minecraftforge.fml.loading.FMLEnvironment;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.Optional;
import java.util.concurrent.CompletableFuture;

/**
 * Asks GitHub, once per game launch and in the background, whether a newer Brasshaven release exists (a release tagged
 * {@code v<version>}; development builds are not offered). It only ever tells: nothing is downloaded. Any failure
 * (offline, rate limit, private repository) is silent. The client shows a toast and a chat line
 * ({@code client.ReleaseClient}, opt-out {@code updates.checkForUpdates} in brasshaven-client.toml); a dedicated server
 * writes one line to its log for the admin (opt-out in brasshaven-common.toml).
 */
public final class UpdateChecker {
    public record Release(String version, String url) {}

    private static final String API = "https://api.github.com/repos/" + BuildInfo.REPOSITORY + "/releases?per_page=30";
    private static CompletableFuture<Optional<Release>> result;

    private UpdateChecker() {}

    public static void register() {
        if (FMLEnvironment.dist == Dist.DEDICATED_SERVER) {
            ServerStartedEvent.BUS.addListener(e -> {
                if (BrasshavenConfig.UPDATE_CHECK.get()) {
                    check().thenAccept(r -> r.ifPresent(rel -> Brasshaven.LOGGER.info(
                            "Brasshaven {} is available (this server runs {}). Changelog and download: {} - update the "
                            + "server and every player to the same version, after a backup of the world.",
                            rel.version(), BuildInfo.version(), rel.url())));
                }
            });
        }
    }

    /** Automated test runs (CI, the scripted client) never call out. */
    public static boolean disabledHere() {
        return System.getenv("CI") != null || Boolean.getBoolean("brasshaven.ci");
    }

    /** The newer release, if any; the request is made once, later calls share its answer. */
    public static synchronized CompletableFuture<Optional<Release>> check() {
        if (result == null) {
            result = disabledHere() ? CompletableFuture.completedFuture(Optional.empty()) : fetch();
        }
        return result;
    }

    private static CompletableFuture<Optional<Release>> fetch() {
        try {
            HttpClient client = HttpClient.newBuilder()
                    .connectTimeout(Duration.ofSeconds(5))
                    .followRedirects(HttpClient.Redirect.NORMAL)
                    .build();
            HttpRequest request = HttpRequest.newBuilder(URI.create(API))
                    .timeout(Duration.ofSeconds(10))
                    .header("Accept", "application/vnd.github+json")
                    .header("User-Agent", "Brasshaven-mod/" + BuildInfo.version())
                    .GET()
                    .build();
            return client.sendAsync(request, HttpResponse.BodyHandlers.ofString())
                    .thenApply(r -> r.statusCode() == 200 ? newest(r.body()) : Optional.<Release>empty())
                    .exceptionally(t -> {
                        Brasshaven.LOGGER.debug("Brasshaven update check skipped: {}", t.getMessage());
                        return Optional.empty();
                    });
        } catch (RuntimeException e) {
            Brasshaven.LOGGER.debug("Brasshaven update check skipped: {}", e.getMessage());
            return CompletableFuture.completedFuture(Optional.empty());
        }
    }

    /** The highest published {@code v*} release, when it is newer than the running jar. */
    static Optional<Release> newest(String body) {
        try {
            JsonElement root = JsonParser.parseString(body);
            if (!root.isJsonArray()) {
                return Optional.empty();
            }
            ModVersion current = ModVersion.parse(BuildInfo.version());
            ModVersion best = null;
            Release found = null;
            for (JsonElement e : (JsonArray) root) {
                if (!e.isJsonObject()) {
                    continue;
                }
                JsonObject o = e.getAsJsonObject();
                String tag = string(o, "tag_name");
                if (tag == null || !tag.matches("v\\d.*") || bool(o, "draft")) {
                    continue;
                }
                ModVersion v = ModVersion.parse(tag);
                if (v.isNewerThan(current) && (best == null || v.isNewerThan(best))) {
                    best = v;
                    String url = string(o, "html_url");
                    found = new Release(tag.substring(1), url != null ? url : BuildInfo.RELEASES_URL);
                }
            }
            return Optional.ofNullable(found);
        } catch (RuntimeException ex) {
            return Optional.empty();
        }
    }

    private static String string(JsonObject o, String key) {
        JsonElement e = o.get(key);
        return e != null && e.isJsonPrimitive() ? e.getAsString() : null;
    }

    private static boolean bool(JsonObject o, String key) {
        JsonElement e = o.get(key);
        return e != null && e.isJsonPrimitive() && e.getAsBoolean();
    }
}
