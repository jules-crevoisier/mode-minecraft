package com.brasshaven.item;

import com.brasshaven.accessory.AccessorySlotType;
import net.minecraft.core.component.DataComponents;
import net.minecraft.locale.Language;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.equipment.Equippable;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.function.BooleanSupplier;
import java.util.function.Consumer;

/**
 * The one tooltip layout of every Brasshaven item (tools/wf/tooltips.py documents the conventions):
 *
 * <pre>
 *   Name
 *   A one-line flavour, in italics                 item.brasshaven.&lt;id&gt;.flavor
 *   What it does, in plain words                   .desc (first paragraph)
 *   Key facts: accessory slot, ability, cooldown   computed by the item ({@link Facts})
 *   More rules and numbers                         .desc2, .desc3 and details, shown with Shift when long
 *   Hold Shift for details
 * </pre>
 *
 * Long sentences are wrapped so a tooltip never runs across the whole screen.
 */
public final class BrassTooltip {
    /** Set by the client: is Shift held? (tooltips are only built on the client, false elsewhere) */
    public static volatile BooleanSupplier shiftDown = () -> false;

    /** Colours (tools/STYLE_STEAMPUNK.md): warm grey italics, cream rules, brass headings, muted hint. */
    public static final int FLAVOR = 0xA89C8A;
    public static final int RULES = 0xDCCDB0;
    public static final int HEADING = 0xF6C343;
    public static final int DETAIL = 0xC2B49A;
    public static final int HINT = 0x8C8070;
    /** Characters per tooltip line before wrapping (about 200 px of the default font). */
    private static final int WRAP = 40;
    /** Extra lines beyond this many go behind "Hold Shift for details". */
    private static final int LOOSE = 1;

    private BrassTooltip() {}

    /** Items that add facts (always shown) and details (shown with Shift) of their own. */
    public interface Facts {
        void facts(ItemStack stack, List<Component> facts, List<Component> details);
    }

    /** Items whose class already calls {@link #append}: the client tooltip event leaves them alone. */
    public interface Styled {}

    public static String descId(Item item) {
        return item instanceof BlockItem block ? block.getBlock().getDescriptionId() : item.getDescriptionId();
    }

    /** Appends the Brasshaven lines of this stack (everything below the name). */
    public static void append(ItemStack stack, Consumer<Component> out) {
        for (Component line : lines(stack)) {
            out.accept(line);
        }
    }

    public static List<Component> lines(ItemStack stack) {
        Item item = stack.getItem();
        String key = descId(item);
        Language lang = Language.getInstance();
        List<Component> out = new ArrayList<>();
        if (lang.has(key + ".flavor")) {
            for (String line : wrap(lang.getOrDefault(key + ".flavor"))) {
                out.add(Component.literal(line).withStyle(s -> s.withColor(FLAVOR).withItalic(true)));
            }
        }
        List<List<String>> paragraphs = new ArrayList<>();
        for (int i = 1; i <= 9; i++) {
            String k = i == 1 ? key + ".desc" : key + ".desc" + i;
            if (!lang.has(k)) {
                if (i > 1) {
                    break;
                }
                continue;
            }
            paragraphs.add(wrap(lang.getOrDefault(k)));
        }
        List<Component> facts = new ArrayList<>();
        List<Component> details = new ArrayList<>();
        // a full armour set: its bonus is a heading, not a rule of the piece ("Set: ..." / "Ensemble : ...")
        if (isArmor(stack) && !paragraphs.isEmpty()) {
            String first = String.join(" ", paragraphs.getFirst());
            String bonus = first.replaceFirst("^(?i)(set|ensemble)\\s*:\\s*", "");
            if (!bonus.equals(first)) {
                paragraphs.removeFirst();
                facts.add(Component.translatable("tooltip.brasshaven.set_bonus").withStyle(s -> s.withColor(HEADING)));
                for (String line : wrap(capitalize(bonus))) {
                    facts.add(rule(line));
                }
            }
        }
        AccessorySlotType slot = AccessorySlotType.of(stack);
        if (slot != null) {
            facts.add(Component.translatable("tooltip.brasshaven.accessory", slot.label()).withStyle(s -> s.withColor(HEADING)));
            details.add(detail(Component.translatable("tooltip.brasshaven.accessory.worn")));
            if (slot == AccessorySlotType.RING) {
                details.add(detail(Component.translatable("tooltip.brasshaven.accessory.no_stack")));
            }
        }
        if (item instanceof Facts f) {
            f.facts(stack, facts, details);
        }
        // first paragraph always (up to three lines), then the facts, then the rest
        List<Component> rest = new ArrayList<>();
        if (!paragraphs.isEmpty()) {
            List<String> first = paragraphs.removeFirst();
            for (int i = 0; i < first.size(); i++) {
                (i < 3 ? out : rest).add(rule(first.get(i)));
            }
        }
        out.addAll(facts);
        for (List<String> p : paragraphs) {
            for (String line : p) {
                rest.add(rule(line));
            }
        }
        rest.addAll(details);
        if (rest.size() <= LOOSE || shiftDown.getAsBoolean()) {
            out.addAll(rest);
        } else {
            out.add(Component.translatable("tooltip.brasshaven.shift").withStyle(s -> s.withColor(HINT).withItalic(true)));
        }
        return out;
    }

    private static boolean isArmor(ItemStack stack) {
        Equippable eq = stack.get(DataComponents.EQUIPPABLE);
        return eq != null && eq.slot().getType() == EquipmentSlot.Type.HUMANOID_ARMOR;
    }

    public static MutableComponent rule(String text) {
        return Component.literal(text).withStyle(s -> s.withColor(RULES));
    }

    public static MutableComponent rule(Component text) {
        return text.copy().withStyle(s -> s.withColor(RULES));
    }

    public static MutableComponent heading(Component text) {
        return text.copy().withStyle(s -> s.withColor(HEADING));
    }

    public static MutableComponent detail(Component text) {
        return text.copy().withStyle(s -> s.withColor(DETAIL));
    }

    /** Seconds for a tick count: "4", "0.5". */
    public static String seconds(int ticks) {
        float s = ticks / 20F;
        return s == Math.round(s) ? Integer.toString(Math.round(s)) : String.format(Locale.ROOT, "%.1f", s);
    }

    public static String number(float v) {
        return v == Math.round(v) ? Integer.toString(Math.round(v)) : String.format(Locale.ROOT, "%.1f", v);
    }

    private static String capitalize(String s) {
        return s.isEmpty() ? s : Character.toUpperCase(s.charAt(0)) + s.substring(1);
    }

    /** Greedy word wrap at {@link #WRAP} characters. */
    public static List<String> wrap(String text) {
        List<String> lines = new ArrayList<>();
        StringBuilder line = new StringBuilder();
        for (String word : text.trim().split("\\s+")) {
            if (line.length() > 0 && line.length() + 1 + word.length() > WRAP) {
                lines.add(line.toString());
                line.setLength(0);
            }
            if (line.length() > 0) {
                line.append(' ');
            }
            line.append(word);
        }
        if (line.length() > 0) {
            lines.add(line.toString());
        }
        return lines;
    }
}
