package com.brasshaven.client.recipes;

import net.minecraft.resources.Identifier;
import net.minecraft.world.item.ItemStack;
import org.jetbrains.annotations.Nullable;

import java.util.List;

/**
 * One recipe as the viewer draws it, its slots already resolved to items (a tag slot holds every item of the tag;
 * the screen cycles through them once a second).
 *
 * @param id       the recipe id (null for the chisel families, which are not recipes)
 * @param width    crafting: the grid width of a shaped recipe (its inputs fill a width x height grid); 0 when shapeless
 * @param height   crafting: the grid height of a shaped recipe
 * @param inputs   one list per input slot (empty list: empty slot). Smithing: template, base, addition
 * @param outputs  the result (several: cycled), or for the chisel families every block the input can become (a grid)
 * @param station  what does the work (for unknown recipe types)
 * @param cookTime ticks, for furnace recipes
 * @param xp       experience, for furnace recipes
 * @param vanillaType the recipe is of a vanilla type (crafting, smelting...): the "+" button may place it
 */
public record ViewRecipe(@Nullable Identifier id, RecipeCategory category, int width, int height, List<List<ItemStack>> inputs,
                         List<ItemStack> outputs, List<ItemStack> station, int cookTime, float xp, boolean vanillaType) {
    public boolean shapeless() {
        return category == RecipeCategory.CRAFTING && width == 0;
    }

    /** Fits the 2x2 grid of the player's inventory. */
    public boolean fitsInventoryGrid() {
        if (category != RecipeCategory.CRAFTING) {
            return false;
        }
        if (width > 0) {
            return width <= 2 && height <= 2;
        }
        int n = 0;
        for (List<ItemStack> in : inputs) {
            if (!in.isEmpty()) {
                n++;
            }
        }
        return n <= 4;
    }
}
