package com.brasshaven.client;

import com.mojang.logging.LogUtils;
import com.brasshaven.Brasshaven;
import com.brasshaven.config.BrasshavenClientConfig;
import net.minecraft.client.Minecraft;
import net.minecraft.client.Screenshot;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraft.client.gui.screens.inventory.CreativeModeInventoryScreen;
import net.minecraft.client.server.IntegratedServer;
import net.minecraft.commands.CommandSource;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.permissions.LevelBasedPermissionSet;
import net.minecraft.util.FileUtil;
import net.minecraft.world.Difficulty;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.LevelSettings;
import net.minecraft.world.level.WorldDataConfiguration;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.WorldOptions;
import net.minecraft.world.level.levelgen.presets.WorldPresets;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructureStart;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.event.TickEvent;
import org.slf4j.Logger;

import java.io.File;
import java.io.IOException;
import java.lang.reflect.Field;
import java.lang.reflect.Modifier;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import java.util.function.BooleanSupplier;
import java.util.function.Supplier;

/**
 * Scripted client test for CI (tools/ci_client.py, the {@code client-test} job of .github/workflows/build.yml).
 *
 * <p>Does nothing unless the JVM runs with {@code -Dbrasshaven.ci=true} (build.gradle adds it to the client run
 * when Gradle gets {@code -Pbrasshaven.ci=true}), so players never see it.
 *
 * <p>Once the title screen is up it creates a fresh creative world, lets it settle, then plays a list of steps on
 * client ticks: open each of the mod's screens, place machines and use them, summon creatures, place the
 * Clockwork Citadel... Every step ends with a screenshot in {@code <gameDir>/screenshots/ci/<name>.png} (vanilla
 * {@link Screenshot#grab}). An exception or a timeout in one step is logged (ERROR, so the log scan sees it) and
 * the next step still runs. At the end it writes {@code <gameDir>/ci-client-report.txt} (one line per step) and
 * quits the game. A global timeout (-Dbrasshaven.ci.timeout, seconds) and a watchdog thread make sure the game
 * never hangs the CI job.
 */
public final class CiDriver {
    public static final boolean ACTIVE = Boolean.getBoolean("brasshaven.ci");
    /** Showcase mode (-Dbrasshaven.showcase=true, tools/ci_client.py --showcase): a filmed tour instead of the test. */
    static final boolean SHOWCASE = ACTIVE && Boolean.getBoolean("brasshaven.showcase");
    static final Logger LOGGER = LogUtils.getLogger();
    static final String TAG = "[brasshaven-ci] ";
    private static final long TIMEOUT_MS = Long.getLong("brasshaven.ci.timeout", 18 * 60) * 1000L;
    private static final int SETTLE_TICKS = Integer.getInteger("brasshaven.ci.settle", 200);
    private static final String WORLD = "brasshaven-ci";
    /** Floor of the stage built in the sky, away from the terrain (creatures, machines). */
    static final int STAGE_Y = 200;
    /** Empty hotbar slot used to click blocks with an empty hand. */
    private static final int EMPTY_SLOT = 8;

    private enum Phase { BOOT, CREATING, JOINING, RUNNING, DONE }

    private static Phase phase = Phase.BOOT;
    private static int phaseTicks;
    private static final long START = System.currentTimeMillis();
    private static long phaseStart = START;
    private static boolean busy;
    private static boolean optionsSet;
    private static int screenTicks;

    private static final List<Step> STEPS = new ArrayList<>();
    private static int stepIndex;
    private static final List<String> LINES = new ArrayList<>();
    /** Screenshot name -> "ok", "pending" or the failure. */
    private static final Map<String, String> SHOTS = new LinkedHashMap<>();
    private static final Map<String, Step> SHOT_STEP = new LinkedHashMap<>();

    /** Column of the player once the world has settled; the stage and the citadel are placed from it. */
    static int bx;
    static int bz;
    /** Viewpoint for the Citadel, worked out on the server once its bounding box is known. */
    private static volatile double[] citadelView;

    private CiDriver() {}

    public static void register() {
        if (!ACTIVE) {
            return;
        }
        LOGGER.info(TAG + "client test driver active (timeout {}s)", TIMEOUT_MS / 1000);
        TickEvent.ClientTickEvent.Post.BUS.addListener(e -> tick());
        if (SHOWCASE) {
            // the camera paths and the cursor move on every rendered frame, not on ticks
            TickEvent.RenderTickEvent.Pre.BUS.addListener(e -> CiShowcase.frame());
        }
        Thread watchdog = new Thread(() -> {
            try {
                Thread.sleep(TIMEOUT_MS + 120_000L);
            } catch (InterruptedException e) {
                return;
            }
            if (phase != Phase.DONE) {
                LOGGER.error(TAG + "watchdog: the client stopped ticking (phase {}), halting the JVM", phase);
                line("FAIL watchdog: the client stopped ticking in phase " + phase);
                writeReport("watchdog");
                Runtime.getRuntime().halt(3);
            }
        }, "brasshaven-ci-watchdog");
        watchdog.setDaemon(true);
        watchdog.start();
    }

    // ------------------------------------------------------------------ main loop

    private static void tick() {
        if (busy || phase == Phase.DONE) {
            return;
        }
        busy = true;
        try {
            tickPhase(Minecraft.getInstance());
        } catch (Throwable t) {
            LOGGER.error(TAG + "driver error in phase {}", phase, t);
            line("FAIL driver: " + t);
            finish("driver error");
        } finally {
            busy = false;
        }
    }

    private static void tickPhase(Minecraft mc) {
        if (System.currentTimeMillis() - START > TIMEOUT_MS) {
            LOGGER.error(TAG + "global timeout ({}s) in phase {}", TIMEOUT_MS / 1000, phase);
            if (phase == Phase.RUNNING && stepIndex < STEPS.size()) {
                STEPS.get(stepIndex).fail("global timeout");
                for (int i = stepIndex + 1; i < STEPS.size(); i++) {
                    STEPS.get(i).result = "SKIP " + STEPS.get(i).name + ": global timeout";
                    line(STEPS.get(i).result);
                }
                stepIndex = STEPS.size();
            } else {
                line("FAIL " + phase.name().toLowerCase() + ": global timeout");
            }
            finish("global timeout");
            return;
        }
        phaseTicks++;
        switch (phase) {
            case BOOT -> boot(mc);
            case CREATING -> creating(mc);
            case JOINING -> joining(mc);
            case RUNNING -> runSteps(mc);
            default -> {
            }
        }
    }

    private static void setPhase(Phase next) {
        phase = next;
        phaseTicks = 0;
        phaseStart = System.currentTimeMillis();
    }

    static String secs(long since) {
        return String.format(java.util.Locale.ROOT, "%.1fs", (System.currentTimeMillis() - since) / 1000.0);
    }

    /** Waits for the title screen (resources loaded, no overlay), then creates the test world. */
    private static void boot(Minecraft mc) {
        if (!mc.isGameLoadFinished() || mc.gui.overlay() != null || mc.gui.screen() == null) {
            phaseTicks = 0;
            return;
        }
        if (!optionsSet) {
            optionsSet = true;
            // Xvfb windows never get the focus: without this the game pauses itself
            mc.options.pauseOnLostFocus = false;
            mc.options.onboardAccessibility = false;
            mc.options.renderDistance().set(8);
            try {
                BrasshavenClientConfig.MINIMAP.set(true);
                BrasshavenClientConfig.HEALTH_BARS.set(BrasshavenClientConfig.HealthBars.ALWAYS);
            } catch (RuntimeException e) {
                LOGGER.warn(TAG + "could not set the client config (minimap, health bars): {}", e.toString());
            }
            if (SHOWCASE) {
                CiShowcase.options(mc);
            }
            line("PASS boot (" + secs(START) + " to the menu, screen " + mc.gui.screen().getClass().getSimpleName() + ")");
        }
        if (phaseTicks < 40) {
            return;
        }
        setPhase(Phase.CREATING);
        // outside of the tick event: world creation blocks the render thread while the server starts
        mc.execute(() -> {
            try {
                String folder = FileUtil.findAvailableName(mc.getLevelSource().getBaseDir(), WORLD, "");
                LevelSettings settings = new LevelSettings("Brasshaven CI", GameType.CREATIVE,
                        new LevelSettings.DifficultySettings(Difficulty.NORMAL, false, false), true, WorldDataConfiguration.DEFAULT);
                WorldOptions options = new WorldOptions("brasshaven-ci".hashCode(), false, false);
                LOGGER.info(TAG + "creating world '{}'", folder);
                mc.createWorldOpenFlows().createFreshLevel(folder, settings, options, WorldPresets::createNormalWorldDimensions,
                        new TitleScreen());
            } catch (Throwable t) {
                LOGGER.error(TAG + "could not create the test world", t);
                line("FAIL world: " + t);
                finish("world creation failed");
            }
        });
    }

    private static void creating(Minecraft mc) {
        if (mc.player != null && mc.level != null) {
            line("PASS world (" + secs(phaseStart) + " to create and join)");
            setPhase(Phase.JOINING);
        } else if (phaseTicks > 400 && mc.gui.screen() instanceof TitleScreen) {
            // createFreshLevel goes back to its parent screen when the data packs fail to load
            LOGGER.error(TAG + "back on the title screen: the test world could not be created (see the log above)");
            line("FAIL world: creation gave up (data packs?)");
            finish("world creation failed");
        } else if (phaseTicks > 20 * 60 * 10) {
            LOGGER.error(TAG + "the test world never loaded");
            line("FAIL world: never loaded (screen " + (mc.gui.screen() == null ? "none" : mc.gui.screen().getClass().getName()) + ")");
            finish("world never loaded");
        }
    }

    /** Lets the loading screen close and the terrain around the player settle. */
    private static void joining(Minecraft mc) {
        if (mc.player == null || mc.level == null) {
            line("FAIL world: left the world while settling");
            finish("left the world");
            return;
        }
        if (mc.gui.screen() != null) {
            // the settle time counts from the moment the loading screen is gone
            if (++screenTicks < 20 * 60 * 3) {
                phaseTicks = 0;
                return;
            }
            LOGGER.warn(TAG + "closing leftover screen {}", mc.gui.screen().getClass().getName());
            mc.gui.setScreen(null);
        }
        if (phaseTicks < SETTLE_TICKS) {
            return;
        }
        bx = mc.player.blockPosition().getX();
        bz = mc.player.blockPosition().getZ();
        LOGGER.info(TAG + "world settled, player at {}", mc.player.blockPosition());
        if (SHOWCASE) {
            CiShowcase.build();
        } else {
            buildSteps();
        }
        setPhase(Phase.RUNNING);
    }

    private static void runSteps(Minecraft mc) {
        if (stepIndex >= STEPS.size()) {
            // give the last screenshots time to reach the disk
            if (shotsPending() && phaseTicks < 200) {
                return;
            }
            finish("all steps done");
            return;
        }
        Step step = STEPS.get(stepIndex);
        if (step.opIndex == 0 && step.started == 0) {
            step.started = System.currentTimeMillis();
            LOGGER.info(TAG + "step {} ({}/{})", step.name, stepIndex + 1, STEPS.size());
            closeScreen(mc);
        }
        // instant ops chain within one tick; a waiting op returns false and resumes next tick
        for (int guard = 0; guard < 64 && step.opIndex < step.ops.size(); guard++) {
            Op op = step.ops.get(step.opIndex);
            boolean done;
            try {
                if (mc.player == null || mc.level == null) {
                    throw new IllegalStateException("not in a world any more");
                }
                done = op.tick();
            } catch (Throwable t) {
                LOGGER.error(TAG + "step {} FAILED at '{}'", step.name, op.label, t);
                step.fail(op.label + ": " + t);
                nextStep(mc);
                return;
            }
            op.age++;
            if (!done) {
                return;
            }
            step.opIndex++;
        }
        if (step.opIndex >= step.ops.size()) {
            if (step.problems.isEmpty()) {
                step.result = "PASS " + step.name + " (" + secs(step.started) + ")";
                line(step.result);
            } else {
                LOGGER.error(TAG + "step {} FAILED: {}", step.name, step.problems);
                step.fail(String.join("; ", step.problems));
            }
            nextStep(mc);
        }
    }

    private static void nextStep(Minecraft mc) {
        if (SHOWCASE) {
            CiShowcase.stepEnded(STEPS.get(stepIndex));
        }
        closeScreen(mc);
        stepIndex++;
        phaseTicks = 0;
    }

    private static void finish(String why) {
        if (phase == Phase.DONE) {
            return;
        }
        phase = Phase.DONE;
        Map<String, String> shots;
        synchronized (CiDriver.class) {
            shots = new LinkedHashMap<>(SHOTS);
        }
        for (Map.Entry<String, String> shot : shots.entrySet()) {
            if (!"ok".equals(shot.getValue())) {
                Step step = SHOT_STEP.get(shot.getKey());
                LOGGER.error(TAG + "screenshot {} not saved: {}", shot.getKey(), shot.getValue());
                if (step != null && step.result != null && step.result.startsWith("PASS")) {
                    step.fail("screenshot " + shot.getKey() + " " + shot.getValue());
                }
            }
        }
        writeReport(why);
        if (SHOWCASE) {
            CiShowcase.writeLog(why);
        }
        LOGGER.info(TAG + "DONE ({}), quitting", why);
        Minecraft.getInstance().stop();
    }

    private static synchronized boolean shotsPending() {
        return SHOTS.containsValue("pending");
    }

    static synchronized void line(String s) {
        LINES.add(s);
        LOGGER.info(TAG + "REPORT {}", s);
    }

    private static synchronized void writeReport(String why) {
        List<String> out = new ArrayList<>();
        out.add("# Brasshaven client test - " + why + " after " + secs(START));
        int pass = 0;
        int fail = 0;
        for (String l : LINES) {
            out.add(l);
            if (l.startsWith("PASS")) {
                pass++;
            } else if (l.startsWith("FAIL")) {
                fail++;
            }
        }
        for (Map.Entry<String, String> shot : SHOTS.entrySet()) {
            out.add("SHOT " + shot.getKey() + ": " + shot.getValue());
        }
        out.add("RESULT: " + pass + " passed, " + fail + " failed, ended by: " + why);
        try {
            Files.write(new File(Minecraft.getInstance().gameDirectory, "ci-client-report.txt").toPath(), out, StandardCharsets.UTF_8);
        } catch (IOException | RuntimeException e) {
            LOGGER.error(TAG + "could not write the report", e);
        }
    }

    // ------------------------------------------------------------------ the scenario

    private static void buildSteps() {
        // creative world from the start; freeze time and weather so every screenshot looks the same
        step("setup")
                .cmd(() -> List.of("gamerule advance_time false", "gamerule advance_weather false", "gamerule spawn_mobs false",
                        "time set 6000", "weather clear",
                        "give @s brasshaven:wayfarer_atlas", "give @s brasshaven:wayfarer_manual", "give @s brasshaven:brass_wrench"))
                .run("fly", CiDriver::fly)
                .waitTicks(20);

        step("hud_minimap")
                .cmd(() -> List.of("tp @s ~ ~8 ~ 135 15"))
                .run("fly", CiDriver::fly)
                .settleChunks(1200)
                .waitTicks(100)
                .shot("hud_minimap");

        step("world_map")
                .run("open", ClientHooks::openWorldMap)
                .until("WorldMapScreen", () -> screen() instanceof com.brasshaven.client.map.WorldMapScreen, 60)
                .waitTicks(60)
                .shot("world_map");

        // the options panel, the minimap set to 96 px with its slider: it shows live in its corner
        step("world_map_options")
                .run("open options", () -> {
                    BrasshavenClientConfig.setMinimapPixels(96);
                    if (screen() instanceof com.brasshaven.client.map.WorldMapScreen map) {
                        map.openOptions();
                    }
                })
                .waitTicks(30)
                .shot("world_map_options")
                .run("default size", () -> BrasshavenClientConfig.setMinimapPixels(BrasshavenClientConfig.MinimapSize.MEDIUM.outer));

        // the tilted 3D view (a fresh map screen: the options closed)
        step("world_map_3d")
                .run("open 3d", () -> {
                    ClientHooks.openWorldMap();
                    if (screen() instanceof com.brasshaven.client.map.WorldMapScreen map) {
                        map.set3d(true);
                    }
                })
                .until("WorldMapScreen", () -> screen() instanceof com.brasshaven.client.map.WorldMapScreen, 60)
                .waitTicks(80)
                .shot("world_map_3d")
                .run("back to 2d", () -> {
                    if (screen() instanceof com.brasshaven.client.map.WorldMapScreen map) {
                        map.set3d(false);
                    }
                });

        step("quest_journal")
                .run("request", () -> com.brasshaven.network.BrasshavenNet.toServer(new com.brasshaven.network.QuestRequestMsg(true)))
                .until("QuestJournalScreen", () -> screen() instanceof com.brasshaven.client.gui.QuestJournalScreen, 200)
                .waitTicks(30)
                .shot("quest_journal");

        step("talent_tree")
                .run("open", () -> Minecraft.getInstance().gui.setScreen(new com.brasshaven.client.gui.SkillTreeScreen()))
                .waitTicks(30)
                .shot("talent_tree");

        step("manual")
                .run("open welcome", () -> ClientHooks.openGuide("welcome"))
                .until("GuideScreen", () -> screen() instanceof com.brasshaven.client.gui.GuideScreen, 40)
                .waitTicks(30)
                .shot("manual_welcome")
                .run("open machines", () -> ClientHooks.openGuide("machines"))
                .waitTicks(30)
                .shot("manual_machines");

        // a stage in the sky, far above the terrain: flat floor, nothing in the way
        step("stage")
                .cmd(() -> List.of(
                        "fill " + at(-14, 0, -6) + " " + at(14, 0, 22) + " minecraft:smooth_stone",
                        "tp @s " + (bx + 0.5) + " " + (STAGE_Y + 1) + " " + (bz + 0.5) + " 0 25"))
                .run("fly", CiDriver::fly)
                .waitTicks(40);

        step("machine_screen")
                .cmd(() -> List.of("setblock " + at(0, 1, 2) + " brasshaven:auto_harvester"))
                .waitTicks(10)
                .run("use", () -> useBlock(0, 1, 2))
                .until("MachineScreen", () -> screen() instanceof com.brasshaven.client.gui.MachineScreen, 100)
                .waitTicks(30)
                .shot("machine_harvester");

        step("guild_terminal")
                .cmd(() -> List.of(
                        "setblock " + at(2, 1, 2) + " minecraft:chest",
                        "item replace block " + at(2, 1, 2) + " container.0 with minecraft:diamond 12",
                        "item replace block " + at(2, 1, 2) + " container.1 with minecraft:iron_ingot 40",
                        "item replace block " + at(2, 1, 2) + " container.2 with minecraft:oak_log 64",
                        "setblock " + at(1, 1, 2) + " brasshaven:guild_terminal"))
                .waitTicks(10)
                .run("use", () -> useBlock(1, 1, 2))
                .until("TerminalScreen", () -> screen() instanceof com.brasshaven.client.gui.TerminalScreen, 100)
                .waitTicks(40)
                .shot("guild_terminal");

        // two waystones: the first one used is discovered, so the second one's screen lists a destination
        step("waystone")
                .cmd(() -> List.of("setblock " + at(-3, 1, 2) + " brasshaven:waystone", "setblock " + at(-1, 1, 2) + " brasshaven:waystone"))
                .waitTicks(10)
                .run("use first", () -> useBlock(-3, 1, 2))
                .until("WaystoneScreen", () -> screen() instanceof com.brasshaven.client.gui.WaystoneScreen, 100)
                .run("close", () -> closeScreen(Minecraft.getInstance()))
                .waitTicks(10)
                .run("use second", () -> useBlock(-1, 1, 2))
                .until("WaystoneScreen", () -> screen() instanceof com.brasshaven.client.gui.WaystoneScreen, 100)
                .waitTicks(30)
                .shot("waystone");

        socialSteps();

        step("creative_tab")
                .run("open", CiDriver::openCreativeTab)
                .until("CreativeModeInventoryScreen", () -> screen() instanceof CreativeModeInventoryScreen, 40)
                .waitTicks(40)
                .shot("creative_tab");

        String still = "{NoAI:1b,PersistenceRequired:1b,Rotation:[180f,0f]}";
        step("creatures")
                .cmd(() -> List.of(
                        "fill " + at(-6, 1, 1) + " " + at(6, 3, 3) + " minecraft:air",
                        "fill " + at(5, 1, 6) + " " + at(9, 5, 10) + " minecraft:glass hollow",
                        "fill " + at(6, 2, 7) + " " + at(8, 4, 9) + " minecraft:water",
                        "summon brasshaven:grand_clockmaker " + (bx - 5.5) + " " + (STAGE_Y + 1) + " " + (bz + 13.5) + " " + still,
                        "summon brasshaven:brass_golem " + (bx + 0.5) + " " + (STAGE_Y + 1) + " " + (bz + 11.5) + " " + still,
                        "summon brasshaven:clockwork_spider " + (bx - 2.5) + " " + (STAGE_Y + 1) + " " + (bz + 6.5) + " " + still,
                        "summon brasshaven:glow_jellyfish " + (bx + 7.5) + " " + (STAGE_Y + 3) + " " + (bz + 8.5)
                                + " {NoAI:1b,NoGravity:1b,PersistenceRequired:1b,Rotation:[180f,0f]}",
                        "tp @s " + (bx + 0.5) + " " + (STAGE_Y + 2.5) + " " + (bz - 3.5) + " facing "
                                + (bx + 0.5) + " " + (STAGE_Y + 2) + " " + (bz + 10)))
                .run("fly", CiDriver::fly)
                .waitTicks(100)
                .shot("creatures");

        // the Clockwork Citadel well away from the stage, seen from a point worked out from its bounding box
        step("mega_structure")
                .run("render distance", () -> Minecraft.getInstance().options.renderDistance().set(10))
                .server("locate the citadel", CiDriver::prepareCitadel)
                .cmd(() -> {
                    double[] v = citadelView;
                    return List.of("tp @s " + v[3] + " " + (v[4] + 30) + " " + v[5]);
                })
                .run("fly", CiDriver::fly)
                .waitTicks(60)
                // the force-loaded chunks generate in the background: /place refuses until they are all there
                .retry("place structure", () -> List.of("place structure brasshaven:clockwork_citadel " + (bx + 240) + " 64 " + bz),
                        100, 30)
                .cmd(() -> {
                    double[] v = citadelView;
                    return List.of("tp @s " + v[0] + " " + v[1] + " " + v[2] + " facing " + v[3] + " " + v[4] + " " + v[5]);
                })
                .run("fly", CiDriver::fly)
                .settleChunks(2400)
                .waitTicks(60)
                .shot("mega_structure");
    }

    /**
     * The multiplayer features (com.brasshaven.social). The test has one player, so /brasshaven social demo fills the
     * company, the inbox and the board from two demo brasshaven; the trade screen and a player card (which need a second
     * player) are shown as client-side previews, which never reach the server.
     */
    private static void socialSteps() {
        step("company")
                .cmd(() -> List.of("brasshaven social demo", "brasshaven company sharexp", "brasshaven emote cheer"))
                .waitTicks(20)
                .run("open", com.brasshaven.client.social.ClientSocial::openCompany)
                .until("CompanyScreen", () -> screen() instanceof com.brasshaven.client.social.CompanyScreen, 60)
                .waitTicks(30)
                .shot("company");

        step("player_card")
                .run("open", () -> com.brasshaven.client.social.ClientSocial.card(new com.brasshaven.social.SocialNet.PlayerCard(
                        UUID.fromString("0000ada0-0000-4000-8000-000000000001"), "Ada", "Brass Owls", 3, 1, 0, 1)))
                .until("PlayerCardScreen", () -> screen() instanceof com.brasshaven.client.social.PlayerCardScreen, 40)
                .waitTicks(20)
                .shot("player_card");

        step("emote_wheel")
                .run("open", () -> Minecraft.getInstance().gui.setScreen(new com.brasshaven.client.social.EmoteWheelScreen()))
                .waitTicks(20)
                .shot("emote_wheel");

        step("pneumatic_post")
                .cmd(() -> List.of("setblock " + at(3, 1, -2) + " brasshaven:pneumatic_post[facing=west]",
                        "setblock " + at(-3, 1, -2) + " brasshaven:contract_board[facing=east]",
                        "give @s minecraft:paper 16", "give @s brasshaven:brass_nugget 8"))
                .waitTicks(10)
                .run("use", () -> useBlock(3, 1, -2))
                .until("PostScreen", () -> screen() instanceof com.brasshaven.client.social.PostScreen, 100)
                .waitTicks(40)
                .shot("pneumatic_post");

        step("contract_board")
                .run("use", () -> useBlock(-3, 1, -2))
                .until("ContractScreen", () -> screen() instanceof com.brasshaven.client.social.ContractScreen, 100)
                .waitTicks(40)
                .shot("contract_board");

        step("trade")
                .run("open", CiDriver::previewTrade)
                .until("TradeScreen", () -> screen() instanceof com.brasshaven.client.social.TradeScreen, 20)
                .waitTicks(20)
                .shot("trade");
    }

    /** The trade screen with both offers filled, client side only (a real trade needs a second player). */
    static void previewTrade() {
        Minecraft mc = Minecraft.getInstance();
        net.minecraft.network.FriendlyByteBuf buf = new net.minecraft.network.FriendlyByteBuf(io.netty.buffer.Unpooled.buffer());
        buf.writeUtf("Ada");
        com.brasshaven.social.TradeMenu menu = new com.brasshaven.social.TradeMenu(Integer.MAX_VALUE - 7, mc.player.getInventory(), buf);
        net.minecraft.world.item.ItemStack[] mine = {new net.minecraft.world.item.ItemStack(net.minecraft.world.item.Items.IRON_INGOT, 32),
                new net.minecraft.world.item.ItemStack(net.minecraft.world.item.Items.BREAD, 12)};
        net.minecraft.world.item.ItemStack[] theirs = {new net.minecraft.world.item.ItemStack(net.minecraft.world.item.Items.DIAMOND, 3),
                new net.minecraft.world.item.ItemStack(net.minecraft.world.item.Items.COMPASS)};
        for (int i = 0; i < mine.length; i++) {
            menu.getSlot(i).set(mine[i]);
        }
        for (int i = 0; i < theirs.length; i++) {
            menu.getSlot(com.brasshaven.social.TradeMenu.OFFER + i).set(theirs[i]);
        }
        menu.setData(1, 1);
        mc.gui.setScreen(new com.brasshaven.client.social.TradeScreen(menu, mc.player.getInventory(),
                net.minecraft.network.chat.Component.translatable("gui.brasshaven.trade.title", "Ada")));
    }

    private static String at(int dx, int dy, int dz) {
        return (bx + dx) + " " + (STAGE_Y + dy) + " " + (bz + dz);
    }

    static Screen screen() {
        return Minecraft.getInstance().gui.screen();
    }

    static void closeScreen(Minecraft mc) {
        Screen screen = mc.gui.screen();
        if (screen == null || mc.player == null) {
            return;
        }
        try {
            screen.onClose();
        } catch (Throwable t) {
            LOGGER.error(TAG + "closing {} threw", screen.getClass().getName(), t);
        }
        if (mc.gui.screen() != null) {
            mc.gui.setScreen(null);
        }
    }

    /** Creative flight, so the camera stays where the teleports put it. */
    static void fly() {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player != null && mc.player.getAbilities().mayfly) {
            mc.player.getAbilities().flying = true;
            mc.player.onUpdateAbilities();
        }
    }

    /** Right-clicks a stage block with an empty hand, through the normal client interaction path. */
    private static void useBlock(int dx, int dy, int dz) {
        Minecraft mc = Minecraft.getInstance();
        BlockPos pos = new BlockPos(bx + dx, STAGE_Y + dy, bz + dz);
        mc.player.getInventory().setSelectedSlot(EMPTY_SLOT);
        InteractionResult result = mc.gameMode.useItemOn(mc.player, InteractionHand.MAIN_HAND,
                new BlockHitResult(Vec3.atCenterOf(pos), Direction.UP, pos, false));
        LOGGER.info(TAG + "used {} at {} -> {}", mc.level.getBlockState(pos), pos, result);
    }

    /** Creative inventory on the mod's tab (the tab to show is a private static field of the screen). */
    private static void openCreativeTab() throws ReflectiveOperationException {
        Minecraft mc = Minecraft.getInstance();
        CreativeModeTab tab = com.brasshaven.registry.ModTabs.MAIN.get();
        boolean set = false;
        for (Field f : CreativeModeInventoryScreen.class.getDeclaredFields()) {
            if (Modifier.isStatic(f.getModifiers()) && f.getType() == CreativeModeTab.class) {
                f.setAccessible(true);
                f.set(null, tab);
                set = true;
                break;
            }
        }
        if (!set) {
            LOGGER.warn(TAG + "no selected-tab field in CreativeModeInventoryScreen, showing the default tab");
        }
        mc.gui.setScreen(new CreativeModeInventoryScreen(mc.player, mc.player.connection.enabledFeatures(),
                mc.options.operatorItemsTab().get()));
    }

    /**
     * Server thread: works out where /place structure will put the citadel (same seed and chunk, so the same
     * layout), force-loads its chunks and picks a viewpoint that frames its bounding box.
     */
    private static List<String> prepareCitadel(IntegratedServer server, ServerPlayer player) {
        ServerLevel level = server.overworld();
        BlockPos pos = new BlockPos(bx + 240, 64, bz);
        Holder.Reference<Structure> holder = level.registryAccess().lookupOrThrow(Registries.STRUCTURE)
                .get(Brasshaven.id("clockwork_citadel"))
                .orElseThrow(() -> new IllegalStateException("no structure brasshaven:clockwork_citadel"));
        ChunkGenerator generator = level.getChunkSource().getGenerator();
        // like /place structure: the spot is chosen here, so the terrain site check is skipped
        StructureStart start = com.brasshaven.world.SiteFit.unchecked(() -> holder.value().generate(holder, level.dimension(),
                level.registryAccess(), generator, generator.getBiomeSource(), level.getChunkSource().randomState(),
                level.getStructureManager(), level.getSeed(), ChunkPos.containing(pos), 0, level, b -> true));
        if (!start.isValid()) {
            throw new IllegalStateException("the citadel did not generate at " + pos);
        }
        BoundingBox box = start.getBoundingBox();
        LOGGER.info(TAG + "citadel bounding box {}", box);
        double cx = (box.minX() + box.maxX()) / 2.0;
        double cz = (box.minZ() + box.maxZ()) / 2.0;
        double cy = box.minY() + (box.maxY() - box.minY()) * 0.35;
        double size = Math.max(box.maxX() - box.minX(), box.maxZ() - box.minZ());
        double back = size * 0.55 + 20;
        citadelView = new double[] {cx - back, box.maxY() + size * 0.35 + 12, cz - back, cx, cy, cz};
        List<String> out = new ArrayList<>();
        int minCx = (box.minX() >> 4) - 1;
        int maxCx = (box.maxX() >> 4) + 1;
        for (int chz = (box.minZ() >> 4) - 1; chz <= (box.maxZ() >> 4) + 1; chz++) {
            // one row of chunks per command: /forceload takes at most 256 chunks
            out.add("forceload add " + (minCx * 16) + " " + (chz * 16) + " " + (maxCx * 16) + " " + (chz * 16));
        }
        return out;
    }

    // ------------------------------------------------------------------ server commands

    /** Runs commands as the player on the integrated server; returns the ones that failed, with their output. */
    static CompletableFuture<List<String>> runCommands(List<String> commands) {
        Minecraft mc = Minecraft.getInstance();
        IntegratedServer server = mc.getSingleplayerServer();
        if (server == null) {
            throw new IllegalStateException("no integrated server");
        }
        UUID id = mc.player.getUUID();
        return server.submit(() -> {
            List<String> failed = new ArrayList<>();
            ServerPlayer player = server.getPlayerList().getPlayer(id);
            for (String command : commands) {
                if (!runCommand(server, player, command)) {
                    failed.add("/" + command);
                }
            }
            return failed;
        });
    }

    static boolean runCommand(IntegratedServer server, ServerPlayer player, String command) {
        boolean[] ok = {false};
        StringBuilder output = new StringBuilder();
        CommandSource sink = new CommandSource() {
            @Override
            public void sendSystemMessage(Component message) {
                if (!output.isEmpty()) {
                    output.append(" | ");
                }
                output.append(message.getString());
            }

            @Override
            public boolean acceptsSuccess() {
                return true;
            }

            @Override
            public boolean acceptsFailure() {
                return true;
            }

            @Override
            public boolean shouldInformAdmins() {
                return false;
            }
        };
        CommandSourceStack source = (player != null ? player.createCommandSourceStack() : server.createCommandSourceStack())
                .withSource(sink)
                .withPermission(LevelBasedPermissionSet.OWNER)
                .withCallback((success, result) -> ok[0] |= success);
        server.getCommands().performPrefixedCommand(source, command);
        LOGGER.info(TAG + "/{} -> {} {}", command, ok[0] ? "ok" : "FAILED", output);
        return ok[0];
    }

    // ------------------------------------------------------------------ steps and ops

    static Step step(String name) {
        Step step = new Step(name);
        STEPS.add(step);
        return step;
    }

    @FunctionalInterface
    interface Action {
        void run() throws Exception;
    }

    @FunctionalInterface
    interface ServerTask {
        List<String> run(IntegratedServer server, ServerPlayer player) throws Exception;
    }

    abstract static class Op {
        final String label;
        int age;

        Op(String label) {
            this.label = label;
        }

        abstract boolean tick() throws Exception;
    }

    static final class Step {
        final String name;
        final List<Op> ops = new ArrayList<>();
        final List<String> problems = new ArrayList<>();
        int opIndex;
        long started;
        String result;

        Step(String name) {
            this.name = name;
        }

        void fail(String why) {
            String old = result;
            result = "FAIL " + name + " (" + (started == 0 ? "-" : secs(started)) + "): " + why;
            if (old != null) {
                synchronized (CiDriver.class) {
                    LINES.remove(old); // a step that passed, then lost its screenshot
                }
            }
            line(result);
        }

        Step add(Op op) {
            ops.add(op);
            return this;
        }

        Step run(String label, Action action) {
            return add(new Op(label) {
                @Override
                boolean tick() throws Exception {
                    action.run();
                    return true;
                }
            });
        }

        Step waitTicks(int ticks) {
            return add(new Op("wait " + ticks) {
                @Override
                boolean tick() {
                    return age >= ticks;
                }
            });
        }

        /** Waits for a condition; failing to see it within maxTicks fails the step. */
        Step until(String what, BooleanSupplier condition, int maxTicks) {
            return add(new Op("wait for " + what) {
                @Override
                boolean tick() {
                    if (condition.getAsBoolean()) {
                        return true;
                    }
                    if (age >= maxTicks) {
                        Screen s = screen();
                        throw new IllegalStateException("no " + what + " after " + maxTicks + " ticks (screen: "
                                + (s == null ? "none" : s.getClass().getName()) + ")");
                    }
                    return false;
                }
            });
        }

        /** Waits until no chunk section is left to compile for 20 ticks in a row (or maxTicks, without failing). */
        Step settleChunks(int maxTicks) {
            return add(new Op("chunks rendered") {
                int quiet;

                @Override
                boolean tick() {
                    quiet = Minecraft.getInstance().levelRenderer.hasRenderedAllSections() ? quiet + 1 : 0;
                    if (age >= maxTicks) {
                        LOGGER.warn(TAG + "{}: chunks still compiling after {} ticks, going on", name, maxTicks);
                        return true;
                    }
                    return quiet >= 20;
                }
            });
        }

        /** Commands run as the player on the integrated server; a failed command fails the step (which goes on). */
        Step cmd(Supplier<List<String>> commands) {
            return add(new Op("commands") {
                CompletableFuture<List<String>> pending;

                @Override
                boolean tick() {
                    if (pending == null) {
                        pending = runCommands(commands.get());
                    }
                    if (!pending.isDone()) {
                        if (age > 20 * 180) {
                            throw new IllegalStateException("the server did not run the commands within 3 minutes");
                        }
                        return false;
                    }
                    problems.addAll(pending.join());
                    return true;
                }
            });
        }

        /** Code on the server thread; the commands it returns are then run as the player. */
        Step server(String label, ServerTask task) {
            return add(new Op(label) {
                CompletableFuture<List<String>> pending;

                @Override
                boolean tick() {
                    if (pending == null) {
                        Minecraft mc = Minecraft.getInstance();
                        IntegratedServer server = mc.getSingleplayerServer();
                        UUID id = mc.player.getUUID();
                        pending = server.submit(() -> {
                            ServerPlayer player = server.getPlayerList().getPlayer(id);
                            try {
                                List<String> failed = new ArrayList<>();
                                for (String command : task.run(server, player)) {
                                    if (!runCommand(server, player, command)) {
                                        failed.add("/" + command);
                                    }
                                }
                                return failed;
                            } catch (Exception e) {
                                throw new java.util.concurrent.CompletionException(e);
                            }
                        });
                    }
                    if (!pending.isDone()) {
                        if (age > 20 * 180) {
                            throw new IllegalStateException("the server task did not finish within 3 minutes");
                        }
                        return false;
                    }
                    problems.addAll(pending.join());
                    return true;
                }
            });
        }

        /**
         * Runs the commands again every {@code every} ticks until they all succeed (for commands that need chunks
         * loading in the background); fails the step after maxTries attempts.
         */
        Step retry(String label, Supplier<List<String>> commands, int every, int maxTries) {
            return add(new Op(label) {
                CompletableFuture<List<String>> pending;
                int tries;
                int nextAt;

                @Override
                boolean tick() {
                    if (pending != null) {
                        if (!pending.isDone()) {
                            return false;
                        }
                        List<String> failed = pending.join();
                        pending = null;
                        if (failed.isEmpty()) {
                            LOGGER.info(TAG + "{}: done after {} tries", label, tries);
                            return true;
                        }
                        if (tries >= maxTries) {
                            throw new IllegalStateException("still failing after " + tries + " tries: " + failed);
                        }
                        nextAt = age + every;
                    }
                    if (age >= nextAt) {
                        tries++;
                        pending = runCommands(commands.get());
                    }
                    return false;
                }
            });
        }

        /** Clears the chat, waits a few frames, then saves the screenshot as screenshots/ci/<name>.png. */
        Step shot(String shotName) {
            run("clear chat", () -> Minecraft.getInstance().gui.hud.getChat().clearMessages(false));
            waitTicks(4);
            Step self = this;
            add(new Op("screenshot " + shotName) {
                @Override
                boolean tick() {
                    Minecraft mc = Minecraft.getInstance();
                    File dir = new File(mc.gameDirectory, Screenshot.SCREENSHOT_DIR + "/ci");
                    dir.mkdirs();
                    File file = new File(dir, shotName + ".png");
                    file.delete();
                    synchronized (CiDriver.class) {
                        SHOTS.put(shotName, "pending");
                        SHOT_STEP.put(shotName, self);
                    }
                    Screenshot.grab(mc.gameDirectory, "ci/" + shotName + ".png", mc.gameRenderer.mainRenderTarget(), 1, message -> {
                        String status = file.isFile() && file.length() > 0 ? "ok" : "failed: " + message.getString();
                        synchronized (CiDriver.class) {
                            SHOTS.put(shotName, status);
                        }
                        LOGGER.info(TAG + "screenshot {}: {}", shotName, status);
                    });
                    return true;
                }
            });
            return waitTicks(10);
        }
    }
}
