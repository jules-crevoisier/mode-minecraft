package com.brasshaven.recipe;

import net.minecraft.core.registries.Registries;
import net.minecraft.network.protocol.game.ClientboundPlaceGhostRecipePacket;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.AbstractCraftingMenu;
import net.minecraft.world.inventory.AbstractFurnaceMenu;
import net.minecraft.world.inventory.RecipeBookMenu;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.item.crafting.ShapedRecipe;
import net.minecraft.world.item.crafting.display.RecipeDisplay;
import net.minecraft.world.level.gamerules.GameRules;

/**
 * The recipe viewer's "+" button, on the server: fills the open crafting grid (crafting table, the inventory's 2x2,
 * furnaces) with the items of one recipe, taken from the player's inventory.
 *
 * <p>The moving itself is vanilla's recipe-book placement ({@link RecipeBookMenu#handlePlacement}, i.e.
 * {@code ServerPlaceRecipe}): the grid's current items go back to the inventory, then the recipe's ingredients are
 * moved from the inventory into the grid, once or as many times as possible. The client only names the recipe; no item
 * comes from it, so nothing can be duplicated. What this adds over the vanilla packet is that the recipe need not be
 * unlocked in the player's recipe book (the viewer shows every recipe) - unless the {@code limited_crafting} game rule
 * is on, where crafting itself needs the recipe unlocked - and checks the vanilla packet leaves to the client: the
 * menu is the one open, still valid, and of the recipe's kind, and the recipe fits its grid.
 */
public final class RecipeFill {
    private RecipeFill() {}

    public static void place(ServerPlayer player, int containerId, Identifier recipeId, boolean max) {
        AbstractContainerMenu open = player.containerMenu;
        if (open.containerId != containerId || !(open instanceof RecipeBookMenu menu) || !open.stillValid(player)) {
            return;
        }
        ServerLevel level = player.level();
        RecipeHolder<?> recipe = level.getServer().getRecipeManager()
                .byKey(ResourceKey.create(Registries.RECIPE, recipeId)).orElse(null);
        if (recipe == null || recipe.value().isSpecial() || recipe.value().placementInfo().isImpossibleToPlace()
                || !fits(menu, recipe.value())) {
            return;
        }
        if (level.getGameRules().get(GameRules.LIMITED_CRAFTING) && !player.getRecipeBook().contains(recipe.id())) {
            return;
        }
        RecipeBookMenu.PostPlaceAction after = menu.handlePlacement(max, player.isCreative(), recipe, level, player.getInventory());
        if (after == RecipeBookMenu.PostPlaceAction.PLACE_GHOST_RECIPE) {
            // missing ingredients: the recipe's outline in the grid, like the recipe book does
            RecipeDisplay[] first = new RecipeDisplay[1];
            level.getServer().getRecipeManager().listDisplaysForRecipe(recipe.id(), e -> {
                if (first[0] == null) {
                    first[0] = e.display();
                }
            });
            if (first[0] != null) {
                player.connection.send(new ClientboundPlaceGhostRecipePacket(containerId, first[0]));
            }
        }
    }

    /** The recipe is of the menu's kind and fits its grid (a 3x3 recipe never goes into the inventory's 2x2). */
    static boolean fits(RecipeBookMenu menu, Recipe<?> recipe) {
        if (menu instanceof AbstractCraftingMenu crafting) {
            if (recipe.getType() != RecipeType.CRAFTING) {
                return false;
            }
            int slots = crafting.getInputGridSlots().size();
            int side = slots <= 4 ? 2 : 3;
            if (recipe instanceof ShapedRecipe shaped) {
                return shaped.getWidth() <= side && shaped.getHeight() <= side;
            }
            return recipe.placementInfo().ingredients().size() <= slots;
        }
        if (menu instanceof AbstractFurnaceMenu) {
            RecipeType<?> type = switch (menu.getRecipeBookType()) {
                case FURNACE -> RecipeType.SMELTING;
                case BLAST_FURNACE -> RecipeType.BLASTING;
                case SMOKER -> RecipeType.SMOKING;
                default -> null;
            };
            return type != null && recipe.getType() == type;
        }
        return false; // another mod's recipe-book menu: its grid is unknown
    }
}
