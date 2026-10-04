package com.wayfarers.client.gui;

import com.wayfarers.client.ClientSkills;
import com.wayfarers.generated.GeneratedSkills;
import com.wayfarers.network.SkillActionMsg;
import com.wayfarers.network.WayfarersNet;
import net.minecraft.ChatFormatting;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.util.FormattedCharSequence;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

import java.util.ArrayList;
import java.util.List;

/**
 * The talent tree (K): four branches side by side, each a small constellation of talents linked to their
 * prerequisites. Click an available talent to unlock it; click an unlocked active talent to equip it on V.
 */
public class SkillTreeScreen extends Screen {
    private static final int W = 420;
    private static final int H = 250;
    private static final int NODE = 22;
    private static final int COL_W = 30;
    private static final int ROW_H = 31;
    private static final int BRANCH_W = 102;

    private int left;
    private int top;

    public SkillTreeScreen() {
        super(Component.translatable("gui.wayfarers.skills.title"));
    }

    @Override
    protected void init() {
        left = (width - W) / 2;
        top = (height - H) / 2;
        WayfarersNet.toServer(new SkillActionMsg(SkillActionMsg.Action.REQUEST, ""));
    }

    private int branchIndex(String branch) {
        for (int i = 0; i < GeneratedSkills.BRANCHES.size(); i++) {
            if (GeneratedSkills.BRANCHES.get(i).id().equals(branch)) {
                return i;
            }
        }
        return 0;
    }

    private int nodeX(GeneratedSkills.Skill s) {
        return left + 14 + branchIndex(s.branch()) * BRANCH_W + 12 + s.col() * COL_W;
    }

    private int nodeY(GeneratedSkills.Skill s) {
        return top + 42 + s.row() * ROW_H;
    }

    private static GeneratedSkills.Skill skill(String id) {
        return GeneratedSkills.SKILLS.stream().filter(s -> s.id().equals(id)).findFirst().orElse(null);
    }

    private static ItemStack icon(String id) {
        return BuiltInRegistries.ITEM.getOptional(Identifier.parse(id)).map(ItemStack::new).orElse(new ItemStack(Items.BOOK));
    }

    @Override
    public void extractRenderState(GuiGraphicsExtractor g, int mouseX, int mouseY, float a) {
        WfGui.window(g, font, title, left, top, W, H);
        Component points = Component.translatable("gui.wayfarers.skills.points", ClientSkills.points, ClientSkills.earned);
        g.text(font, points, left + 16, top + 14, WfGui.INK, false);
        // the hint goes on the right of the points line, clipped to the window (it overflowed it in both languages)
        int hintX = left + 16 + font.width(points) + 12;
        int hintW = left + W - 16 - hintX;
        String hint = Component.translatable("gui.wayfarers.skills.hint").getString();
        WfGui.textClipped(g, font, hint, Math.max(hintX, left + W - 16 - font.width(hint)), top + 14, hintW, WfGui.INK_SOFT, false);
        boolean overPoints = mouseX >= left + 16 && mouseX < left + W - 16 && mouseY >= top + 12 && mouseY < top + 23;
        // branch panels
        for (int i = 0; i < GeneratedSkills.BRANCHES.size(); i++) {
            GeneratedSkills.Branch b = GeneratedSkills.BRANCHES.get(i);
            int bx = left + 14 + i * BRANCH_W;
            WfGui.sprite(g, WfGui.INSET, bx, top + 26, BRANCH_W - 6, H - 38);
            g.centeredText(font, Component.translatable("skill.wayfarers.branch." + b.id()), bx + (BRANCH_W - 6) / 2, top + 30, b.color());
        }
        // links first, then nodes on top
        for (GeneratedSkills.Skill s : GeneratedSkills.SKILLS) {
            for (String r : s.requires()) {
                GeneratedSkills.Skill p = skill(r);
                if (p == null) {
                    continue;
                }
                int color = ClientSkills.has(s.id()) ? 0xFFF6C343 : ClientSkills.has(p.id()) ? 0xFFB58A45 : 0xFF4A3F38;
                int x0 = nodeX(p) + NODE / 2;
                int y0 = nodeY(p) + NODE / 2;
                int x1 = nodeX(s) + NODE / 2;
                int y1 = nodeY(s) + NODE / 2;
                int ym = (y0 + y1) / 2;
                g.fill(x0 - 1, y0, x0 + 1, ym + 1, color);
                g.fill(Math.min(x0, x1) - 1, ym - 1, Math.max(x0, x1) + 1, ym + 1, color);
                g.fill(x1 - 1, ym, x1 + 1, y1, color);
            }
        }
        GeneratedSkills.Skill hovered = null;
        for (GeneratedSkills.Skill s : GeneratedSkills.SKILLS) {
            int x = nodeX(s);
            int y = nodeY(s);
            boolean has = ClientSkills.has(s.id());
            boolean can = ClientSkills.canUnlock(s.id(), s.cost(), s.requires());
            boolean isActive = s.kind().equals("active");
            boolean equipped = isActive && has && s.ability().equals(ClientSkills.active);
            int frame = equipped ? 0xFF9FE6FF : has ? 0xFFF6C343 : can ? 0xFFB58A45 : 0xFF2B2320;
            g.fill(x - 1, y - 1, x + NODE + 1, y + NODE + 1, 0xFF0F0C0A);
            g.fill(x, y, x + NODE, y + NODE, frame);
            g.fill(x + 2, y + 2, x + NODE - 2, y + NODE - 2, has ? 0xFF3E3430 : 0xFF1F1B17);
            if (isActive) {
                g.outline(x - 3, y - 3, NODE + 6, NODE + 6, has ? 0xFFF6C343 : 0xFF4A3F38);
            }
            g.item(icon(s.icon()), x + 3, y + 3);
            if (!has && !can) {
                g.fill(x + 2, y + 2, x + NODE - 2, y + NODE - 2, 0x99000000);
            }
            if (mouseX >= x && mouseX < x + NODE && mouseY >= y && mouseY < y + NODE) {
                hovered = s;
                g.fill(x + 2, y + 2, x + NODE - 2, y + NODE - 2, 0x40FFFFFF);
            }
        }
        // mana / active summary
        g.text(font, Component.translatable("gui.wayfarers.skills.mana", (int) ClientSkills.maxMana), left + 16, top + H - 11, WfGui.INK_SOFT, false);
        if (!ClientSkills.active.isEmpty()) {
            WfGui.textClipped(g, font, Component.translatable("gui.wayfarers.skills.active", abilityKey(),
                    Component.translatable("skill.wayfarers.ability." + ClientSkills.active)).getString(), left + 150, top + H - 11,
                    W - 150 - 16, WfGui.INK_SOFT, false);
        }
        super.extractRenderState(g, mouseX, mouseY, a);
        if (hovered == null && overPoints) {
            g.setComponentTooltipForNextFrame(font, List.of(Component.translatable("gui.wayfarers.skills.hint"),
                    Component.translatable("gui.wayfarers.skills.points.tip").withStyle(ChatFormatting.GRAY)), mouseX, mouseY);
        }
        if (hovered != null) {
            List<FormattedCharSequence> lines = new ArrayList<>();
            lines.add(Component.translatable("skill.wayfarers." + hovered.id()).withStyle(ChatFormatting.GOLD).getVisualOrderText());
            lines.addAll(font.split(Component.translatable("skill.wayfarers." + hovered.id() + ".desc"), 200));
            boolean has = ClientSkills.has(hovered.id());
            Component state = has
                    ? Component.translatable(hovered.kind().equals("active") ? "gui.wayfarers.skills.click_equip" : "gui.wayfarers.skills.owned",
                    abilityKey())
                    .withStyle(ChatFormatting.GREEN)
                    : Component.translatable("gui.wayfarers.skills.cost", hovered.cost())
                    .withStyle(ClientSkills.canUnlock(hovered.id(), hovered.cost(), hovered.requires()) ? ChatFormatting.YELLOW : ChatFormatting.RED);
            lines.add(state.getVisualOrderText());
            g.setTooltipForNextFrame(font, lines, mouseX, mouseY);
        }
    }

    @Override
    public boolean mouseClicked(MouseButtonEvent event, boolean doubleClick) {
        for (GeneratedSkills.Skill s : GeneratedSkills.SKILLS) {
            int x = nodeX(s);
            int y = nodeY(s);
            if (event.x() >= x && event.x() < x + NODE && event.y() >= y && event.y() < y + NODE) {
                if (ClientSkills.has(s.id())) {
                    if (s.kind().equals("active")) {
                        WayfarersNet.toServer(new SkillActionMsg(SkillActionMsg.Action.SET_ACTIVE, s.id()));
                    }
                } else if (ClientSkills.canUnlock(s.id(), s.cost(), s.requires())) {
                    WayfarersNet.toServer(new SkillActionMsg(SkillActionMsg.Action.UNLOCK, s.id()));
                }
                return true;
            }
        }
        return super.mouseClicked(event, doubleClick);
    }

    /** The key bound to "use active talent" (V unless rebound). */
    private static Component abilityKey() {
        return com.wayfarers.client.WayfarersClient.ABILITY_KEY.getTranslatedKeyMessage();
    }

    @Override
    public boolean keyPressed(net.minecraft.client.input.KeyEvent event) {
        // the key that opens the talent tree closes it too
        if (com.wayfarers.client.WayfarersClient.SKILLS_KEY.matches(event)) {
            onClose();
            return true;
        }
        return super.keyPressed(event);
    }

    @Override
    public boolean isPauseScreen() {
        return false;
    }
}
