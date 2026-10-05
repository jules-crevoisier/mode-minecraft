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
    /** Below this scale (GUI pixels per block) the thumbnails are drawn instead of the full regions. */
    static final float THUMBNAIL_SCALE = 0.5F;

    private static final java.util.Map<DynamicTexture, Identifier> IDS = new java.util.IdentityHashMap<>();
    private static int nextId;

    private MapRenderer() {}

    /** The id {@code tex} is registered under with the texture manager (registered on first use). */
    static Identifier textureId(DynamicTexture tex) {
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
        if (MapShade.refresh()) {
            ClientMap.restyle();
        }
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

    // ------------------------------------------------------------------ markers and the arrow, sized to the map
    /** Marker size (GUI px) on a minimap of {@code outer} px: 6 on the smallest, 9 at 68 px, 11 at most. */
    static float minimapMarker(int outer) {
        return Math.max(6.0F, Math.min(11.0F, outer / 8.5F));
    }

    /** Player arrow length (GUI px) on a minimap of {@code outer} px: 7 at 56 px, 8 at 68, 13 at 128 and more. */
    static float minimapArrow(int outer) {
        return Math.max(7.0F, Math.min(13.0F, 7.0F + (outer - 56) * 0.085F));
    }

    /** Marker size on the world map at a zoom level (-6 .. 6): 7 zoomed out, 9 at 1 block per pixel, 13 close up. */
    static float worldMarker(int zoom) {
        return Math.max(7.0F, Math.min(13.0F, 9.0F + zoom * 0.7F));
    }

    static float worldArrow(int zoom) {
        return Math.max(8.0F, Math.min(16.0F, 11.0F + zoom * 0.9F));
    }

    static int guiScale() {
        return Math.max(1, Minecraft.getInstance().getWindow().getGuiScale());
    }

    /**
     * A marker icon centred on (x, y), about {@code size} GUI px wide, with a soft drop shadow; {@code faded}: an
     * edge marker for something off the minimap.
     */
    static void marker(GuiGraphicsExtractor g, ClientMap.Marker m, int x, int y, boolean faded, float size) {
        int alpha = faded ? 0xB0 : 0xFF;
        if (m.kind() == ClientMap.Kind.PLAYER) {
            PlayerInfo info = Minecraft.getInstance().getConnection() == null ? null
                    : Minecraft.getInstance().getConnection().getPlayerInfo(m.label());
            int h = Math.max(3, Math.round(size - 1) / 2);
            g.fill(x - h, y - h, x + h + 2, y + h + 2, 0x50000000);
            g.fill(x - h - 1, y - h - 1, x + h + 1, y + h + 1, 0xFF0F0C0A);
            g.fill(x - h, y - h, x + h, y + h, 0xFFF3E3C0);
            if (info != null) {
                PlayerFaceExtractor.extractRenderState(g, info.getSkin(), x - h, y - h, h * 2);
            } else {
                spriteCrisp(g, markerSprite(m), 9, x, y, size, alpha << 24 | 0xFFFFFF, false);
            }
            return;
        }
        int tint = m.kind() == ClientMap.Kind.WAYPOINT ? (alpha << 24) | (m.color() & 0xFFFFFF) : alpha << 24 | 0xFFFFFF;
        if (m.kind() == ClientMap.Kind.PING) {
            // a pulsing ring around the ping
            long t = System.currentTimeMillis() % 1200;
            int r = Math.round(size * 0.45F) + (int) (t / 150);
            int a = (int) (200 * (1 - t / 1200.0));
            ring(g, x, y, r, (a << 24) | 0xFF7A3C);
        }
        spriteCrisp(g, markerSprite(m), 9, x, y, size, tint, true);
    }

    /** As above at the classic 9 px (cards, legend). */
    static void marker(GuiGraphicsExtractor g, ClientMap.Marker m, int x, int y, boolean faded) {
        marker(g, m, x, y, faded, 9.0F);
    }

    static void spriteCentered(GuiGraphicsExtractor g, Identifier sprite, int x, int y, int size, int color) {
        g.blitSprite(RenderPipelines.GUI_TEXTURED, sprite, x - size / 2, y - size / 2, size, size, color);
    }

    /**
     * A pixel-art sprite of {@code texels} x {@code texels} centred on (x, y), about {@code size} GUI px wide, drawn
     * at a whole number of screen pixels per texel so it stays crisp at every size and GUI scale. {@code shadow}: a
     * translucent copy one texel down-right under it.
     */
    static void spriteCrisp(GuiGraphicsExtractor g, Identifier sprite, int texels, float x, float y, float size, int color,
                            boolean shadow) {
        int gs = guiScale();
        int k = Math.max(1, Math.round(size * gs / texels));
        int real = texels * k;
        int o = -real / 2;
        g.pose().pushMatrix();
        g.pose().translate(Math.round(x * gs) / (float) gs, Math.round(y * gs) / (float) gs);
        g.pose().scale(1.0F / gs, 1.0F / gs);
        if (shadow) {
            int a = ((color >>> 24) * 0x70 / 255) << 24;
            g.blitSprite(RenderPipelines.GUI_TEXTURED, sprite, o + k, o + k, real, real, a);
        }
        g.blitSprite(RenderPipelines.GUI_TEXTURED, sprite, o, o, real, real, color);
        g.pose().popMatrix();
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

    /** The arrow's outline, pointing up, in units of half its length: tip, right barb, notch, left barb. */
    private static final float[] ARROW = {0.0F, -1.0F, 0.76F, 0.92F, 0.0F, 0.44F, -0.76F, 0.92F};

    /**
     * The player's arrow at (x, y), {@code size} GUI px long, pointing {@code angle} radians clockwise from up. Drawn
     * as a polygon at the screen's own resolution (one fill per pixel row), so it is sharp at every size, angle and
     * GUI scale: a soot outline, a cream lit half and a red shaded half (a compass needle), and a soft drop shadow.
     */
    static void arrow(GuiGraphicsExtractor g, float x, float y, float angle, float size) {
        int gs = guiScale();
        float r = size * gs / 2.0F;
        float cos = (float) Math.cos(angle);
        float sin = (float) Math.sin(angle);
        float edge = Math.max(1.0F, gs * 0.6F);
        float[] in = new float[8];
        float[] out = new float[8];
        float grow = (r + edge * 1.8F) / r;
        for (int i = 0; i < 4; i++) {
            float px = ARROW[i * 2] * r;
            float py = ARROW[i * 2 + 1] * r;
            in[i * 2] = px * cos - py * sin;
            in[i * 2 + 1] = px * sin + py * cos;
            out[i * 2] = in[i * 2] * grow;
            out[i * 2 + 1] = in[i * 2 + 1] * grow;
        }
        g.pose().pushMatrix();
        g.pose().translate(Math.round(x * gs) / (float) gs, Math.round(y * gs) / (float) gs);
        g.pose().scale(1.0F / gs, 1.0F / gs);
        float sh = Math.max(1.0F, gs * 0.7F);
        polygon(g, out, sh, sh, 0x60000000);
        polygon(g, out, 0, 0, 0xFF0F0C0A);
        polygon(g, new float[] {in[0], in[1], in[4], in[5], in[6], in[7]}, 0, 0, 0xFFFFF8EC);
        polygon(g, new float[] {in[0], in[1], in[2], in[3], in[4], in[5]}, 0, 0, 0xFFE0483B);
        g.pose().popMatrix();
    }

    /** Fills a polygon (x, y pairs, offset by dx, dy) one pixel row at a time: the pixels whose centre is inside. */
    static void polygon(GuiGraphicsExtractor g, float[] p, float dx, float dy, int color) {
        int n = p.length / 2;
        float minY = Float.MAX_VALUE;
        float maxY = -Float.MAX_VALUE;
        for (int i = 0; i < n; i++) {
            minY = Math.min(minY, p[i * 2 + 1] + dy);
            maxY = Math.max(maxY, p[i * 2 + 1] + dy);
        }
        float[] xs = new float[n];
        for (int y = (int) Math.floor(minY); y <= (int) Math.ceil(maxY); y++) {
            float yc = y + 0.5F;
            int c = 0;
            for (int i = 0; i < n; i++) {
                int j = (i + 1) % n;
                float x0 = p[i * 2] + dx;
                float y0 = p[i * 2 + 1] + dy;
                float x1 = p[j * 2] + dx;
                float y1 = p[j * 2 + 1] + dy;
                if ((y0 <= yc) != (y1 <= yc)) {
                    xs[c++] = x0 + (yc - y0) * (x1 - x0) / (y1 - y0);
                }
            }
            java.util.Arrays.sort(xs, 0, c);
            for (int k = 0; k + 1 < c; k += 2) {
                int a = (int) Math.ceil(xs[k] - 0.5F);
                int b = (int) Math.ceil(xs[k + 1] - 0.5F);
                if (b > a) {
                    g.fill(a, y, b, y + 1, color);
                }
            }
        }
    }
}
