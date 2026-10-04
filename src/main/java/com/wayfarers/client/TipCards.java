package com.wayfarers.client;

import com.mojang.blaze3d.platform.InputConstants;
import com.wayfarers.Wayfarers;
import com.wayfarers.client.gui.GuideScreen;
import com.wayfarers.client.gui.WfGui;
import com.wayfarers.config.WayfarersClientConfig;
import com.wayfarers.generated.GeneratedGuide;
import net.minecraft.ChatFormatting;
import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.util.FormattedCharSequence;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraftforge.client.event.AddGuiOverlayLayersEvent;
import net.minecraftforge.client.gui.overlay.ForgeLayeredDraw;
import net.minecraftforge.event.entity.player.ItemTooltipEvent;
import org.lwjgl.glfw.GLFW;

import java.util.ArrayDeque;
import java.util.Deque;
import java.util.List;

/**
 * One-time tip cards (sent by the server the first time a player meets a system) shown under the quest
 * tracker, plus the manual shortcut: items with a manual page get "Hold W: manual page" in their tooltip,
 * and holding W over them in an inventory opens that page.
 */
public final class TipCards {
    private static final int W = 170;
    private static final int SHOW_TICKS = 200;
    private static final Deque<String> QUEUE = new ArrayDeque<>();
    private static String current;
    private static int age;
    private static int holdW;
    private static String shownId;
    private static List<FormattedCharSequence> shownLines = List.of();
    private static ItemStack shownIcon = ItemStack.EMPTY;

    private TipCards() {}

    public static void register(AddGuiOverlayLayersEvent event) {
        event.getLayeredDraw().addAbove(ForgeLayeredDraw.PRE_SLEEP_STACK, Wayfarers.id("tips"),
                ForgeLayeredDraw.BOSS_OVERLAY, TipCards::extract);
    }

    public static void show(String tip) {
        if (WayfarersClientConfig.TIPS.get() && !tip.equals(current) && !QUEUE.contains(tip)) {
            QUEUE.add(tip);
        }
    }

    private static GeneratedGuide.Tip tip(String id) {
        return GeneratedGuide.TIPS.stream().filter(t -> t.id().equals(id)).findFirst().orElse(null);
    }

    public static void tick() {
        if (current != null && ++age > SHOW_TICKS) {
            current = null;
        }
        if (current == null && !QUEUE.isEmpty()) {
            current = QUEUE.poll();
            age = 0;
            shownId = null;
        }
        // hold W over an item with a manual page (in any inventory screen) to open it
        Minecraft mc = Minecraft.getInstance();
        if (mc.gui.screen() instanceof AbstractContainerScreen<?> screen) {
            Slot slot = screen.getSlotUnderMouse();
            String page = slot != null && slot.hasItem() ? GuideScreen.pageFor(slot.getItem()) : null;
            if (page != null && InputConstants.isKeyDown(mc.getWindow(), GLFW.GLFW_KEY_W)) {
                if (++holdW == 8) {
                    mc.gui.setScreen(new GuideScreen(page));
                }
            } else {
                holdW = 0;
            }
        } else {
            holdW = 0;
        }
    }

    public static void onTooltip(ItemTooltipEvent event) {
        if (GuideScreen.pageFor(event.getItemStack()) != null) {
            event.getToolTip().add(Component.translatable("gui.wayfarers.manual.hold").withStyle(ChatFormatting.DARK_AQUA));
        }
    }

    private static void extract(GuiGraphicsExtractor g, DeltaTracker dt) {
        Minecraft mc = Minecraft.getInstance();
        if (current == null || mc.player == null) {
            return;
        }
        GeneratedGuide.Tip t = tip(current);
        if (t == null) {
            current = null;
            return;
        }
        Font font = mc.font;
        if (!t.id().equals(shownId)) { // drawn every frame for ten seconds: wrap the text and build the icon once
            shownId = t.id();
            shownLines = font.split(Component.translatable("tip.wayfarers." + t.id()), W - 30);
            shownIcon = BuiltInRegistries.ITEM.getOptional(Identifier.parse(t.icon())).map(ItemStack::new)
                    .orElse(new ItemStack(Items.BOOK));
        }
        List<FormattedCharSequence> lines = shownLines;
        int h = 20 + lines.size() * 9;
        // slide in from the right during the first 8 ticks, out during the last 8
        float slide = Math.min(1F, Math.min(age, SHOW_TICKS - age) / 8F);
        int x = g.guiWidth() - (int) ((W + 6) * slide);
        int y = g.guiHeight() / 2 - h / 2 - 20;
        WfGui.sprite(g, WfGui.CARD, x, y, W, h);
        g.item(shownIcon, x + 5, y + 5);
        g.text(font, Component.translatable("gui.wayfarers.tip.title"), x + 25, y + 5, WfGui.INK_SOFT, false);
        for (int i = 0; i < lines.size(); i++) {
            g.text(font, lines.get(i), x + 25, y + 15 + i * 9, WfGui.INK, false);
        }
    }
}
