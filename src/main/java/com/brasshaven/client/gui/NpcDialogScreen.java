package com.brasshaven.client.gui;

import com.brasshaven.client.ClientContracts;
import com.brasshaven.config.BrasshavenClientConfig;
import com.brasshaven.generated.GeneratedNpcs;
import com.brasshaven.network.NpcActionMsg;
import com.brasshaven.network.NpcDialogMsg;
import com.brasshaven.network.BrasshavenNet;
import com.brasshaven.util.NpcQuests;
import net.minecraft.ChatFormatting;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.util.FormattedCharSequence;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.item.ItemStack;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

/**
 * A quest giver's screen: its greeting and its contracts on the left (new, in progress, ready, done, for later, and
 * the deliveries addressed to it), the selected contract on a parcel card on the right (what it says, the objective,
 * progress, rewards) with Accept / Turn in / Hand over, Track (the HUD tracker) and, for a delivery, a new parcel.
 * Every button asks the server ({@link NpcActionMsg}), which answers with a fresh {@link NpcDialogMsg}.
 */
public class NpcDialogScreen extends Screen {
    private static final int W = 372;
    private static final int MAX_H = 226;
    private static final int ROW = 22;
    private static final NpcQuests.State[] STATES = NpcQuests.State.values();

    private NpcDialogMsg msg;
    private int h = MAX_H;
    private int left;
    private int top;
    private String selected;
    private int scroll;
    private WfButton main;
    private WfButton track;
    private WfButton parcel;

    public NpcDialogScreen(NpcDialogMsg msg) {
        super(Component.translatable("entity.brasshaven.wayfarer_npc"));
        this.msg = msg;
        selectDefault();
    }

    public int entityId() {
        return msg.entityId();
    }

    /** The server answered a button: same NPC, fresh states (the selection is kept). */
    public void refresh(NpcDialogMsg fresh) {
        this.msg = fresh;
        if (selected == null || entry(selected) == null) {
            selectDefault();
        }
        updateButtons();
    }

    private void selectDefault() {
        // a delivery for this NPC, then something to turn in, then something new, then the rest
        selected = null;
        for (NpcQuests.State want : new NpcQuests.State[] {NpcQuests.State.DELIVERY, NpcQuests.State.READY,
                NpcQuests.State.AVAILABLE, NpcQuests.State.ACTIVE}) {
            for (NpcDialogMsg.Entry e : msg.entries()) {
                if (state(e) == want) {
                    selected = e.id();
                    return;
                }
            }
        }
        if (!msg.entries().isEmpty()) {
            selected = msg.entries().get(0).id();
        }
    }

    private NpcDialogMsg.Entry entry(String id) {
        for (NpcDialogMsg.Entry e : msg.entries()) {
            if (e.id().equals(id)) {
                return e;
            }
        }
        return null;
    }

    private static NpcQuests.State state(NpcDialogMsg.Entry e) {
        return STATES[Math.max(0, Math.min(STATES.length - 1, e.state()))];
    }

    private Optional<GeneratedNpcs.Quest> quest(String id) {
        return ClientContracts.quest(ClientContracts.PREFIX + id);
    }

    // ------------------------------------------------------------------ layout
    private int listX() { return left + 10; }
    private int greetY() { return top + 22; }
    private int greetH() { return 44; }
    private int listY() { return greetY() + greetH() + 4; }
    private int listW() { return 150; }
    private int listH() { return h - (listY() - top) - 34; }
    private int rows() { return Math.max(1, (listH() - 6) / ROW); }
    private int cardX() { return left + 166; }
    private int cardY() { return top + 18; }
    private int cardW() { return W - 176; }
    private int cardH() { return h - 28; }

    @Override
    protected void init() {
        h = Math.min(MAX_H, height - 20);
        left = (width - W) / 2;
        top = WfGui.windowTop(height, h, 0);
        int bw = (cardW() - 16) / 2;
        int by = cardY() + cardH() - 24;
        main = addRenderableWidget(new WfButton(cardX() + 6, by, bw, 20, Component.empty(), b -> act()));
        track = addRenderableWidget(new WfButton(cardX() + 10 + bw, by, bw, 20, Component.empty(), b -> toggleTrack()));
        parcel = addRenderableWidget(new WfButton(cardX() + 6, by - 22, cardW() - 12, 20,
                Component.translatable("gui.brasshaven.npc.parcel"), b -> send(NpcQuests.PARCEL_AGAIN)));
        addRenderableWidget(new WfButton(listX(), top + h - 28, listW(), 20,
                Component.translatable("gui.brasshaven.npc.close"), b -> onClose()));
        updateButtons();
    }

    private void updateButtons() {
        if (main == null) {
            return;
        }
        NpcDialogMsg.Entry e = selected == null ? null : entry(selected);
        NpcQuests.State s = e == null ? NpcQuests.State.LOCKED : state(e);
        Optional<GeneratedNpcs.Quest> q = e == null ? Optional.empty() : quest(e.id());
        boolean delivery = q.isPresent() && q.get().kind() == GeneratedNpcs.Kind.DELIVER;
        main.visible = e != null && s != NpcQuests.State.DONE && s != NpcQuests.State.LOCKED;
        if (s == NpcQuests.State.AVAILABLE) {
            main.setMessage(Component.translatable("gui.brasshaven.npc.accept"));
            main.active = true;
        } else if (e != null && e.receiver()) {
            main.setMessage(Component.translatable("gui.brasshaven.npc.deliver"));
            main.active = s == NpcQuests.State.DELIVERY;
        } else {
            main.setMessage(Component.translatable("gui.brasshaven.npc.turn_in"));
            main.active = s == NpcQuests.State.READY;
            main.visible &= !delivery;
        }
        String tracked = BrasshavenClientConfig.TRACKED_QUEST.get();
        boolean isTracked = selected != null && tracked.equals(ClientContracts.PREFIX + selected);
        track.setMessage(Component.translatable(isTracked ? "gui.brasshaven.npc.untrack" : "gui.brasshaven.npc.track"));
        track.visible = e != null && (s == NpcQuests.State.ACTIVE || s == NpcQuests.State.READY
                || s == NpcQuests.State.DELIVERY);
        parcel.visible = e != null && delivery && !e.receiver() && s == NpcQuests.State.ACTIVE && e.progress() == 0;
    }

    private void act() {
        NpcDialogMsg.Entry e = selected == null ? null : entry(selected);
        if (e == null) {
            return;
        }
        send(state(e) == NpcQuests.State.AVAILABLE ? NpcQuests.ACCEPT : NpcQuests.TURN_IN);
        if (state(e) == NpcQuests.State.AVAILABLE && BrasshavenClientConfig.TRACKED_QUEST.get().isEmpty()) {
            setTracked(ClientContracts.PREFIX + e.id()); // the first contract taken shows on the HUD at once
        }
    }

    private void send(int action) {
        if (selected != null) {
            BrasshavenNet.toServer(new NpcActionMsg(msg.entityId(), selected, action));
        }
    }

    private void toggleTrack() {
        if (selected == null) {
            return;
        }
        String id = ClientContracts.PREFIX + selected;
        setTracked(id.equals(BrasshavenClientConfig.TRACKED_QUEST.get()) ? "" : id);
        updateButtons();
    }

    private static void setTracked(String id) {
        BrasshavenClientConfig.TRACKED_QUEST.set(id);
        BrasshavenClientConfig.TRACKED_QUEST.save();
    }

    @Override
    public void tick() {
        super.tick();
        Minecraft mc = Minecraft.getInstance();
        Entity npc = mc.level == null ? null : mc.level.getEntity(msg.entityId());
        if (mc.player == null || npc == null || !npc.isAlive() || mc.player.distanceToSqr(npc) > 10 * 10) {
            onClose(); // walked away
        }
    }

    // ------------------------------------------------------------------ rendering
    private Component npcName() {
        Minecraft mc = Minecraft.getInstance();
        Entity npc = mc.level == null ? null : mc.level.getEntity(msg.entityId());
        return npc != null ? npc.getDisplayName() : Component.translatable("npc.brasshaven.role." + msg.role());
    }

    @Override
    public void extractRenderState(GuiGraphicsExtractor g, int mouseX, int mouseY, float a) {
        WfGui.window(g, font, npcName(), left, top, W, h);
        drawGreeting(g);
        drawList(g, mouseX, mouseY);
        drawCard(g);
        super.extractRenderState(g, mouseX, mouseY, a);
        hoverTips(g, mouseX, mouseY);
    }

    private boolean nothingLeft() {
        for (NpcDialogMsg.Entry e : msg.entries()) {
            NpcQuests.State s = state(e);
            if (s != NpcQuests.State.DONE) {
                return false;
            }
        }
        return true;
    }

    private void drawGreeting(GuiGraphicsExtractor g) {
        WfGui.sprite(g, WfGui.CARD, listX(), greetY(), listW(), greetH());
        String key = (nothingLeft() ? "npc.brasshaven.idle." : "npc.brasshaven.greet.") + msg.role();
        int ty = greetY() + 5;
        List<FormattedCharSequence> lines = font.split(Component.translatable(key).withStyle(ChatFormatting.ITALIC),
                listW() - 10);
        for (int i = 0; i < Math.min(4, lines.size()); i++) {
            g.text(font, lines.get(i), listX() + 5, ty, WfGui.INK, false);
            ty += 9;
        }
    }

    private void drawList(GuiGraphicsExtractor g, int mouseX, int mouseY) {
        WfGui.sprite(g, WfGui.INSET, listX(), listY(), listW(), listH());
        List<NpcDialogMsg.Entry> es = msg.entries();
        if (es.isEmpty()) {
            g.text(font, Component.translatable("gui.brasshaven.npc.none"), listX() + 6, listY() + 8, WfGui.CREAM_SOFT, true);
        }
        int rowW = listW() - 12;
        for (int i = 0; i < rows() && i + scroll < es.size(); i++) {
            NpcDialogMsg.Entry e = es.get(i + scroll);
            int rx = listX() + 3;
            int ry = listY() + 3 + i * ROW;
            boolean hover = mouseX >= rx && mouseX < rx + rowW && mouseY >= ry && mouseY < ry + ROW - 1;
            if (e.id().equals(selected)) {
                WfGui.sprite(g, WfGui.ROW_SELECTED, rx, ry, rowW, ROW - 1);
            } else if (hover) {
                WfGui.sprite(g, WfGui.ROW_HOVER, rx, ry, rowW, ROW - 1);
            }
            NpcQuests.State s = state(e);
            g.item(ClientContracts.icon(ClientContracts.PREFIX + e.id()), rx + 2, ry + 2);
            int color = switch (s) {
                case DONE -> 0xFFA6F07A;
                case LOCKED -> WfGui.MUTED;
                case READY, DELIVERY -> WfGui.GOLD;
                default -> WfGui.CREAM;
            };
            WfGui.textClipped(g, font, ClientContracts.title(ClientContracts.PREFIX + e.id()).getString(), rx + 21, ry + 7,
                    rowW - 40, color, true);
            String icon = switch (s) {
                case DONE -> "done";
                case LOCKED -> "lock";
                case ACTIVE -> "progress";
                default -> null;
            };
            if (icon != null) {
                WfGui.sprite(g, WfGui.icon(icon), rx + rowW - 18, ry + 2, 16, 16);
            } else {
                // "!" something new, "?" something to hand in
                g.text(font, s == NpcQuests.State.AVAILABLE ? "!" : "?", rx + rowW - 12, ry + 7, WfGui.GOLD, true);
            }
        }
        if (es.size() > rows()) {
            int tx = listX() + listW() - 9;
            int ty = listY() + 3;
            int th = listH() - 6;
            WfGui.sprite(g, WfGui.SCROLL_TRACK, tx, ty, 6, th);
            int thumb = Math.max(16, th * rows() / es.size());
            int pos = (th - thumb) * scroll / Math.max(1, es.size() - rows());
            WfGui.sprite(g, WfGui.SCROLL_THUMB, tx, ty + pos, 6, thumb);
        }
    }

    private void drawCard(GuiGraphicsExtractor g) {
        int x = cardX();
        int y = cardY();
        int w = cardW();
        WfGui.sprite(g, WfGui.CARD, x, y, w, cardH());
        NpcDialogMsg.Entry e = selected == null ? null : entry(selected);
        if (e == null) {
            return;
        }
        String qid = ClientContracts.PREFIX + e.id();
        Optional<GeneratedNpcs.Quest> q = quest(e.id());
        NpcQuests.State s = state(e);
        g.item(ClientContracts.icon(qid), x + 6, y + 6);
        int ty = y + 7;
        for (FormattedCharSequence line : font.split(WfGui.bold(ClientContracts.title(qid)), w - 30)) {
            g.text(font, line, x + 26, ty, WfGui.INK, false);
            ty += 10;
        }
        ty = Math.max(ty, y + 26) + 2;
        // what the giver says (the receiver of a delivery reads who sent it instead)
        List<FormattedCharSequence> story = font.split(
                (e.receiver() && q.isPresent()
                        ? Component.translatable("gui.brasshaven.npc.from", Component.translatable("npc.brasshaven.role." + q.get().giver()))
                        : ClientContracts.story(qid)).copy().withStyle(ChatFormatting.ITALIC), w - 10);
        for (int i = 0; i < Math.min(5, story.size()); i++) {
            g.text(font, story.get(i), x + 5, ty, WfGui.INK_SOFT, false);
            ty += 9;
        }
        ty += 4;
        for (FormattedCharSequence line : font.split(ClientContracts.description(qid), w - 10)) {
            g.text(font, line, x + 5, ty, WfGui.INK, false);
            ty += 9;
        }
        ty += 3;
        if (s == NpcQuests.State.DONE) {
            g.text(font, WfGui.bold(Component.translatable("gui.brasshaven.npc.state.done")), x + 5, ty, WfGui.INK_GREEN, false);
        } else if (s == NpcQuests.State.LOCKED && q.isPresent()) {
            for (FormattedCharSequence line : font.split(Component.translatable("gui.brasshaven.npc.after",
                    ClientContracts.title(ClientContracts.PREFIX + q.get().after())), w - 10)) {
                g.text(font, line, x + 5, ty, WfGui.INK_RED, false);
                ty += 9;
            }
        } else if (s != NpcQuests.State.AVAILABLE) {
            g.text(font, Component.translatable("gui.brasshaven.npc.progress", e.progress(), e.needed()), x + 5, ty,
                    WfGui.INK, false);
            ty += 10;
            int bw = w - 10;
            WfGui.sprite(g, WfGui.id("bar_back"), x + 5, ty, bw, 6);
            int fill = e.needed() == 0 ? 0 : (bw - 2) * Math.min(e.progress(), e.needed()) / e.needed();
            if (fill > 0) {
                WfGui.sprite(g, WfGui.id(e.progress() >= e.needed() ? "bar_done" : "bar_fill"), x + 6, ty + 1, fill, 4);
            }
        } else if (q.isPresent() && q.get().kind() == GeneratedNpcs.Kind.DELIVER) {
            g.text(font, Component.translatable("gui.brasshaven.npc.to", Component.translatable("npc.brasshaven.role." + q.get().to())),
                    x + 5, ty, WfGui.INK, false);
        }
        // rewards, above the buttons
        if (q.isPresent()) {
            int ry = cardY() + cardH() - 74;
            g.text(font, WfGui.bold(Component.translatable("gui.brasshaven.quests.rewards")), x + 5, ry, WfGui.INK, false);
            ry += 10;
            int ix = x + 5;
            if (q.get().xp() > 0) {
                WfGui.sprite(g, WfGui.icon("xp"), ix, ry, 16, 16);
                String xp = String.valueOf(q.get().xp());
                g.text(font, xp, ix + 16, ry + 5, WfGui.INK_GREEN, false);
                ix += 22 + font.width(xp);
            }
            for (GeneratedNpcs.Reward r : q.get().rewards()) {
                var item = BuiltInRegistries.ITEM.getOptional(Identifier.parse(r.item()));
                if (item.isEmpty() || ix + 16 > x + w - 4) {
                    continue;
                }
                ItemStack stack = new ItemStack(item.get(), r.count());
                g.item(stack, ix, ry);
                g.itemDecorations(font, stack, ix, ry);
                ix += 18;
            }
        }
    }

    private void hoverTips(GuiGraphicsExtractor g, int mouseX, int mouseY) {
        List<NpcDialogMsg.Entry> es = msg.entries();
        int rowW = listW() - 12;
        for (int i = 0; i < rows() && i + scroll < es.size(); i++) {
            int rx = listX() + 3;
            int ry = listY() + 3 + i * ROW;
            if (mouseX >= rx && mouseX < rx + rowW && mouseY >= ry && mouseY < ry + ROW - 1) {
                NpcDialogMsg.Entry e = es.get(i + scroll);
                List<Component> tip = new ArrayList<>();
                tip.add(ClientContracts.title(ClientContracts.PREFIX + e.id()));
                NpcQuests.State s = state(e);
                tip.add(Component.translatable("gui.brasshaven.npc.state." + (e.receiver() && s == NpcQuests.State.DELIVERY
                        ? "delivery" : s.name().toLowerCase(java.util.Locale.ROOT))).withStyle(ChatFormatting.GRAY));
                g.setComponentTooltipForNextFrame(font, tip, mouseX, mouseY);
            }
        }
    }

    // ------------------------------------------------------------------ input
    @Override
    public boolean mouseClicked(MouseButtonEvent event, boolean doubleClick) {
        double mx = event.x();
        double my = event.y();
        List<NpcDialogMsg.Entry> es = msg.entries();
        int rowW = listW() - 12;
        for (int i = 0; i < rows() && i + scroll < es.size(); i++) {
            int rx = listX() + 3;
            int ry = listY() + 3 + i * ROW;
            if (mx >= rx && mx < rx + rowW && my >= ry && my < ry + ROW - 1) {
                selected = es.get(i + scroll).id();
                updateButtons();
                return true;
            }
        }
        return super.mouseClicked(event, doubleClick);
    }

    @Override
    public boolean mouseScrolled(double x, double y, double scrollX, double scrollY) {
        int max = Math.max(0, msg.entries().size() - rows());
        scroll = (int) Math.max(0, Math.min(max, scroll - Math.signum(scrollY)));
        return true;
    }

    @Override
    public boolean isPauseScreen() {
        return false;
    }
}
