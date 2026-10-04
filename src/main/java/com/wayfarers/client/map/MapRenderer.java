package com.wayfarers.client.map;

import com.mojang.blaze3d.systems.RenderSystem;
import com.mojang.blaze3d.textures.FilterMode;
import com.mojang.blaze3d.textures.GpuSampler;
import com.wayfarers.Wayfarers;
import com.wayfarers.map.MapProtocol;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.PlayerFaceExtractor;
import net.minecraft.client.multiplayer.PlayerInfo;
import net.minecraft.client.renderer.RenderPipelines;
import net.minecraft.client.renderer.texture.DynamicTexture;
import net.minecraft.resources.Identifier;

/**
 * Drawing shared by the minimap and the world map: the explored regions (full textures up close, thumbnails when
 * zoomed out, the live cave view on top), marker icons and the player arrow.
 */
final class MapRenderer {
    static final Identifier ARROW = Wayfarers.id("map/arrow");
    /** Below this scale (GUI pixels per block) the thumbnails are drawn instead of the full regions. */
    static final float THUMBNAIL_SCALE = 0.5F;

    private static final java.util.Map<DynamicTexture, Identifier> IDS = new java.util.IdentityHashMap<>();
    private static int nextId;

    private MapRenderer() {}

    /** The id {@code tex} is registered under with the texture manager (registered on first use). */
    private static Identifier textureId(DynamicTexture tex) {
        return IDS.computeIfAbsent(tex, t -> {
            Identifier id = Wayfarers.id("map_region/" + nextId++);
            Minecraft.getInstance().getTextureManager().register(id, t);
            return id;
        });
    }

    /** Closes a region texture, through the texture manager when it was registered there. */
    static void close(DynamicTexture tex) {
        Identifier id = IDS.remove(tex);
        if (id != null) {
            Minecraft.getInstance().getTextureManager().release(id);
        } else {
            tex.close();
        }
    }

    static Identifier markerSprite(ClientMap.Marker m) {
        if (m.kind() == ClientMap.Kind.WAYPOINT && m.ref() instanceof MapProtocol.Waypoint w) {
            return Wayfarers.id("map/wp/" + MapProtocol.ICONS[Math.floorMod(w.icon(), MapProtocol.ICONS.length)]);
        }
        return Wayfarers.id("map/marker/" + m.kind().name().toLowerCase(java.util.Locale.ROOT));
    }

    /**
     * Draws the map centred on block (cx, cz) at {@code scale} GUI pixels per block, turned by {@code angle} radians
     * around the screen point (sx, sy). {@code radius}: half the diagonal of the visible area in GUI pixels. The
     * caller sets the scissor.
     */
    static void tiles(GuiGraphicsExtractor g, double cx, double cz, float scale, float sx, float sy, float angle, float radius) {
        tiles(g, cx, cz, scale, sx, sy, angle, radius, -1);
    }

    /** As above, tinted by {@code color} (ARGB: its alpha fades the terrain, for the minimap's opacity setting). */
    static void tiles(GuiGraphicsExtractor g, double cx, double cz, float scale, float sx, float sy, float angle, float radius,
                      int color) {
        MapLayer base = ClientMap.layer();
        if (base == null) {
            return;
        }
        boolean full = scale >= THUMBNAIL_SCALE;
        double reach = radius / scale;
        int rx0 = (int) Math.floor((cx - reach) / MapTile.SIZE);
        int rx1 = (int) Math.floor((cx + reach) / MapTile.SIZE);
        int rz0 = (int) Math.floor((cz - reach) / MapTile.SIZE);
        int rz1 = (int) Math.floor((cz + reach) / MapTile.SIZE);
        g.pose().pushMatrix();
        g.pose().translate(sx, sy);
        if (angle != 0) {
            g.pose().rotate(angle);
        }
        for (int rz = rz0; rz <= rz1; rz++) {
            for (int rx = rx0; rx <= rx1; rx++) {
                ClientMap.want(rx, rz, full);
                MapTile t = base.peek(rx, rz);
                if (t == null) {
                    continue;
                }
                DynamicTexture tex = full ? base.texture(t) : null;
                int size = MapTile.SIZE;
                if (tex == null) {
                    tex = base.miniTexture(t);
                    size = MapTile.MINI;
                }
                if (tex != null) {
                    blitRegion(g, tex, size, rx, rz, cx, cz, scale, color);
                }
            }
        }
        MapLayer cave = ClientMap.cave();
        if (cave != null && full) {
            for (MapTile t : cave.all()) {
                if (t.rx >= rx0 && t.rx <= rx1 && t.rz >= rz0 && t.rz <= rz1) {
                    DynamicTexture tex = cave.texture(t);
                    if (tex != null) {
                        blitRegion(g, tex, MapTile.SIZE, t.rx, t.rz, cx, cz, scale, color);
                    }
                }
            }
        }
        g.pose().popMatrix();
    }

    private static void blitRegion(GuiGraphicsExtractor g, DynamicTexture tex, int size, int rx, int rz, double cx, double cz, float scale,
                                   int color) {
        g.pose().pushMatrix();
        g.pose().translate((float) (((double) rx * MapTile.SIZE - cx) * scale), (float) (((double) rz * MapTile.SIZE - cz) * scale));
        float s = scale * MapTile.SIZE / size;
        g.pose().scale(s, s);
        if (color == -1) {
            GpuSampler sampler = RenderSystem.getSamplerCache().getClampToEdge(FilterMode.NEAREST);
            g.blit(tex.getTextureView(), sampler, 0, 0, size, size, 0, 1, 0, 1);
        } else {
            // only the Identifier blit takes a colour: the region textures are registered under an id on first use
            g.blit(RenderPipelines.GUI_TEXTURED, textureId(tex), 0, 0, 0.0F, 0.0F, size, size, size, size, color);
        }
        g.pose().popMatrix();
    }

    /** A marker icon centred on (x, y); {@code small}: half-faded edge marker. */
    static void marker(GuiGraphicsExtractor g, ClientMap.Marker m, int x, int y, boolean faded) {
        int alpha = faded ? 0xB0 : 0xFF;
        if (m.kind() == ClientMap.Kind.PLAYER) {
            PlayerInfo info = Minecraft.getInstance().getConnection() == null ? null
                    : Minecraft.getInstance().getConnection().getPlayerInfo(m.label());
            g.fill(x - 5, y - 5, x + 5, y + 5, 0xFF0F0C0A);
            g.fill(x - 4, y - 4, x + 4, y + 4, 0xFFF3E3C0);
            if (info != null) {
                PlayerFaceExtractor.extractRenderState(g, info.getSkin(), x - 4, y - 4, 8);
            } else {
                spriteCentered(g, markerSprite(m), x, y, 9, alpha << 24 | 0xFFFFFF);
            }
            return;
        }
        int tint = m.kind() == ClientMap.Kind.WAYPOINT ? (alpha << 24) | (m.color() & 0xFFFFFF) : alpha << 24 | 0xFFFFFF;
        if (m.kind() == ClientMap.Kind.PING) {
            // a pulsing ring around the ping
            long t = System.currentTimeMillis() % 1200;
            int r = 4 + (int) (t / 150);
            int a = (int) (200 * (1 - t / 1200.0));
            ring(g, x, y, r, (a << 24) | 0xFF7A3C);
        }
        spriteCentered(g, markerSprite(m), x, y, 9, tint);
    }

    static void spriteCentered(GuiGraphicsExtractor g, Identifier sprite, int x, int y, int size, int color) {
        g.blitSprite(RenderPipelines.GUI_TEXTURED, sprite, x - size / 2, y - size / 2, size, size, color);
    }

    /** A thin square-ish ring (cheap circle) of radius r. */
    static void ring(GuiGraphicsExtractor g, int x, int y, int r, int color) {
        int d = Math.max(1, r * 7 / 10);
        g.fill(x - d, y - r, x + d, y - r + 1, color);
        g.fill(x - d, y + r - 1, x + d, y + r, color);
        g.fill(x - r, y - d, x - r + 1, y + d, color);
        g.fill(x + r - 1, y - d, x + r, y + d, color);
        g.fill(x - r + 1, y - r + 1, x - d + 1, y - d + 1, color);
        g.fill(x + d - 1, y - r + 1, x + r - 1, y - d + 1, color);
        g.fill(x - r + 1, y + d - 1, x - d + 1, y + r - 1, color);
        g.fill(x + d - 1, y + d - 1, x + r - 1, y + r - 1, color);
    }

    /** The player's arrow at (x, y), pointing {@code angle} radians clockwise from up. */
    static void arrow(GuiGraphicsExtractor g, float x, float y, float angle) {
        g.pose().pushMatrix();
        g.pose().translate(x, y);
        g.pose().rotate(angle);
        g.blitSprite(RenderPipelines.GUI_TEXTURED, ARROW, -6, -6, 13, 13);
        g.pose().popMatrix();
    }
}
