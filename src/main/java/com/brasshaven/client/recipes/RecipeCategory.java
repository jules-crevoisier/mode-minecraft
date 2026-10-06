package com.brasshaven.client.recipes;

import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

import java.util.Locale;

/**
 * The recipe viewer's tabs: one per way of making things, each with the block that does it (its icon, and its "uses"
 * list shows every recipe of the tab) and the size of one recipe's cell in the recipe screen.
 */
public enum RecipeCategory {
    CRAFTING("minecraft:crafting_table", 136, 62),
    SMELTING("minecraft:furnace", 136, 40),
    BLASTING("minecraft:blast_furnace", 136, 40),
    SMOKING("minecraft:smoker", 136, 40),
    CAMPFIRE("minecraft:campfire", 136, 40),
    STONECUTTING("minecraft:stonecutter", 90, 26),
    SMITHING("minecraft:smithing_table", 136, 26),
    /** The Chisel Table's families (data/<ns>/chisel), built on the client from ChiselFamilies. */
    CHISEL("brasshaven:chisel_table", 276, 44),
    /** Recipe types the viewer does not know how to draw (other mods): their result and station. */
    OTHER("minecraft:knowledge_book", 90, 26);

    public final String stationId;
    /** Size of one recipe in the recipe screen, GUI pixels. */
    public final int cellW;
    public final int cellH;
    private ItemStack icon;

    RecipeCategory(String stationId, int cellW, int cellH) {
        this.stationId = stationId;
        this.cellW = cellW;
        this.cellH = cellH;
    }

    public ItemStack icon() {
        if (icon == null) {
            icon = BuiltInRegistries.ITEM.getOptional(Identifier.parse(stationId)).map(ItemStack::new)
                    .orElse(new ItemStack(Items.BOOK));
        }
        return icon;
    }

    public Component title() {
        return Component.translatable("gui.brasshaven.recipes.cat." + name().toLowerCase(Locale.ROOT));
    }

    public boolean cooking() {
        return this == SMELTING || this == BLASTING || this == SMOKING || this == CAMPFIRE;
    }

    /** The category a vanilla recipe type id stands for (null: decide from the display). */
    static RecipeCategory ofType(String type) {
        return switch (type) {
            case "minecraft:crafting" -> CRAFTING;
            case "minecraft:smelting" -> SMELTING;
            case "minecraft:blasting" -> BLASTING;
            case "minecraft:smoking" -> SMOKING;
            case "minecraft:campfire_cooking" -> CAMPFIRE;
            case "minecraft:stonecutting" -> STONECUTTING;
            case "minecraft:smithing" -> SMITHING;
            default -> null;
        };
    }

    /** The categories whose "uses" are all their recipes when this item is looked up: the blocks that do the work. */
    static RecipeCategory ofStation(Item item) {
        String id = BuiltInRegistries.ITEM.getKey(item).toString();
        return switch (id) {
            case "minecraft:crafting_table", "minecraft:crafter" -> CRAFTING;
            case "minecraft:furnace" -> SMELTING;
            case "minecraft:blast_furnace" -> BLASTING;
            case "minecraft:smoker" -> SMOKING;
            case "minecraft:campfire", "minecraft:soul_campfire" -> CAMPFIRE;
            case "minecraft:stonecutter" -> STONECUTTING;
            case "minecraft:smithing_table" -> SMITHING;
            case "brasshaven:chisel_table", "brasshaven:chisel" -> CHISEL;
            default -> null;
        };
    }
}
