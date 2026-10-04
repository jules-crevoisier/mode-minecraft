package com.wayfarers.client;

import com.wayfarers.Wayfarers;
import com.wayfarers.client.gui.WfGui;
import com.wayfarers.item.SpellItem;
import net.minecraft.client.AttackIndicatorStatus;
import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraftforge.client.event.AddGuiOverlayLayersEvent;
import net.minecraftforge.client.gui.overlay.ForgeLayeredDraw;

/**
 * The mana gauge: a slim blue vial standing right of the hotbar (past the off-hand slot or the attack indicator
 * when they are on that side), with the mana as "37/50" beside it, shown while you hold a magic item or while your
 * mana refills. Under the number, a small brass key cap shows the active ability: its key when ready, the seconds
 * left while it recharges.
 *
 * <p>(It used to lie across the screen just above the experience bar, which is where the hearts and the food bar
 * are drawn in survival: it covered them.)
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

    /** Left edge of the free space right of the hotbar, like vanilla's own placement of the off-hand slot. */
    private static int rightOfHotbar(Minecraft mc, int screenCenter) {
        int x = screenCenter + 91 + 4;
        HumanoidArm offhandSide = mc.player.getMainArm().getOpposite();
        if (offhandSide == HumanoidArm.RIGHT && !mc.player.getOffhandItem().isEmpty()) {
            x += 29;
        } else if (offhandSide == HumanoidArm.LEFT && mc.options.attackIndicator().get() == AttackIndicatorStatus.HOTBAR) {
            x += 22;
        }
        return x;
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
        Font font = mc.font;
        int x = rightOfHotbar(mc, g.guiWidth() / 2);
        int bottom = g.guiHeight() - 1;
        int h = 21;
        int top = bottom - h;
        float frac = ClientSkills.maxMana <= 0 ? 0 : Math.min(1F, ClientSkills.mana / ClientSkills.maxMana);
        // vial: soot rim, dark glass, blue mana rising from the bottom, a glint on the glass
        g.fill(x - 1, top - 1, x + 7, bottom + 1, 0xFF0F0C0A);
        g.fill(x, top, x + 6, bottom, 0xFF14243A);
        int fill = Math.round(h * frac);
        if (fill > 0) {
            g.fillGradient(x, bottom - fill, x + 6, bottom, 0xFF6FD8FF, 0xFF2F6FD8);
        }
        g.fill(x + 1, top + 1, x + 2, bottom - 1, 0x40FFFFFF);
        g.fill(x - 1, top - 2, x + 7, top - 1, 0xFFB58A45);
        String label = (int) ClientSkills.mana + "/" + (int) ClientSkills.maxMana;
        g.text(font, label, x + 10, top, 0xFF9FE6FF, true);
        if (!ClientSkills.active.isEmpty()) {
            long remaining = ClientSkills.cooldownTicks - (now - ClientSkills.syncedAt) / 50;
            String v = remaining > 0 ? (remaining / 20 + 1) + "s" : WayfarersClient.ABILITY_KEY.getTranslatedKeyMessage().getString();
            int w = Math.max(12, font.width(v) + 5);
            // ready: a brass key cap engraved with the key; recharging: a dark cap with the seconds in cream
            // (brown on brass was hard to read)
            if (remaining > 0) {
                g.fill(x + 10, bottom - 11, x + 10 + w, bottom + 1, 0xFF0F0C0A);
                g.fill(x + 11, bottom - 10, x + 9 + w, bottom, 0xFF3E3430);
                g.text(font, v, x + 10 + (w - font.width(v) + 1) / 2, bottom - 9, WfGui.CREAM, false);
            } else {
                WfGui.sprite(g, WfGui.id("button_small"), x + 10, bottom - 11, w, 12);
                g.text(font, v, x + 10 + (w - font.width(v) + 1) / 2, bottom - 9, WfGui.PLATE_INK, false);
            }
        }
    }
}
