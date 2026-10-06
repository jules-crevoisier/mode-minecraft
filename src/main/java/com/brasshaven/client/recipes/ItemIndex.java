package com.brasshaven.client.recipes;

import com.brasshaven.Brasshaven;
import net.minecraft.client.Minecraft;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.tags.TagKey;
import net.minecraft.world.flag.FeatureFlagSet;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

import java.text.Normalizer;
import java.util.Iterator;
import java.util.LinkedHashSet;
import java.util.Locale;
import java.util.Set;
import java.util.regex.Pattern;

/**
 * The item list of the recipe viewer: every item of the game once, the mod's first (in its creative tab's order), then
 * the others in registry order. Built when first needed and again when the language changes, with a search key per
 * item (its name in the current language, lower case and without accents, so "epee" finds "Épée", and its id), so a
 * search only walks plain strings. Searches: words (all must match the name or the id), {@code @mod} (by mod id),
 * {@code #tag} (by item tag).
 */
public final class ItemIndex {
    private static final Pattern MARKS = Pattern.compile("\\p{M}+");

    private static ItemStack[] stacks = new ItemStack[0];
    private static String[] names = new String[0];
    private static String[] ids = new String[0];
    private static String[] namespaces = new String[0];
    private static int modCount;
    private static String builtLang;
    /** Bumped at every rebuild: the grids filter again. */
    private static int version;

    private ItemIndex() {}

    /** Builds the list if it is missing or was built for another language. */
    public static void ensure() {
        Minecraft mc = Minecraft.getInstance();
        String lang = mc.options.languageCode;
        if (builtLang == null || !builtLang.equals(lang) || stacks.length == 0) {
            build(mc);
            builtLang = lang;
        }
    }

    public static int version() {
        return version;
    }

    public static int size() {
        return stacks.length;
    }

    public static ItemStack get(int i) {
        return stacks[i];
    }

    /** Lower case, accents removed: the form both the names and the searches are compared in. */
    public static String fold(String s) {
        String lower = s.toLowerCase(Locale.ROOT);
        for (int i = 0; i < lower.length(); i++) {
            if (lower.charAt(i) > 127) {
                return MARKS.matcher(Normalizer.normalize(lower, Normalizer.Form.NFD)).replaceAll("");
            }
        }
        return lower;
    }

    private static void build(Minecraft mc) {
        long start = System.nanoTime();
        FeatureFlagSet features = mc.getConnection() != null ? mc.getConnection().enabledFeatures() : null;
        Set<Item> order = new LinkedHashSet<>();
        com.brasshaven.registry.ModItems.ALL.forEach(i -> order.add(i.get()));
        com.brasshaven.generated.ModDecor.ITEMS.forEach(i -> order.add(i.get()));
        com.brasshaven.generated.GeneratedWorldBlocks.ITEMS.forEach(i -> order.add(i.get()));
        for (Item item : BuiltInRegistries.ITEM) {
            if (BuiltInRegistries.ITEM.getKey(item).getNamespace().equals(Brasshaven.MODID)) {
                order.add(item);
            }
        }
        int mod = order.size();
        for (Item item : BuiltInRegistries.ITEM) {
            order.add(item);
        }
        order.remove(Items.AIR);
        if (features != null) {
            order.removeIf(item -> !item.isEnabled(features));
        }
        int n = order.size();
        stacks = new ItemStack[n];
        names = new String[n];
        ids = new String[n];
        namespaces = new String[n];
        Iterator<Item> it = order.iterator();
        for (int i = 0; i < n; i++) {
            Item item = it.next();
            ItemStack stack = new ItemStack(item);
            Identifier key = BuiltInRegistries.ITEM.getKey(item);
            stacks[i] = stack;
            String name;
            try {
                name = stack.getHoverName().getString();
            } catch (RuntimeException e) {
                name = key.getPath();
            }
            names[i] = fold(name);
            ids[i] = key.getPath().replace('_', ' ');
            namespaces[i] = key.getNamespace();
        }
        modCount = Math.min(mod, n);
        version++;
        Brasshaven.LOGGER.debug("Recipe viewer: {} items listed in {} ms", n, (System.nanoTime() - start) / 1_000_000);
    }

    /**
     * Fills {@code out} with the indices of the items matching {@code query} (in list order) and returns how many.
     * {@code out} must hold {@link #size()} ints.
     */
    public static int filter(String query, boolean modOnly, int[] out) {
        String[] terms = fold(query).trim().split("\\s+");
        int n = 0;
        int end = modOnly ? modCount : stacks.length;
        for (int i = 0; i < end; i++) {
            if (matches(i, terms)) {
                out[n++] = i;
            }
        }
        return n;
    }

    private static boolean matches(int i, String[] terms) {
        for (String t : terms) {
            if (t.isEmpty()) {
                continue;
            }
            if (t.charAt(0) == '@') {
                if (!namespaces[i].contains(t.substring(1))) {
                    return false;
                }
            } else if (t.charAt(0) == '#') {
                if (!hasTag(stacks[i].getItem(), t.substring(1))) {
                    return false;
                }
            } else if (!names[i].contains(t) && !ids[i].contains(t)) {
                return false;
            }
        }
        return true;
    }

    private static boolean hasTag(Item item, String part) {
        if (part.isEmpty()) {
            return true;
        }
        Iterator<TagKey<Item>> tags = item.builtInRegistryHolder().tags().iterator();
        while (tags.hasNext()) {
            if (tags.next().location().toString().contains(part)) {
                return true;
            }
        }
        return false;
    }
}
