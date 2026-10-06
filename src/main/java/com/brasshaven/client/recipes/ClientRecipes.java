package com.brasshaven.client.recipes;

import com.brasshaven.Brasshaven;
import com.brasshaven.chisel.ChiselFamilies;
import io.netty.buffer.Unpooled;
import net.minecraft.client.Minecraft;
import net.minecraft.core.RegistryAccess;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.resources.Identifier;
import net.minecraft.util.context.ContextMap;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.display.FurnaceRecipeDisplay;
import net.minecraft.world.item.crafting.display.RecipeDisplay;
import net.minecraft.world.item.crafting.display.ShapedCraftingRecipeDisplay;
import net.minecraft.world.item.crafting.display.ShapelessCraftingRecipeDisplay;
import net.minecraft.world.item.crafting.display.SlotDisplay;
import net.minecraft.world.item.crafting.display.SlotDisplayContext;
import net.minecraft.world.item.crafting.display.SmithingRecipeDisplay;
import net.minecraft.world.item.crafting.display.StonecutterRecipeDisplay;
import net.minecraft.world.level.block.Block;

import java.util.ArrayList;
import java.util.EnumMap;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;

/**
 * The recipes the server sent for the viewer (recipe/RecipeSync), on the client. The message parts are kept as bytes
 * and decoded the first time the viewer needs them (opening an inventory warms it up), against the client's registries
 * and tags; then every recipe is indexed by the items it makes and the items it uses. The Chisel Table's families
 * (chisel/ChiselFamilies, also synced by the server) are turned into recipes when asked for. Main thread only.
 */
public final class ClientRecipes {
    private static int generation = -1;
    private static byte[][] parts;
    private static int received;
    private static Index index;

    private ClientRecipes() {}

    private static final class Index {
        final Map<Item, List<ViewRecipe>> byOutput = new IdentityHashMap<>();
        final Map<Item, List<ViewRecipe>> byInput = new IdentityHashMap<>();
        final EnumMap<RecipeCategory, List<ViewRecipe>> byCategory = new EnumMap<>(RecipeCategory.class);
        int count;
    }

    /** One part of the server's data; a new generation (after a /reload) replaces the old one once it is complete. */
    public static void receive(int gen, int part, int count, byte[] data) {
        if (count <= 0 || part < 0 || part >= count) {
            return;
        }
        if (gen != generation || parts == null || parts.length != count) {
            generation = gen;
            parts = new byte[count][];
            received = 0;
        }
        if (parts[part] == null) {
            parts[part] = data;
            if (++received == count) {
                index = null; // decoded again on next use, with the tags the server sent just before
            }
        }
    }

    /** Forgets everything (leaving the world). */
    public static void clear() {
        generation = -1;
        parts = null;
        received = 0;
        index = null;
    }

    /** The server sent its recipes (all parts of them). */
    public static boolean ready() {
        return parts != null && received == parts.length;
    }

    /** Decodes and indexes the recipes now if that is still to do (opening an inventory calls it). */
    public static void warmUp() {
        index();
    }

    /** How many recipes the viewer knows (0: none received yet). */
    public static int count() {
        Index i = index();
        return i == null ? 0 : i.count;
    }

    private static Index index() {
        Minecraft mc = Minecraft.getInstance();
        if (index == null && ready() && mc.level != null && mc.getConnection() != null) {
            long start = System.nanoTime();
            index = build(mc.getConnection().registryAccess(), SlotDisplayContext.fromLevel(mc.level));
            Brasshaven.LOGGER.info("Recipe viewer: {} recipes indexed in {} ms", index.count, (System.nanoTime() - start) / 1_000_000);
        }
        return index;
    }

    private static Index build(RegistryAccess access, ContextMap ctx) {
        Index idx = new Index();
        for (byte[] bytes : parts) {
            RegistryFriendlyByteBuf buf = new RegistryFriendlyByteBuf(Unpooled.wrappedBuffer(bytes), access);
            try {
                String[] types = new String[buf.readVarInt()];
                for (int i = 0; i < types.length; i++) {
                    types[i] = buf.readIdentifier().toString();
                }
                int n = buf.readVarInt();
                for (int i = 0; i < n; i++) {
                    Identifier id = buf.readIdentifier();
                    String type = types[buf.readVarInt()];
                    RecipeDisplay display = RecipeDisplay.STREAM_CODEC.decode(buf);
                    ViewRecipe r = convert(id, type, display, ctx);
                    if (r != null && !r.outputs().isEmpty()) {
                        add(idx, r);
                    }
                }
            } catch (RuntimeException e) {
                Brasshaven.LOGGER.warn("Recipe viewer: a part of the server's recipes could not be read: {}", e.toString());
            }
        }
        return idx;
    }

    private static void add(Index idx, ViewRecipe r) {
        idx.count++;
        idx.byCategory.computeIfAbsent(r.category(), k -> new ArrayList<>()).add(r);
        for (ItemStack out : r.outputs()) {
            addTo(idx.byOutput, out.getItem(), r);
        }
        for (List<ItemStack> slot : r.inputs()) {
            for (ItemStack in : slot) {
                addTo(idx.byInput, in.getItem(), r);
            }
        }
    }

    private static void addTo(Map<Item, List<ViewRecipe>> map, Item item, ViewRecipe r) {
        List<ViewRecipe> list = map.computeIfAbsent(item, k -> new ArrayList<>(2));
        if (list.isEmpty() || list.get(list.size() - 1) != r) {
            list.add(r);
        }
    }

    private static List<ItemStack> resolve(SlotDisplay slot, ContextMap ctx) {
        try {
            return List.copyOf(slot.resolveForStacks(ctx).stream().filter(s -> !s.isEmpty()).toList());
        } catch (RuntimeException e) {
            return List.of();
        }
    }

    private static List<List<ItemStack>> slots(List<SlotDisplay> displays, ContextMap ctx) {
        List<List<ItemStack>> out = new ArrayList<>(displays.size());
        for (SlotDisplay d : displays) {
            out.add(resolve(d, ctx));
        }
        return List.copyOf(out);
    }

    private static ViewRecipe convert(Identifier id, String type, RecipeDisplay display, ContextMap ctx) {
        RecipeCategory byType = RecipeCategory.ofType(type);
        boolean vanilla = byType != null;
        List<ItemStack> result = resolve(display.result(), ctx);
        List<ItemStack> station = resolve(display.craftingStation(), ctx);
        if (display instanceof ShapedCraftingRecipeDisplay s) {
            return new ViewRecipe(id, RecipeCategory.CRAFTING, s.width(), s.height(), slots(s.ingredients(), ctx), result, station,
                    0, 0, byType == RecipeCategory.CRAFTING);
        }
        if (display instanceof ShapelessCraftingRecipeDisplay s) {
            return new ViewRecipe(id, RecipeCategory.CRAFTING, 0, 0, slots(s.ingredients(), ctx), result, station, 0, 0,
                    byType == RecipeCategory.CRAFTING);
        }
        if (display instanceof FurnaceRecipeDisplay f) {
            RecipeCategory cat = byType != null && byType.cooking() ? byType
                    : !station.isEmpty() && RecipeCategory.ofStation(station.get(0).getItem()) != null
                    && RecipeCategory.ofStation(station.get(0).getItem()).cooking() ? RecipeCategory.ofStation(station.get(0).getItem())
                    : RecipeCategory.SMELTING;
            return new ViewRecipe(id, cat, 0, 0, List.of(resolve(f.ingredient(), ctx)), result, station, f.duration(), f.experience(),
                    vanilla && cat == byType);
        }
        if (display instanceof StonecutterRecipeDisplay s) {
            return new ViewRecipe(id, RecipeCategory.STONECUTTING, 0, 0, List.of(resolve(s.input(), ctx)), result, station, 0, 0, vanilla);
        }
        if (display instanceof SmithingRecipeDisplay s) {
            return new ViewRecipe(id, RecipeCategory.SMITHING, 0, 0,
                    List.of(resolve(s.template(), ctx), resolve(s.base(), ctx), resolve(s.addition(), ctx)), result, station, 0, 0, vanilla);
        }
        return new ViewRecipe(id, RecipeCategory.OTHER, 0, 0, List.of(), result, station, 0, 0, false);
    }

    // ------------------------------------------------------------------ queries

    /** The recipes that make this item, per tab (tab order). */
    public static Map<RecipeCategory, List<ViewRecipe>> recipes(ItemStack stack) {
        EnumMap<RecipeCategory, List<ViewRecipe>> out = new EnumMap<>(RecipeCategory.class);
        Index idx = index();
        if (idx != null) {
            for (ViewRecipe r : idx.byOutput.getOrDefault(stack.getItem(), List.of())) {
                out.computeIfAbsent(r.category(), k -> new ArrayList<>()).add(r);
            }
        }
        ChiselFamilies.Family family = family(stack);
        if (family != null) {
            List<ItemStack> others = members(family, stack.getItem());
            out.put(RecipeCategory.CHISEL, List.of(chisel(others, List.of(new ItemStack(stack.getItem())))));
        }
        return out;
    }

    /** The recipes that use this item (and, for a crafting table, furnace..., every recipe made there), per tab. */
    public static Map<RecipeCategory, List<ViewRecipe>> uses(ItemStack stack) {
        EnumMap<RecipeCategory, List<ViewRecipe>> out = new EnumMap<>(RecipeCategory.class);
        Index idx = index();
        RecipeCategory station = RecipeCategory.ofStation(stack.getItem());
        if (station == RecipeCategory.CHISEL) {
            List<ViewRecipe> all = new ArrayList<>();
            for (ChiselFamilies.Family f : ChiselFamilies.clientFamilies()) {
                List<ItemStack> members = members(f, null);
                all.add(chisel(members, members));
            }
            if (!all.isEmpty()) {
                out.put(RecipeCategory.CHISEL, all);
            }
        } else if (station != null && idx != null && idx.byCategory.containsKey(station)) {
            out.put(station, new ArrayList<>(idx.byCategory.get(station)));
        }
        if (idx != null) {
            for (ViewRecipe r : idx.byInput.getOrDefault(stack.getItem(), List.of())) {
                if (r.category() != station) {
                    out.computeIfAbsent(r.category(), k -> new ArrayList<>()).add(r);
                }
            }
        }
        ChiselFamilies.Family family = family(stack);
        if (family != null && station != RecipeCategory.CHISEL) {
            out.put(RecipeCategory.CHISEL, List.of(chisel(List.of(new ItemStack(stack.getItem())), members(family, stack.getItem()))));
        }
        return out;
    }

    private static ChiselFamilies.Family family(ItemStack stack) {
        Minecraft mc = Minecraft.getInstance();
        return mc.level == null ? null : ChiselFamilies.family(mc.level, stack);
    }

    /** The family's blocks as items, without {@code except}. */
    private static List<ItemStack> members(ChiselFamilies.Family family, Item except) {
        List<ItemStack> out = new ArrayList<>();
        for (Block b : family.blocks()) {
            Item item = b.asItem();
            if (item != except && item != net.minecraft.world.item.Items.AIR) {
                out.add(new ItemStack(item));
            }
        }
        return List.copyOf(out);
    }

    private static ViewRecipe chisel(List<ItemStack> input, List<ItemStack> outputs) {
        return new ViewRecipe(null, RecipeCategory.CHISEL, 0, 0, List.of(input), outputs,
                List.of(RecipeCategory.CHISEL.icon()), 0, 0, false);
    }
}
