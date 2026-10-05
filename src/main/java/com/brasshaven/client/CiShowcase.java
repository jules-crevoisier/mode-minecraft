package com.brasshaven.client;

import com.brasshaven.Brasshaven;
import com.brasshaven.config.BrasshavenClientConfig;
import com.brasshaven.generated.GeneratedSkills;
import com.mojang.blaze3d.platform.Window;
import net.minecraft.client.CameraType;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.components.AbstractWidget;
import net.minecraft.client.gui.components.events.GuiEventListener;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.input.CharacterEvent;
import net.minecraft.client.input.KeyEvent;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.client.input.MouseButtonInfo;
import net.minecraft.client.server.IntegratedServer;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructureStart;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.Vec3;

import java.io.File;
import java.io.IOException;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.function.Supplier;

/**
 * The filmed tour of the {@code showcase} CI job (tools/ci_client.py --showcase, which records the Xvfb display with
 * ffmpeg x11grab and cuts one clip per scene; tools/make_video.py composes the presentation videos from the clips).
 *
 * <p>Only runs with {@code -Dbrasshaven.ci=true -Dbrasshaven.showcase=true}. It reuses {@link CiDriver}'s world, steps
 * and commands. Each step prepares a scene (places a structure, builds a farm, spawns a boss...) and then films it
 * between a BEGIN and an END mark: smooth camera paths (position and look set on every rendered frame), real screens
 * driven like a player would (cursor glides, hovers, clicks, keys, typing, scrolling, dragging).
 *
 * <p>Software OpenGL is slow, so the scenes are filmed in slow motion: {@code /tick rate} slows the game by a factor
 * k picked from the frame rate measured at the start (or -Dbrasshaven.showcase.slowmo), and the camera and cursor
 * follow the same slowed clock. The wrapper speeds each clip up by k again, which multiplies the frame rate of the
 * footage by k. Everything is written to {@code <gameDir>/showcase/scenes.json}: per scene the wall-clock begin and
 * end (epoch ms, the clock of x11grab), k, and the cursor track (scene seconds, window pixels, button state) that the
 * composer draws as a cursor (the X cursor itself is not recorded).
 */
final class CiShowcase {
    private static final String TAG = "[brasshaven-showcase] ";
    private static final double FORCED_SLOWMO = parseDouble(System.getProperty("brasshaven.showcase.slowmo", "0"));
    /** Frame rate the footage should reach once sped up again. */
    private static final double TARGET_FPS = 24.0;
    private static final double MAX_SLOWMO = 6.0;

    private static double slowmo = 1.0;
    private static double measuredFps;
    private static long frames;

    private static Scene current;
    private static final List<Scene> SCENES = new ArrayList<>();
    private static final Map<String, BoundingBox> BOXES = new HashMap<>();
    private static final Map<String, double[]> SPOTS = new HashMap<>();

    /** Ground level of the clearing around the spawn column where the gameplay scenes are filmed. */
    private static int gy = 64;

    private static Cam cam;
    /** Cursor position in GUI coordinates, or null while no cursor is shown. */
    private static double[] cursor;
    private static Glide glide;
    private static boolean pressed;
    private static boolean dragging;

    private CiShowcase() {}

    // ------------------------------------------------------------------ hooks called by CiDriver

    /** Video settings for the filming: French, modest distances, no clouds, no tip cards over the shots. */
    static void options(Minecraft mc) {
        mc.options.renderDistance().set(10);
        mc.options.simulationDistance().set(6);
        mc.options.fov().set(70);
        mc.options.bobView().set(false);
        mc.options.entityShadows().set(true);
        mc.options.framerateLimit().set(120);
        try {
            BrasshavenClientConfig.TIPS.set(false);
            BrasshavenClientConfig.MINIMAP_ROTATE.set(true);
            BrasshavenClientConfig.QUEST_TRACKER.set(true);
            BrasshavenClientConfig.DAMAGE_NUMBERS.set(true);
        } catch (RuntimeException e) {
            CiDriver.LOGGER.warn(TAG + "could not set the client config: {}", e.toString());
        }
        CiDriver.LOGGER.info(TAG + "language {}, window {}x{}, gui scale {}", mc.options.languageCode,
                mc.getWindow().getScreenWidth(), mc.getWindow().getScreenHeight(), mc.getWindow().getGuiScale());
    }

    /** Called on every rendered frame (RenderTickEvent.Pre): moves the camera and the cursor. */
    static void frame() {
        frames++;
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null || current == null) {
            return;
        }
        double t = time();
        try {
            if (cam != null) {
                cam.apply(mc, t);
            }
            if (glide != null) {
                double u = glide.seconds <= 0 ? 1.0 : Math.min(1.0, (t - glide.start) / glide.seconds);
                double e = ease(u);
                double[] p = {glide.from[0] + (glide.to[0] - glide.from[0]) * e, glide.from[1] + (glide.to[1] - glide.from[1]) * e};
                moveCursor(mc, p, t);
                if (u >= 1.0) {
                    glide = null;
                }
            } else if (cursor != null && mc.gui.screen() == null) {
                hideCursor(t);
            }
        } catch (Throwable e) {
            CiDriver.LOGGER.error(TAG + "frame update failed in scene {}", current == null ? "-" : current.name, e);
            cam = null;
            glide = null;
        }
    }

    /** A step is over (passed or failed): close its scene if it is still open and put the game speed back. */
    static void stepEnded(CiDriver.Step step) {
        if (current != null) {
            current.end = System.currentTimeMillis();
            current.status = "unfinished";
            current.error = step.result == null ? "step ended" : step.result;
            CiDriver.LOGGER.error(TAG + "SCENE {} ENDED EARLY: {}", current.name, current.error);
            current = null;
        }
        cam = null;
        glide = null;
        cursor = null;
        pressed = false;
        dragging = false;
        Minecraft mc = Minecraft.getInstance();
        if (mc.player != null && Math.abs(slowmo - 1.0) > 1e-6 && step.result != null && step.result.startsWith("FAIL")) {
            CiDriver.runCommands(List.of("tick rate 20"));
        }
        writeLog("running");
    }

    // ------------------------------------------------------------------ the tour

    static void build() {
        String still = "{NoAI:1b,PersistenceRequired:1b,Rotation:[180f,0f]}";
        CiDriver.step("setup")
                .cmd(() -> List.of("gamerule advance_time false", "gamerule advance_weather false", "gamerule spawn_mobs false",
                        "time set 5000", "weather clear", "difficulty normal",
                        "give @s brasshaven:wayfarer_atlas", "give @s brasshaven:wayfarer_manual",
                        "give @s brasshaven:structure_compass", "give @s brasshaven:brass_wrench"))
                .server("clearing", CiShowcase::prepareClearing)
                .run("fly", CiDriver::fly)
                .waitTicks(40);

        // frame rate over a slow flight above the forest, before anything is filmed: picks the slow-motion factor
        CiDriver.step("calibrate")
                .cmd(() -> List.of("gamemode spectator", "tp @s " + bx(-30) + " " + (gy + 30) + " " + bz(-30)))
                .run("hud off", () -> hud(false))
                .settleChunks(1600)
                .add(beginOp("calibrate", true))
                .add(cameraOp(8, () -> line(bx(-30), gy + 30, bz(-30), bx(30), gy + 26, bz(10), -60, 25, -40)))
                .add(endOp(true));

        structureScene("citadel", "clockwork_citadel", 700, 0, 200, 290, 16);
        structureScene("sylvan_palace", "sylvan_palace", 0, 700, 30, 110, 12);
        structureScene("world_tree", "giant_tree", -700, 0, 300, 380, 12);

        CiDriver.step("back_home")
                .cmd(() -> List.of("forceload remove all", "gamemode creative",
                        "tp @s " + bx(0.5) + " " + gy + " " + bz(8.5) + " 180 10"))
                .run("hud on", () -> hud(true))
                .settleChunks(2400)
                .waitTicks(40);

        // ---- quests: the journal, a tracked quest, the HUD and minimap while exploring
        CiDriver.step("quest_journal")
                .cmd(() -> List.of("gamemode creative", "tp @s " + bx(0.5) + " " + gy + " " + bz(8.5) + " 180 5"))
                .run("hud on", () -> hud(true))
                .run("hotbar", () -> Minecraft.getInstance().player.getInventory().setSelectedSlot(0))
                .waitTicks(20)
                .add(beginOp("quest_journal", false))
                .add(holdOp(0.8))
                .run("open", () -> com.brasshaven.network.BrasshavenNet.toServer(new com.brasshaven.network.QuestRequestMsg(true)))
                .until("QuestJournalScreen", () -> CiDriver.screen() instanceof com.brasshaven.client.gui.QuestJournalScreen, 200)
                .add(holdOp(0.6))
                .add(glideOp(() -> rel(0.22, 0.30), 0.9))
                .add(holdOp(0.5))
                .add(keyOp(264))
                .add(holdOp(0.7))
                .add(keyOp(264))
                .add(holdOp(0.7))
                .add(keyOp(265))
                .add(holdOp(0.7))
                .add(glideOp(() -> widgetField("track"), 0.9))
                .add(holdOp(0.4))
                .add(clickOp())
                .add(holdOp(1.2))
                .run("close", () -> CiDriver.closeScreen(Minecraft.getInstance()))
                .add(holdOp(2.0))
                .add(endOp(false));

        CiDriver.step("hud_explore")
                .cmd(() -> List.of("gamemode creative", "tp @s " + bx(0.5) + " " + (gy + 14) + " " + bz(-6)))
                .run("hud on", () -> hud(true))
                .run("fly", CiDriver::fly)
                .waitTicks(20)
                .add(beginOp("hud_explore", false))
                .add(cameraOp(10, () -> line(bx(0.5), gy + 14, bz(-6), bx(-50), gy + 18, bz(-60), 160, 12, 115)))
                .add(endOp(false));

        // ---- a quest giver and his contracts
        CiDriver.step("npc_contract")
                .cmd(() -> List.of("gamemode creative", "tp @s " + bx(6.5) + " " + gy + " " + bz(-6.5) + " 0 0",
                        "brasshaven npc spawn guild_agent",
                        "tp @s " + bx(6.5) + " " + gy + " " + bz(-4.0) + " 180 8"))
                .run("hud on", () -> hud(true))
                .run("empty hand", () -> Minecraft.getInstance().player.getInventory().setSelectedSlot(8))
                .waitTicks(30)
                .add(beginOp("npc_contract", false))
                .add(holdOp(1.2))
                .run("talk", () -> {
                    Minecraft mc = Minecraft.getInstance();
                    Entity npc = nearest("brasshaven:wayfarer_npc", 8);
                    if (npc == null) {
                        throw new IllegalStateException("no quest giver near the player");
                    }
                    mc.gameMode.interact(mc.player, npc, new EntityHitResult(npc), InteractionHand.MAIN_HAND);
                })
                .until("NpcDialogScreen", () -> CiDriver.screen() instanceof com.brasshaven.client.gui.NpcDialogScreen, 100)
                .add(holdOp(0.8))
                .add(glideOp(() -> rel(0.32, 0.42), 0.9))
                .add(holdOp(0.9))
                .add(glideOp(() -> widgetField("main"), 0.8))
                .add(holdOp(0.3))
                .add(clickOp())
                .add(holdOp(1.0))
                .add(glideOp(() -> widgetField("track"), 0.6))
                .add(holdOp(0.3))
                .add(clickOp())
                .add(holdOp(1.2))
                .run("close", () -> CiDriver.closeScreen(Minecraft.getInstance()))
                .add(holdOp(1.6))
                .add(endOp(false));

        // ---- the world map: drag, zoom, the 3D view, the options panel
        CiDriver.step("world_map")
                .cmd(() -> List.of("gamemode creative", "tp @s " + bx(0.5) + " " + (gy + 3) + " " + bz(0.5) + " 200 10"))
                .run("fly", CiDriver::fly)
                .waitTicks(20)
                .run("open", ClientHooks::openWorldMap)
                .until("WorldMapScreen", () -> CiDriver.screen() instanceof com.brasshaven.client.map.WorldMapScreen, 60)
                .waitTicks(30)
                .add(beginOp("world_map", false))
                .add(holdOp(0.6))
                .add(glideOp(() -> rel(0.38, 0.5), 0.8))
                .add(dragOp(-90, -40, 1.6))
                .add(holdOp(0.4))
                .add(scrollOp(1))
                .add(holdOp(0.5))
                .add(scrollOp(1))
                .add(holdOp(0.8))
                .add(scrollOp(-1))
                .add(holdOp(0.4))
                .add(glideOp(() -> mapButton(-2), 0.9))
                .add(holdOp(0.6))
                .add(clickOp())
                .add(holdOp(1.6))
                .add(glideOp(() -> rel(0.38, 0.5), 0.7))
                .add(dragOp(70, 20, 1.4))
                .add(holdOp(0.6))
                .add(glideOp(() -> mapButton(-1), 0.8))
                .add(holdOp(0.4))
                .add(clickOp())
                .add(holdOp(2.2))
                .add(endOp(false))
                .run("2d again", () -> {
                    if (CiDriver.screen() instanceof com.brasshaven.client.map.WorldMapScreen map) {
                        map.set3d(false);
                    }
                });

        // ---- waystones: discover one, travel from the other
        CiDriver.step("waystone")
                .cmd(() -> List.of("gamemode creative",
                        "setblock " + at(-6, 0, -8) + " brasshaven:waystone", "setblock " + at(-6, 0, 6) + " brasshaven:waystone",
                        "tp @s " + bx(-6.5) + " " + gy + " " + bz(-6.5) + " 180 30"))
                .run("hud on", () -> hud(true))
                .run("empty hand", () -> Minecraft.getInstance().player.getInventory().setSelectedSlot(8))
                .waitTicks(20)
                .run("discover", () -> useAt(-6, 0, -8))
                .until("WaystoneScreen", () -> CiDriver.screen() instanceof com.brasshaven.client.gui.WaystoneScreen, 100)
                .run("close", () -> CiDriver.closeScreen(Minecraft.getInstance()))
                .cmd(() -> List.of("tp @s " + bx(-6.5) + " " + gy + " " + bz(3.5) + " 0 25"))
                .waitTicks(30)
                .add(beginOp("waystone", false))
                .add(holdOp(1.0))
                .run("use", () -> useAt(-6, 0, 6))
                .until("WaystoneScreen", () -> CiDriver.screen() instanceof com.brasshaven.client.gui.WaystoneScreen, 100)
                .add(holdOp(0.6))
                .add(glideOp(() -> rel(0.36, 0.26), 0.8))
                .add(holdOp(0.8))
                .add(glideOp(() -> widgetField("travel"), 0.8))
                .add(holdOp(0.5))
                .add(clickOp())
                .add(holdOp(2.4))
                .add(endOp(false));

        // ---- talents: three points from 30 levels, unlock the first talent of two branches
        CiDriver.step("talents")
                .cmd(() -> List.of("xp add @s 30 levels"))
                .waitTicks(20)
                .run("open", () -> Minecraft.getInstance().gui.setScreen(new com.brasshaven.client.gui.SkillTreeScreen()))
                .waitTicks(20)
                .add(beginOp("talents", false))
                .add(holdOp(0.6))
                .add(glideOp(() -> skillNode("warrior", 0), 0.9))
                .add(holdOp(1.0))
                .add(clickOp())
                .add(holdOp(0.6))
                .add(glideOp(() -> skillNode("explorer", 0), 0.8))
                .add(holdOp(0.9))
                .add(clickOp())
                .add(holdOp(0.6))
                .add(glideOp(() -> skillNode("arcanist", 1), 0.8))
                .add(holdOp(1.2))
                .add(glideOp(() -> skillNode("engineer", 2), 0.8))
                .add(holdOp(1.4))
                .add(endOp(false));

        // ---- magic: fire bolts and chain lightning on husks (they do not burn in the sun)
        CiDriver.step("magic")
                .cmd(() -> List.of("gamemode survival", "effect give @s resistance infinite 4 true",
                        "effect give @s regeneration infinite 2 true", "effect give @s saturation infinite 0 true",
                        "item replace entity @s hotbar.0 with brasshaven:fire_staff",
                        "item replace entity @s hotbar.1 with brasshaven:thunder_staff",
                        "tp @s " + bx(0.5) + " " + gy + " " + bz(-2.5) + " 180 5",
                        "summon minecraft:husk " + bx(-3.5) + " " + gy + " " + bz(-13.5),
                        "summon minecraft:husk " + bx(2.5) + " " + gy + " " + bz(-15.5),
                        "summon minecraft:husk " + bx(5.5) + " " + gy + " " + bz(-12.5)))
                .run("hud on", () -> hud(true))
                .run("staff", () -> Minecraft.getInstance().player.getInventory().setSelectedSlot(0))
                .waitTicks(20)
                .add(beginOp("magic", false))
                .add(holdOp(0.6))
                .add(castOp(0, 1.3))
                .add(castOp(0, 1.3))
                .add(castOp(0, 1.3))
                .run("thunder", () -> Minecraft.getInstance().player.getInventory().setSelectedSlot(1))
                .add(holdOp(0.6))
                .add(castOp(1, 2.0))
                .add(endOp(false))
                .cmd(() -> List.of("kill @e[type=minecraft:husk]", "effect clear @s", "gamemode creative"));

        // ---- machines: a ripe field, the Auto-Harvester and two sprinklers at work, then the machine screen
        CiDriver.step("machines")
                .cmd(CiShowcase::farmCommands)
                .run("hud off", () -> hud(false))
                .cmd(() -> List.of("gamemode spectator", "tp @s " + bx(-24) + " " + (gy + 9) + " " + bz(14)))
                .settleChunks(600)
                .add(beginOp("machines", false))
                .add(cameraOp(13, () -> orbit(bx(-14.5), gy, bz(10.5), 14, 9, 140, 215, 0)))
                .add(endOp(false));

        CiDriver.step("machine_screen")
                .cmd(() -> List.of("gamemode creative", "tp @s " + bx(-13.5) + " " + gy + " " + bz(7.5) + " 0 40"))
                .run("hud on", () -> hud(true))
                .run("empty hand", () -> Minecraft.getInstance().player.getInventory().setSelectedSlot(8))
                .waitTicks(20)
                .add(beginOp("machine_screen", false))
                .add(holdOp(0.5))
                .run("use", () -> useAt(-14, 0, 10))
                .until("MachineScreen", () -> CiDriver.screen() instanceof com.brasshaven.client.gui.MachineScreen, 100)
                .add(holdOp(0.6))
                .add(glideOp(() -> widgetIndex(0), 0.8))
                .add(holdOp(0.7))
                .add(glideOp(() -> widgetIndex(2), 0.6))
                .add(holdOp(0.4))
                .add(clickOp())
                .add(holdOp(0.8))
                .add(glideOp(() -> widgetIndex(3), 0.6))
                .add(holdOp(0.4))
                .add(clickOp())
                .add(holdOp(0.8))
                .run("close", () -> CiDriver.closeScreen(Minecraft.getInstance()))
                .add(holdOp(2.0))
                .add(endOp(false));

        // ---- the Guild Terminal: every chest around in one grid, a search, a sort
        CiDriver.step("guild_terminal")
                .cmd(CiShowcase::storageCommands)
                .cmd(() -> List.of("gamemode creative", "tp @s " + bx(10.5) + " " + gy + " " + bz(4.5) + " 180 30"))
                .run("empty hand", () -> Minecraft.getInstance().player.getInventory().setSelectedSlot(8))
                .waitTicks(20)
                .add(beginOp("guild_terminal", false))
                .add(holdOp(0.6))
                .run("use", () -> useAt(10, 0, 2))
                .until("TerminalScreen", () -> CiDriver.screen() instanceof com.brasshaven.client.gui.TerminalScreen, 100)
                .add(holdOp(1.0))
                .add(glideOp(() -> widgetField("search"), 0.8))
                .add(clickOp())
                .add(typeOp("fer", 0.28))
                .add(holdOp(1.4))
                .add(keyOp(259))
                .add(holdOp(0.15))
                .add(keyOp(259))
                .add(holdOp(0.15))
                .add(keyOp(259))
                .add(holdOp(0.6))
                .add(glideOp(() -> widgetField("sortButton"), 0.8))
                .add(holdOp(0.3))
                .add(clickOp())
                .add(holdOp(1.4))
                .add(endOp(false));

        // ---- creatures: brass golems against husks and clockwork spiders, health bars over every head
        CiDriver.step("creatures")
                .cmd(() -> List.of("gamemode spectator",
                        "summon brasshaven:brass_golem " + bx(14.5) + " " + gy + " " + bz(-12.5),
                        "summon brasshaven:brass_golem " + bx(18.5) + " " + gy + " " + bz(-10.5),
                        "summon minecraft:husk " + bx(14.5) + " " + gy + " " + bz(-18.5),
                        "summon minecraft:husk " + bx(17.5) + " " + gy + " " + bz(-19.5),
                        "summon brasshaven:clockwork_spider " + bx(20.5) + " " + gy + " " + bz(-17.5),
                        "summon brasshaven:clockwork_spider " + bx(12.5) + " " + gy + " " + bz(-17.5),
                        "summon brasshaven:steam_drone " + bx(16.5) + " " + (gy + 3) + " " + bz(-14.5),
                        "tp @s " + bx(16.5) + " " + (gy + 4) + " " + bz(-4)))
                .run("hud on", () -> hud(true))
                .waitTicks(10)
                .add(beginOp("creatures", false))
                .add(cameraOp(11, () -> orbit(bx(16.5), gy, bz(-15.0), 10, 4.5, 170, 215, 1.0)))
                .add(endOp(false))
                .cmd(() -> List.of("kill @e[type=!minecraft:player,type=!brasshaven:wayfarer_npc,distance=..60]"));

        // ---- a boss: the Grand Clockmaker, its boss bar, and ENEMY FELLED
        CiDriver.step("boss")
                .cmd(() -> List.of("kill @e[type=minecraft:item]", "gamemode survival",
                        "effect give @s resistance infinite 4 true", "effect give @s regeneration infinite 2 true",
                        "effect give @s saturation infinite 0 true",
                        "item replace entity @s hotbar.0 with minecraft:netherite_sword",
                        "tp @s " + bx(0.5) + " " + gy + " " + bz(6.5) + " 180 0"))
                .run("hud on", () -> hud(true))
                .run("sword", () -> Minecraft.getInstance().player.getInventory().setSelectedSlot(0))
                .waitTicks(20)
                .cmd(() -> List.of("brasshaven boss grand_clockmaker"))
                .waitTicks(10)
                .add(beginOp("boss", false))
                .add(fightOp("brasshaven:grand_clockmaker", 10.0))
                .cmd(() -> List.of("kill @e[type=brasshaven:grand_clockmaker]"))
                .add(holdOp(4.0))
                .add(endOp(false))
                .cmd(() -> List.of("effect clear @s", "gamemode creative", "kill @e[type=minecraft:item]"));

        // ---- multiplayer: company, emotes, Pneumatic Post, Contract Board, secure trade
        CiDriver.step("company")
                .cmd(() -> List.of("brasshaven social demo", "brasshaven company sharexp"))
                .waitTicks(20)
                .run("open", com.brasshaven.client.social.ClientSocial::openCompany)
                .until("CompanyScreen", () -> CiDriver.screen() instanceof com.brasshaven.client.social.CompanyScreen, 60)
                .waitTicks(10)
                .add(beginOp("company", false))
                .add(holdOp(0.6))
                .add(glideOp(() -> rel(0.30, 0.40), 0.8))
                .add(holdOp(0.6))
                .add(glideOp(() -> widgetIndex(0), 0.8))
                .add(holdOp(1.0))
                .add(glideOp(() -> widgetIndex(1), 0.5))
                .add(holdOp(1.0))
                .add(endOp(false));

        CiDriver.step("emotes")
                .cmd(() -> List.of("gamemode creative", "tp @s " + bx(0.5) + " " + gy + " " + bz(0.5) + " 0 0"))
                .run("third person", () -> {
                    Minecraft.getInstance().options.setCameraType(CameraType.THIRD_PERSON_FRONT);
                    hud(false);
                })
                .waitTicks(20)
                .add(beginOp("emotes", false))
                .add(holdOp(0.4))
                .cmd(() -> List.of("brasshaven emote wave"))
                .add(holdOp(2.4))
                .run("wheel", () -> Minecraft.getInstance().gui.setScreen(new com.brasshaven.client.social.EmoteWheelScreen()))
                .add(holdOp(0.4))
                .add(glideOp(() -> emoteCell(0), 0.6))
                .add(holdOp(0.4))
                .add(glideOp(() -> emoteCell(1), 0.45))
                .add(holdOp(0.3))
                .add(glideOp(() -> emoteCell(2), 0.45))
                .add(holdOp(0.5))
                .add(clickOp())
                .add(holdOp(2.8))
                .add(endOp(false))
                .run("first person", () -> {
                    Minecraft.getInstance().options.setCameraType(CameraType.FIRST_PERSON);
                    hud(true);
                });

        CiDriver.step("pneumatic_post")
                .cmd(() -> List.of("setblock " + at(4, 0, 12) + " brasshaven:pneumatic_post[facing=south]",
                        "setblock " + at(-2, 0, 12) + " brasshaven:contract_board[facing=south]",
                        "give @s minecraft:paper 16", "give @s brasshaven:brass_nugget 8",
                        "tp @s " + bx(1.5) + " " + gy + " " + bz(15.5) + " 180 15"))
                .run("empty hand", () -> Minecraft.getInstance().player.getInventory().setSelectedSlot(8))
                .waitTicks(20)
                .add(beginOp("pneumatic_post", false))
                .add(holdOp(0.5))
                .run("use", () -> useAt(4, 0, 12))
                .until("PostScreen", () -> CiDriver.screen() instanceof com.brasshaven.client.social.PostScreen, 100)
                .add(holdOp(0.6))
                .add(glideOp(() -> rel(0.36, 0.30), 0.8))
                .add(holdOp(0.6))
                .add(clickOp())
                .add(holdOp(1.6))
                .add(endOp(false));

        CiDriver.step("contract_board")
                .run("use", () -> useAt(-2, 0, 12))
                .until("ContractScreen", () -> CiDriver.screen() instanceof com.brasshaven.client.social.ContractScreen, 100)
                .add(beginOp("contract_board", false))
                .add(holdOp(0.6))
                .add(glideOp(() -> rel(0.26, 0.32), 0.8))
                .add(holdOp(0.5))
                .add(clickOp())
                .add(holdOp(1.2))
                .add(glideOp(() -> rel(0.30, 0.38), 0.5))
                .add(holdOp(1.2))
                .add(endOp(false));

        CiDriver.step("trade")
                .run("open", CiDriver::previewTrade)
                .until("TradeScreen", () -> CiDriver.screen() instanceof com.brasshaven.client.social.TradeScreen, 20)
                .add(beginOp("trade", false))
                .add(holdOp(0.6))
                .add(glideOp(() -> rel(0.38, 0.16), 0.8))
                .add(holdOp(1.0))
                .add(glideOp(() -> rel(0.62, 0.16), 0.7))
                .add(holdOp(1.2))
                .add(endOp(false));

        // ---- the Manual: turning pages, the keys page
        CiDriver.step("manual")
                .run("open", () -> ClientHooks.openGuide("welcome"))
                .until("GuideScreen", () -> CiDriver.screen() instanceof com.brasshaven.client.gui.GuideScreen, 40)
                .waitTicks(10)
                .add(beginOp("manual", false))
                .add(holdOp(1.2))
                .add(glideOp(() -> widgetField("next"), 0.9))
                .add(holdOp(0.3))
                .add(clickOp())
                .add(holdOp(1.3))
                .run("keys", () -> ClientHooks.openGuide("keys"))
                .add(holdOp(2.6))
                .add(endOp(false));

        // ---- the three Brasshaven biomes, seen from the air
        biomeScene("crimson_mire");
        biomeScene("volcanic_highlands");
        biomeScene("pale_dunes");

        structureScene("sky_harbour", "sky_harbour", 0, -700, 120, 190, 10);
    }

    /** A structure placed with /place structure far from the rest, then an orbit around its bounding box. */
    private static void structureScene(String scene, String id, int dx, int dz, double a0, double a1, double seconds) {
        CiDriver.step(scene)
                .cmd(() -> List.of("gamemode spectator", "forceload remove all"))
                .run("hud off", () -> hud(false))
                .server("locate " + id, (server, player) -> prepareStructure(server, scene, id, CiDriver.bx + dx, CiDriver.bz + dz))
                .cmd(() -> {
                    BoundingBox b = BOXES.get(scene);
                    return List.of("tp @s " + (b.minX() + b.maxX()) / 2 + " " + (b.maxY() + 20) + " " + (b.minZ() + b.maxZ()) / 2);
                })
                .waitTicks(60)
                .retry("place " + id, () -> List.of("place structure brasshaven:" + id + " " + (CiDriver.bx + dx) + " 64 " + (CiDriver.bz + dz)),
                        100, 30)
                .cmd(() -> {
                    double[] p = orbitFor(scene, a0, a1).at(0);
                    return List.of("tp @s " + p[0] + " " + p[1] + " " + p[2]);
                })
                .settleChunks(3000)
                .waitTicks(40)
                .add(beginOp(scene, false))
                .add(cameraOp(seconds, () -> orbitFor(scene, a0, a1)))
                .add(endOp(false));
    }

    /** A Brasshaven biome found with the same search as /locate biome, then a slow glide above it. */
    private static void biomeScene(String biome) {
        String scene = "biome_" + biome;
        CiDriver.step(scene)
                .cmd(() -> List.of("gamemode spectator", "forceload remove all"))
                .run("hud off", () -> hud(false))
                .server("locate " + biome, (server, player) -> locateBiome(server, player, scene, biome))
                .cmd(() -> {
                    double[] s = SPOTS.get(scene);
                    return List.of("tp @s " + s[0] + " " + s[1] + " " + s[2]);
                })
                .settleChunks(3000)
                .waitTicks(40)
                .add(beginOp(scene, false))
                .add(cameraOp(9, () -> {
                    double[] s = SPOTS.get(scene);
                    return line(s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7], s[6] + 12);
                }))
                .add(endOp(false));
    }

    // ------------------------------------------------------------------ server-side preparation

    private static List<String> prepareClearing(IntegratedServer server, ServerPlayer player) {
        ServerLevel level = server.overworld();
        level.getChunk(CiDriver.bx >> 4, CiDriver.bz >> 4);
        gy = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, CiDriver.bx, CiDriver.bz);
        CiDriver.LOGGER.info(TAG + "clearing at {} {} {}", CiDriver.bx, gy, CiDriver.bz);
        int r = 24;
        List<String> out = new ArrayList<>();
        // each /fill stays under the 32768 block limit
        for (int y = gy; y < gy + 40; y += 12) {
            out.add("fill " + (CiDriver.bx - r) + " " + y + " " + (CiDriver.bz - r) + " " + (CiDriver.bx + r) + " "
                    + Math.min(y + 11, gy + 39) + " " + (CiDriver.bz + r) + " minecraft:air");
        }
        out.add("fill " + (CiDriver.bx - r) + " " + (gy - 4) + " " + (CiDriver.bz - r) + " " + (CiDriver.bx + r) + " " + (gy - 2) + " "
                + (CiDriver.bz + r) + " minecraft:dirt");
        out.add("fill " + (CiDriver.bx - r) + " " + (gy - 1) + " " + (CiDriver.bz - r) + " " + (CiDriver.bx + r) + " " + (gy - 1) + " "
                + (CiDriver.bz + r) + " minecraft:grass_block");
        // a cobbled path through the clearing
        out.add("fill " + (CiDriver.bx - 1) + " " + (gy - 1) + " " + (CiDriver.bz - r) + " " + (CiDriver.bx + 1) + " " + (gy - 1) + " "
                + (CiDriver.bz + r) + " minecraft:dirt_path");
        return out;
    }

    private static List<String> prepareStructure(IntegratedServer server, String scene, String id, int x, int z) {
        ServerLevel level = server.overworld();
        BlockPos pos = new BlockPos(x, 64, z);
        Holder.Reference<Structure> holder = level.registryAccess().lookupOrThrow(Registries.STRUCTURE)
                .get(Brasshaven.id(id))
                .orElseThrow(() -> new IllegalStateException("no structure brasshaven:" + id));
        ChunkGenerator generator = level.getChunkSource().getGenerator();
        StructureStart start = com.brasshaven.world.SiteFit.unchecked(() -> holder.value().generate(holder, level.dimension(),
                level.registryAccess(), generator, generator.getBiomeSource(), level.getChunkSource().randomState(),
                level.getStructureManager(), level.getSeed(), ChunkPos.containing(pos), 0, level, b -> true));
        if (!start.isValid()) {
            throw new IllegalStateException(id + " did not generate at " + pos);
        }
        BoundingBox box = start.getBoundingBox();
        BOXES.put(scene, box);
        CiDriver.LOGGER.info(TAG + "{} bounding box {}", id, box);
        List<String> out = new ArrayList<>();
        int minCx = (box.minX() >> 4) - 1;
        int maxCx = (box.maxX() >> 4) + 1;
        for (int chz = (box.minZ() >> 4) - 1; chz <= (box.maxZ() >> 4) + 1; chz++) {
            out.add("forceload add " + (minCx * 16) + " " + (chz * 16) + " " + (maxCx * 16) + " " + (chz * 16));
        }
        return out;
    }

    /** Finds the biome around the spawn (same search as /locate biome) and plans a glide over it. */
    private static List<String> locateBiome(IntegratedServer server, ServerPlayer player, String scene, String biome) {
        ServerLevel level = server.overworld();
        ResourceKey<Biome> key = ResourceKey.create(Registries.BIOME, Brasshaven.id(biome));
        var found = level.findClosestBiome3d(h -> h.is(key), new BlockPos(CiDriver.bx, 64, CiDriver.bz), 6400, 32, 64);
        if (found == null) {
            throw new IllegalStateException("no " + biome + " within 6400 blocks (is the brasshaven:custom_biomes pack on?)");
        }
        BlockPos p = found.getFirst();
        int x0 = p.getX() - 36;
        int x1 = p.getX() + 36;
        int z0 = p.getZ() + 30;
        int z1 = p.getZ() + 10;
        int top = 0;
        for (int[] c : new int[][] {{x0, z0}, {x1, z1}, {p.getX(), p.getZ()}, {(x0 + x1) / 2, z0}}) {
            level.getChunk(c[0] >> 4, c[1] >> 4);
            top = Math.max(top, level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, c[0], c[1]));
        }
        double y = top + 30;
        // glide east while looking north-east and down at the biome
        SPOTS.put(scene, new double[] {x0, y, z0, x1, y + 6, z1, -150, 28});
        CiDriver.LOGGER.info(TAG + "{} at {}, glide at y {}", biome, p, y);
        return List.of();
    }

    private static List<String> farmCommands() {
        // field of 9 x 9 around (-14, 10): farmland under ripe wheat, the harvester in the middle with a chest on its
        // west side, two sprinklers in opposite corners
        int cx = -14;
        int cz = 10;
        List<String> out = new ArrayList<>();
        out.add("fill " + at(cx - 4, -1, cz - 4) + " " + at(cx + 4, -1, cz + 4) + " minecraft:farmland[moisture=7]");
        out.add("fill " + at(cx - 4, 0, cz - 4) + " " + at(cx + 4, 0, cz + 4) + " minecraft:wheat[age=7]");
        out.add("fill " + at(cx - 5, -1, cz - 5) + " " + at(cx + 5, -1, cz - 5) + " minecraft:oak_planks");
        out.add("fill " + at(cx - 5, -1, cz + 5) + " " + at(cx + 5, -1, cz + 5) + " minecraft:oak_planks");
        out.add("fill " + at(cx - 5, -1, cz - 4) + " " + at(cx - 5, -1, cz + 4) + " minecraft:oak_planks");
        out.add("fill " + at(cx + 5, -1, cz - 4) + " " + at(cx + 5, -1, cz + 4) + " minecraft:oak_planks");
        out.add("setblock " + at(cx, -1, cz) + " minecraft:stone_bricks");
        out.add("setblock " + at(cx, 0, cz) + " brasshaven:auto_harvester");
        out.add("setblock " + at(cx - 1, -1, cz) + " minecraft:stone_bricks");
        out.add("setblock " + at(cx - 1, 0, cz) + " minecraft:chest");
        out.add("setblock " + at(cx - 3, -1, cz - 3) + " minecraft:stone_bricks");
        out.add("setblock " + at(cx - 3, 0, cz - 3) + " brasshaven:sprinkler");
        out.add("setblock " + at(cx + 3, -1, cz + 3) + " minecraft:stone_bricks");
        out.add("setblock " + at(cx + 3, 0, cz + 3) + " brasshaven:sprinkler");
        return out;
    }

    private static List<String> storageCommands() {
        List<String> out = new ArrayList<>();
        String[][] chests = {
                {"minecraft:diamond 12", "minecraft:iron_ingot 40", "minecraft:oak_log 64", "minecraft:gold_ingot 18",
                        "minecraft:redstone 64", "minecraft:bread 24"},
                {"brasshaven:brass_ingot 32", "brasshaven:zinc_ingot 20", "minecraft:copper_ingot 48", "minecraft:iron_ore 16",
                        "minecraft:raw_iron 27", "minecraft:emerald 9"},
                {"minecraft:cobblestone 64", "minecraft:coal 40", "minecraft:wheat 64", "minecraft:iron_pickaxe 1",
                        "minecraft:lapis_lazuli 30", "minecraft:iron_block 4"},
        };
        for (int c = 0; c < chests.length; c++) {
            String pos = at(12 + c, 0, 4);
            out.add("setblock " + pos + " minecraft:chest");
            for (int i = 0; i < chests[c].length; i++) {
                out.add("item replace block " + pos + " container." + i + " with " + chests[c][i]);
            }
        }
        out.add("setblock " + at(10, 0, 2) + " brasshaven:guild_terminal");
        return out;
    }

    // ------------------------------------------------------------------ scene marks and the log

    private static final class Scene {
        final String name;
        final long begin;
        final double slow;
        final boolean calibration;
        long end;
        String status = "open";
        String error;
        final List<double[]> cursor = new ArrayList<>();
        double fps;

        Scene(String name, long begin, double slow, boolean calibration) {
            this.name = name;
            this.begin = begin;
            this.slow = slow;
            this.calibration = calibration;
        }
    }

    /** Seconds of footage since the scene began (the wall clock divided by the slow-motion factor). */
    private static double time() {
        return current == null ? 0 : (System.currentTimeMillis() - current.begin) / 1000.0 / current.slow;
    }

    private static CiDriver.Op beginOp(String name, boolean calibration) {
        return new CiDriver.Op("begin " + name) {
            CompletableFuture<List<String>> pending;

            @Override
            boolean tick() {
                Minecraft mc = Minecraft.getInstance();
                double k = calibration ? 1.0 : slowmo;
                if (pending == null) {
                    mc.gui.toastManager().clear();
                    mc.gui.hud.getChat().clearMessages(false);
                    pending = CiDriver.runCommands(List.of("tick rate " + fmt(20.0 / k)));
                }
                if (!pending.isDone()) {
                    return false;
                }
                current = new Scene(name, System.currentTimeMillis(), k, calibration);
                current.fps = measuredFps;
                cam = null;
                glide = null;
                cursor = null;
                frames = 0;
                CiDriver.LOGGER.info(TAG + "SCENE BEGIN {} {} slowmo {}", name, current.begin, fmt(k));
                return true;
            }
        };
    }

    private static CiDriver.Op endOp(boolean calibration) {
        return new CiDriver.Op("end") {
            CompletableFuture<List<String>> pending;

            @Override
            boolean tick() {
                if (current == null) {
                    return true;
                }
                if (pending == null) {
                    current.end = System.currentTimeMillis();
                    double wall = (current.end - current.begin) / 1000.0;
                    double fps = wall > 0 ? frames / wall : 0;
                    current.fps = fps;
                    current.status = "ok";
                    if (cursor != null) {
                        current.cursor.add(new double[] {time(), -1, -1, 0});
                    }
                    CiDriver.LOGGER.info(TAG + "SCENE END {} {} ({} rendered frames in {} s: {} fps)", current.name, current.end,
                            frames, fmt(wall), fmt(fps));
                    if (calibration) {
                        measuredFps = fps;
                        slowmo = FORCED_SLOWMO > 0 ? FORCED_SLOWMO
                                : Math.max(1.0, Math.min(MAX_SLOWMO, Math.ceil(TARGET_FPS / Math.max(0.5, fps))));
                        CiDriver.LOGGER.info(TAG + "measured {} fps, filming at slow motion x{}", fmt(fps), fmt(slowmo));
                        CiDriver.line("PASS calibrate (" + fmt(fps) + " fps, slow motion x" + fmt(slowmo) + ")");
                    }
                    SCENES.add(current);
                    current = null;
                    cam = null;
                    glide = null;
                    cursor = null;
                    writeLog("running");
                    pending = CiDriver.runCommands(List.of("tick rate 20"));
                }
                return pending.isDone();
            }
        };
    }

    static void writeLog(String why) {
        Minecraft mc = Minecraft.getInstance();
        List<Scene> all = new ArrayList<>(SCENES);
        if (current != null) {
            all.add(current);
        }
        StringBuilder sb = new StringBuilder();
        Window w = mc.getWindow();
        sb.append("{\n  \"state\": \"").append(why).append("\",\n");
        sb.append("  \"window\": [").append(w.getScreenWidth()).append(", ").append(w.getScreenHeight()).append("],\n");
        sb.append("  \"gui_scale\": ").append(w.getGuiScale()).append(",\n");
        sb.append("  \"language\": \"").append(mc.options.languageCode).append("\",\n");
        sb.append("  \"measured_fps\": ").append(fmt(measuredFps)).append(",\n");
        sb.append("  \"slowmo\": ").append(fmt(slowmo)).append(",\n");
        sb.append("  \"scenes\": [");
        for (int i = 0; i < all.size(); i++) {
            Scene s = all.get(i);
            sb.append(i == 0 ? "\n" : ",\n");
            sb.append("    {\"name\": \"").append(s.name).append("\", \"begin_ms\": ").append(s.begin)
                    .append(", \"end_ms\": ").append(s.end).append(", \"slowmo\": ").append(fmt(s.slow))
                    .append(", \"fps\": ").append(fmt(s.fps)).append(", \"calibration\": ").append(s.calibration)
                    .append(", \"status\": \"").append(s.status).append("\"");
            if (s.error != null) {
                sb.append(", \"error\": \"").append(s.error.replace("\\", "/").replace("\"", "'")).append("\"");
            }
            sb.append(", \"cursor\": [");
            for (int j = 0; j < s.cursor.size(); j++) {
                double[] c = s.cursor.get(j);
                sb.append(j == 0 ? "" : ", ").append("[").append(fmt3(c[0])).append(", ").append(Math.round(c[1])).append(", ")
                        .append(Math.round(c[2])).append(", ").append((int) c[3]).append("]");
            }
            sb.append("]}");
        }
        sb.append("\n  ]\n}\n");
        try {
            File dir = new File(mc.gameDirectory, "showcase");
            dir.mkdirs();
            Files.writeString(new File(dir, "scenes.json").toPath(), sb.toString(), StandardCharsets.UTF_8);
        } catch (IOException | RuntimeException e) {
            CiDriver.LOGGER.error(TAG + "could not write the scene log", e);
        }
    }

    // ------------------------------------------------------------------ camera

    @FunctionalInterface
    interface Path {
        /** x, y, z of the eye, yaw, pitch at u in [0, 1]. */
        double[] at(double u);
    }

    private static final class Cam {
        final Path path;
        final double start;
        final double seconds;

        Cam(Path path, double start, double seconds) {
            this.path = path;
            this.start = start;
            this.seconds = seconds;
        }

        void apply(Minecraft mc, double t) {
            double u = seconds <= 0 ? 1.0 : Math.max(0.0, Math.min(1.0, (t - start) / seconds));
            double[] p = path.at(u);
            var player = mc.player;
            double y = p[1] - player.getEyeHeight();
            player.setDeltaMovement(Vec3.ZERO);
            player.setPos(p[0], y, p[2]);
            player.xo = p[0];
            player.yo = y;
            player.zo = p[2];
            player.xOld = p[0];
            player.yOld = y;
            player.zOld = p[2];
            float yaw = (float) p[3];
            float pitch = (float) p[4];
            player.setYRot(yaw);
            player.setXRot(pitch);
            player.yRotO = yaw;
            player.xRotO = pitch;
            player.setYHeadRot(yaw);
            player.yHeadRotO = yaw;
        }
    }

    private static CiDriver.Op cameraOp(double seconds, Supplier<Path> path) {
        return new CiDriver.Op("camera " + seconds + "s") {
            double start = -1;

            @Override
            boolean tick() {
                if (start < 0) {
                    start = time();
                    cam = new Cam(path.get(), start, seconds);
                }
                return time() - start >= seconds;
            }
        };
    }

    /** Straight glide from one eye position to another; yaw and pitch go from (yaw0, pitch) to (yaw1, pitch). */
    private static Path line(double x0, double y0, double z0, double x1, double y1, double z1, double yaw0, double pitch, double yaw1) {
        return u -> {
            double e = easeSoft(u);
            return new double[] {x0 + (x1 - x0) * e, y0 + (y1 - y0) * e, z0 + (z1 - z0) * e, yaw0 + (yaw1 - yaw0) * e, pitch};
        };
    }

    /** Arc around (cx, cy, cz) at a radius and a height above cy, from angle a0 to a1 (degrees), looking at the centre. */
    private static Path orbit(double cx, double cy, double cz, double radius, double height, double a0, double a1, double lookUp) {
        return u -> {
            double a = Math.toRadians(a0 + (a1 - a0) * easeSoft(u));
            double x = cx + Math.cos(a) * radius;
            double z = cz + Math.sin(a) * radius;
            double y = cy + height;
            double[] look = look(x, y, z, cx, cy + lookUp, cz);
            return new double[] {x, y, z, look[0], look[1]};
        };
    }

    /** The orbit that frames a placed structure: a slow arc at about 25 degrees above its middle. */
    private static Path orbitFor(String scene, double a0, double a1) {
        BoundingBox b = BOXES.get(scene);
        double cx = (b.minX() + b.maxX() + 1) / 2.0;
        double cz = (b.minZ() + b.maxZ() + 1) / 2.0;
        double size = Math.max(b.maxX() - b.minX(), b.maxZ() - b.minZ());
        double h = b.maxY() - b.minY();
        double radius = size * 0.85 + 22;
        double lookY = b.minY() + h * 0.42;
        double height = Math.max(h * 0.35, radius * 0.42);
        return orbit(cx, lookY, cz, radius, height, a0, a1, 0);
    }

    private static double[] look(double x, double y, double z, double tx, double ty, double tz) {
        double dx = tx - x;
        double dy = ty - y;
        double dz = tz - z;
        double yaw = Math.toDegrees(Math.atan2(-dx, dz));
        double pitch = -Math.toDegrees(Math.atan2(dy, Math.sqrt(dx * dx + dz * dz)));
        return new double[] {yaw, pitch};
    }

    // ------------------------------------------------------------------ cursor, clicks, keys

    private static final class Glide {
        final double[] from;
        final double[] to;
        final double start;
        final double seconds;

        Glide(double[] from, double[] to, double start, double seconds) {
            this.from = from;
            this.to = to;
            this.start = start;
            this.seconds = seconds;
        }
    }

    private static CiDriver.Op glideOp(Supplier<double[]> target, double seconds) {
        return new CiDriver.Op("glide") {
            double start = -1;

            @Override
            boolean tick() {
                if (start < 0) {
                    Screen s = CiDriver.screen();
                    if (s == null) {
                        throw new IllegalStateException("no screen to move the cursor over");
                    }
                    double[] to = target.get();
                    if (to == null) {
                        // a missing widget costs one gesture, not the whole scene
                        CiDriver.LOGGER.warn(TAG + "cursor target not found on {}, skipping the glide", s.getClass().getSimpleName());
                        return true;
                    }
                    double[] from = cursor != null ? cursor.clone() : new double[] {s.width * 0.55, s.height * 0.75};
                    start = time();
                    glide = new Glide(from, to, start, seconds);
                }
                return time() - start >= seconds;
            }
        };
    }

    private static void moveCursor(Minecraft mc, double[] p, double t) {
        Screen s = mc.gui.screen();
        if (s == null) {
            return;
        }
        double[] last = cursor;
        cursor = p;
        Window w = mc.getWindow();
        double sx = (double) w.getScreenWidth() / w.getGuiScaledWidth();
        double sy = (double) w.getScreenHeight() / w.getGuiScaledHeight();
        setMouse(mc, p[0] * sx, p[1] * sy);
        s.mouseMoved(p[0], p[1]);
        if (dragging && last != null) {
            s.mouseDragged(new MouseButtonEvent(p[0], p[1], new MouseButtonInfo(0, 0)), p[0] - last[0], p[1] - last[1]);
        }
        logCursor(t);
    }

    private static void hideCursor(double t) {
        cursor = null;
        if (current != null) {
            current.cursor.add(new double[] {t, -1, -1, 0});
        }
    }

    private static void logCursor(double t) {
        if (current == null || cursor == null) {
            return;
        }
        Window w = Minecraft.getInstance().getWindow();
        double sx = (double) w.getScreenWidth() / w.getGuiScaledWidth();
        double sy = (double) w.getScreenHeight() / w.getGuiScaledHeight();
        double[] e = {t, cursor[0] * sx, cursor[1] * sy, pressed ? 1 : 0};
        List<double[]> log = current.cursor;
        if (!log.isEmpty()) {
            double[] prev = log.get(log.size() - 1);
            if (Math.abs(prev[1] - e[1]) < 0.5 && Math.abs(prev[2] - e[2]) < 0.5 && prev[3] == e[3]) {
                return;
            }
        }
        log.add(e);
    }

    /** MouseHandler keeps the cursor in private fields; the screens read it from there when they draw hovers. */
    private static void setMouse(Minecraft mc, double x, double y) {
        try {
            Field fx = mc.mouseHandler.getClass().getDeclaredField("xpos");
            Field fy = mc.mouseHandler.getClass().getDeclaredField("ypos");
            fx.setAccessible(true);
            fy.setAccessible(true);
            fx.setDouble(mc.mouseHandler, x);
            fy.setDouble(mc.mouseHandler, y);
        } catch (ReflectiveOperationException | RuntimeException e) {
            // the hover effects are lost, the clicks still work
        }
    }

    private static CiDriver.Op clickOp() {
        return new CiDriver.Op("click") {
            double pressedAt = -1;

            @Override
            boolean tick() {
                Screen s = CiDriver.screen();
                if (cursor == null) {
                    CiDriver.LOGGER.warn(TAG + "click without a cursor, skipped");
                    return true;
                }
                double[] p = cursor.clone();
                if (pressedAt < 0) {
                    pressed = true;
                    logCursor(time());
                    pressedAt = time();
                    if (s != null) {
                        s.mouseClicked(new MouseButtonEvent(p[0], p[1], new MouseButtonInfo(0, 0)), false);
                    }
                    return false;
                }
                if (time() - pressedAt < 0.14) {
                    return false;
                }
                pressed = false;
                Screen now = CiDriver.screen();
                if (now != null) {
                    now.mouseReleased(new MouseButtonEvent(p[0], p[1], new MouseButtonInfo(0, 0)));
                    logCursor(time());
                } else {
                    hideCursor(time());
                }
                return true;
            }
        };
    }

    /** Press, move by (dx, dy) GUI pixels, release. */
    private static CiDriver.Op dragOp(double dx, double dy, double seconds) {
        return new CiDriver.Op("drag") {
            double start = -1;

            @Override
            boolean tick() {
                Screen s = CiDriver.screen();
                if (s == null || cursor == null) {
                    throw new IllegalStateException("drag without a screen or a cursor");
                }
                if (start < 0) {
                    double[] p = cursor.clone();
                    s.mouseClicked(new MouseButtonEvent(p[0], p[1], new MouseButtonInfo(0, 0)), false);
                    pressed = true;
                    dragging = true;
                    logCursor(time());
                    start = time();
                    glide = new Glide(p, new double[] {p[0] + dx, p[1] + dy}, start, seconds);
                    return false;
                }
                if (time() - start < seconds + 0.05) {
                    return false;
                }
                dragging = false;
                pressed = false;
                s.mouseReleased(new MouseButtonEvent(cursor[0], cursor[1], new MouseButtonInfo(0, 0)));
                logCursor(time());
                return true;
            }
        };
    }

    private static CiDriver.Op scrollOp(double amount) {
        return new CiDriver.Op("scroll") {
            @Override
            boolean tick() {
                Screen s = CiDriver.screen();
                if (s != null && cursor != null) {
                    s.mouseScrolled(cursor[0], cursor[1], 0, amount);
                }
                return true;
            }
        };
    }

    private static CiDriver.Op keyOp(int key) {
        return new CiDriver.Op("key " + key) {
            @Override
            boolean tick() {
                Screen s = CiDriver.screen();
                if (s != null) {
                    s.keyPressed(new KeyEvent(key, 0, 0));
                    if (CiDriver.screen() != null) {
                        CiDriver.screen().keyReleased(new KeyEvent(key, 0, 0));
                    }
                }
                return true;
            }
        };
    }

    private static CiDriver.Op typeOp(String text, double perChar) {
        return new CiDriver.Op("type " + text) {
            double start = -1;
            int typed;

            @Override
            boolean tick() {
                if (start < 0) {
                    start = time();
                }
                Screen s = CiDriver.screen();
                while (s != null && typed < text.length() && time() - start >= typed * perChar) {
                    s.charTyped(new CharacterEvent(text.charAt(typed)));
                    typed++;
                }
                return typed >= text.length() || s == null;
            }
        };
    }

    /** Waits a number of footage seconds. */
    private static CiDriver.Op holdOp(double seconds) {
        return new CiDriver.Op("hold " + seconds + "s") {
            double start = -1;

            @Override
            boolean tick() {
                if (start < 0) {
                    start = time();
                }
                return time() - start >= seconds;
            }
        };
    }

    // ------------------------------------------------------------------ gameplay actions

    /** Aims at the nearest husk and uses the staff in the given hotbar slot, then waits. */
    private static CiDriver.Op castOp(int slot, double wait) {
        return new CiDriver.Op("cast") {
            double start = -1;
            boolean castDone;

            @Override
            boolean tick() {
                Minecraft mc = Minecraft.getInstance();
                if (start < 0) {
                    start = time();
                    Entity target = nearest("minecraft:husk", 24);
                    double[] from = {mc.player.getYRot(), mc.player.getXRot()};
                    double[] to = target == null ? from
                            : look(mc.player.getX(), mc.player.getEyeY(), mc.player.getZ(), target.getX(), target.getY() + 1.0, target.getZ());
                    double yaw = from[0] + wrap(to[0] - from[0]);
                    cam = new Cam(u -> new double[] {mc.player.getX(), mc.player.getEyeY(), mc.player.getZ(),
                            from[0] + (yaw - from[0]) * ease(u), from[1] + (to[1] - from[1]) * ease(u)}, start, 0.35);
                    return false;
                }
                if (!castDone && time() - start >= 0.4) {
                    castDone = true;
                    mc.player.getInventory().setSelectedSlot(slot);
                    mc.gameMode.useItem(mc.player, InteractionHand.MAIN_HAND);
                    mc.player.swing(InteractionHand.MAIN_HAND);
                }
                return time() - start >= 0.4 + wait;
            }
        };
    }

    /** Faces the boss on every frame and swings at it whenever it is in reach, for a number of footage seconds. */
    private static CiDriver.Op fightOp(String type, double seconds) {
        return new CiDriver.Op("fight") {
            double start = -1;
            double lastHit = -10;

            @Override
            boolean tick() {
                Minecraft mc = Minecraft.getInstance();
                if (start < 0) {
                    start = time();
                    double px = mc.player.getX();
                    double py = mc.player.getY();
                    double pz = mc.player.getZ();
                    float[] aim = {mc.player.getYRot(), mc.player.getXRot()};
                    cam = new Cam(u -> {
                        Entity boss = nearest(type, 40);
                        if (boss != null) {
                            double[] to = look(px, py + mc.player.getEyeHeight(), pz, boss.getX(), boss.getY() + boss.getBbHeight() * 0.6, boss.getZ());
                            aim[0] += (float) (wrap(to[0] - aim[0]) * 0.12);
                            aim[1] += (float) ((Math.max(-30, Math.min(30, to[1])) - aim[1]) * 0.12);
                        }
                        return new double[] {px, py + mc.player.getEyeHeight(), pz, aim[0], aim[1]};
                    }, start, seconds);
                }
                Entity boss = nearest(type, 40);
                if (boss != null && time() - lastHit > 0.65 && boss.distanceTo(mc.player) < 4.5) {
                    lastHit = time();
                    mc.gameMode.attack(mc.player, boss);
                    mc.player.swing(InteractionHand.MAIN_HAND);
                }
                return time() - start >= seconds;
            }
        };
    }

    // ------------------------------------------------------------------ helpers

    private static void hud(boolean visible) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.gui.hud.isHidden() == visible) {
            mc.gui.hud.toggle();
        }
    }

    private static String at(int dx, int dy, int dz) {
        return (CiDriver.bx + dx) + " " + (gy + dy) + " " + (CiDriver.bz + dz);
    }

    private static double bx(double dx) {
        return CiDriver.bx + dx;
    }

    private static double bz(double dz) {
        return CiDriver.bz + dz;
    }

    private static void useAt(int dx, int dy, int dz) {
        Minecraft mc = Minecraft.getInstance();
        BlockPos pos = new BlockPos(CiDriver.bx + dx, gy + dy, CiDriver.bz + dz);
        mc.gameMode.useItemOn(mc.player, InteractionHand.MAIN_HAND, new BlockHitResult(Vec3.atCenterOf(pos), Direction.UP, pos, false));
    }

    private static Entity nearest(String type, double range) {
        Minecraft mc = Minecraft.getInstance();
        Entity best = null;
        double bestD = range * range;
        for (Entity e : mc.level.entitiesForRendering()) {
            if (e.isAlive() && type.equals(EntityType.getKey(e.getType()).toString())) {
                double d = e.distanceToSqr(mc.player);
                if (d < bestD) {
                    bestD = d;
                    best = e;
                }
            }
        }
        return best;
    }

    /** A point of the current screen as fractions of its size. */
    private static double[] rel(double fx, double fy) {
        Screen s = CiDriver.screen();
        return s == null ? null : new double[] {s.width * fx, s.height * fy};
    }

    /** Centre of a widget held in a field of the current screen (an AbstractWidget). */
    private static double[] widgetField(String name) {
        Object w = field(CiDriver.screen(), name);
        return w instanceof AbstractWidget a ? centre(a) : null;
    }

    /** Centre of the n-th widget of the current screen. */
    private static double[] widgetIndex(int n) {
        Screen s = CiDriver.screen();
        if (s == null) {
            return null;
        }
        int i = 0;
        for (GuiEventListener l : s.children()) {
            if (l instanceof AbstractWidget a && a.visible) {
                if (i++ == n) {
                    return centre(a);
                }
            }
        }
        return null;
    }

    private static double[] centre(AbstractWidget a) {
        return new double[] {a.getX() + a.getWidth() / 2.0, a.getY() + a.getHeight() / 2.0};
    }

    /** One of the round tool buttons of the world map, counted from the end (-1: options, -2: 3D view). */
    private static double[] mapButton(int fromEnd) {
        Object list = field(CiDriver.screen(), "buttons");
        if (!(list instanceof List<?> buttons) || buttons.isEmpty()) {
            return null;
        }
        List<double[]> tools = new ArrayList<>();
        int x0 = Integer.MIN_VALUE;
        for (Object b : buttons) {
            int x = (int) call(b, "x");
            int w = (int) call(b, "w");
            int h = (int) call(b, "h");
            if (w == 16 && h == 16) {
                if (x0 == Integer.MIN_VALUE) {
                    x0 = x;
                }
                if (x == x0) {
                    tools.add(new double[] {x + 8, (int) call(b, "y") + 8});
                }
            }
        }
        int i = tools.size() + fromEnd;
        return i >= 0 && i < tools.size() ? tools.get(i) : null;
    }

    /** Centre of a talent node: the first talent of a branch at a given row. */
    private static double[] skillNode(String branch, int row) {
        Screen s = CiDriver.screen();
        for (GeneratedSkills.Skill skill : GeneratedSkills.SKILLS) {
            if (skill.branch().equals(branch) && skill.row() == row) {
                Method nx = method(s, "nodeX", 1);
                Method ny = method(s, "nodeY", 1);
                try {
                    return new double[] {(int) nx.invoke(s, skill) + 11, (int) ny.invoke(s, skill) + 11};
                } catch (ReflectiveOperationException e) {
                    throw new IllegalStateException(e);
                }
            }
        }
        return null;
    }

    /** Centre of one cell of the emote wheel. */
    private static double[] emoteCell(int i) {
        Screen s = CiDriver.screen();
        Object cx = field(s, "cx");
        Object cy = field(s, "cy");
        if (!(cx instanceof Integer x) || !(cy instanceof Integer y)) {
            return null;
        }
        double a = i * Math.PI * 2 / 8;
        return new double[] {x + Math.sin(a) * 62, y - Math.cos(a) * 62};
    }

    private static Object field(Object o, String name) {
        if (o == null) {
            return null;
        }
        for (Class<?> c = o.getClass(); c != null; c = c.getSuperclass()) {
            try {
                Field f = c.getDeclaredField(name);
                f.setAccessible(true);
                return f.get(o);
            } catch (NoSuchFieldException e) {
                // try the superclass
            } catch (ReflectiveOperationException | RuntimeException e) {
                return null;
            }
        }
        return null;
    }

    private static Method method(Object o, String name, int params) {
        for (Class<?> c = o.getClass(); c != null; c = c.getSuperclass()) {
            for (Method m : c.getDeclaredMethods()) {
                if (m.getName().equals(name) && m.getParameterCount() == params) {
                    m.setAccessible(true);
                    return m;
                }
            }
        }
        throw new IllegalStateException("no method " + name + " on " + o.getClass().getName());
    }

    private static Object call(Object o, String name) {
        try {
            return method(o, name, 0).invoke(o);
        } catch (ReflectiveOperationException e) {
            throw new IllegalStateException(e);
        }
    }

    private static double ease(double u) {
        return u <= 0 ? 0 : u >= 1 ? 1 : 0.5 - 0.5 * Math.cos(Math.PI * u);
    }

    /** Linear in the middle, eased at both ends: a camera move that starts and stops softly. */
    private static double easeSoft(double u) {
        return 0.65 * u + 0.35 * ease(u);
    }

    private static double wrap(double degrees) {
        double d = degrees % 360.0;
        if (d > 180) {
            d -= 360;
        } else if (d < -180) {
            d += 360;
        }
        return d;
    }

    private static double parseDouble(String s) {
        try {
            return Double.parseDouble(s);
        } catch (NumberFormatException e) {
            return 0;
        }
    }

    private static String fmt(double v) {
        return String.format(Locale.ROOT, "%.2f", v);
    }

    private static String fmt3(double v) {
        return String.format(Locale.ROOT, "%.3f", v);
    }
}
