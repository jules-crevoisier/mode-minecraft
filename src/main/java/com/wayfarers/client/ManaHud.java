package com.wayfarers.client;

import com.wayfarers.Wayfarers;
import com.wayfarers.client.gui.WfGui;
import com.wayfarers.item.SpellItem;
import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraftforge.client.event.AddGuiOverlayLayersEvent;
import net.minecraftforge.client.gui.overlay.ForgeLayeredDraw;

/**
 * The mana bar: a slim blue bar just above the experience bar, shown while you hold a magic item or while
 * your mana refills. The active ability's cooldown shows as a small dial next to it.
 */
public final class ManaHud {
    private static long lastVisible;

    private ManaHud() {}

    public static void register(AddGuiOverlayLayersEvent event) {
        event.getLayeredDraw().addAbove(ForgeLayeredDraw.PRE_SLEEP_STACK, Wayfarers.id("mana"),
                ForgeLayeredDraw.BOSS_OVERLAY, ManaHud::extract);
    }

    private static boolean holdingMagic(Minecraft mc) {
        return mc.player.getMainHandItem().getItem() instanceof SpellItem || mc.player.getOffhandItem().getItem() instanceof SpellItem;
    }

    private static void extract(GuiGraphicsExtractor g, DeltaTracker dt) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null || mc.player.isSpectator()) {
            return;
        }
        long now = System.currentTimeMillis();
        boolean refilling = ClientSkills.mana < ClientSkills.maxMana - 0.5F;
        if (holdingMagic(mc) || refilling) {
            lastVisible = now;
        }
        if (now - lastVisible > 2000) {
            return;
        }
        int w = 182;
        int x = g.guiWidth() / 2 - w / 2;
        int y = g.guiHeight() - 32 - 6;
        float frac = ClientSkills.maxMana <= 0 ? 0 : Math.min(1F, ClientSkills.mana / ClientSkills.maxMana);
        g.fill(x - 1, y - 1, x + w + 1, y + 4, 0xFF0F0C0A);
        g.fill(x, y, x + w, y + 3, 0xFF14243A);
        int fill = (int) (w * frac);
        if (fill > 0) {
            g.fillGradient(x, y, x + fill, y + 3, 0xFF6FD8FF, 0xFF2F6FD8);
        }
        String label = (int) ClientSkills.mana + " / " + (int) ClientSkills.maxMana;
        g.text(mc.font, label, g.guiWidth() / 2 - mc.font.width(label) / 2, y - 9, 0xFF9FE6FF, true);
        if (!ClientSkills.active.isEmpty()) {
            long remaining = ClientSkills.cooldownTicks - (now - ClientSkills.syncedAt) / 50;
            String v = remaining > 0 ? (remaining / 20 + 1) + "s" : "V";
            WfGui.sprite(g, WfGui.id("button_small"), x + w + 4, y - 6, 12, 12);
            g.centeredText(mc.font, v, x + w + 10, y - 4, remaining > 0 ? 0xFF6E5A40 : 0xFF2B1B0C);
        }
    }
}
