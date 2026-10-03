package com.wayfarers.command;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import com.wayfarers.Wayfarers;
import com.wayfarers.boss.WayfarerBoss;
import com.wayfarers.registry.ModEntities;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.phys.Vec3;
import com.wayfarers.data.WayfarersData;
import com.wayfarers.generated.GeneratedContent;
import com.wayfarers.item.MagnetRingItem;
import com.wayfarers.item.StructureCompassItem;
import com.wayfarers.registry.ModItems;
import com.wayfarers.util.InventoryUtil;
import com.wayfarers.util.QuestBook;
import com.wayfarers.util.StructureLocator;
import com.wayfarers.util.Waystones;
import net.minecraft.ChatFormatting;
import net.minecraft.advancements.AdvancementHolder;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraftforge.event.RegisterCommandsEvent;
import net.minecraftforge.registries.RegistryObject;

import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * {@code /wayfarers ...}. Player-level sub-commands back the clickable chat menus and key
 * bindings (warp, waystones, sort, magnet, atlas); operator sub-commands are for testing and
 * showcasing (kit, locate, tp, progress, demo).
 */
public final class WayfarersCommand {
    private static final Map<String, List<java.util.function.Supplier<? extends Item>>> KITS = Map.of(
            "starter", List.of(ModItems.WAYFARER_ATLAS, ModItems.STRUCTURE_COMPASS, ModItems.TRAVEL_BACKPACK,
                    ModItems.SORTING_CHEST, ModItems.GUILD_TERMINAL, ModItems.WAYSTONE, ModItems.RECALL_SCROLL),
            "explorer", List.of(ModItems.CARTOGRAPHER_BLADE, ModItems.EXPLORER_HELMET, ModItems.EXPLORER_CHESTPLATE,
                    ModItems.EXPLORER_LEGGINGS, ModItems.EXPLORER_BOOTS, ModItems.MAGNET_RING),
            "depths", List.of(ModItems.TELLURIC_HAMMER, ModItems.FROST_BLADE, ModItems.BOOMERANG,
                    ModItems.EXCAVATOR_PICKAXE, ModItems.LUMBER_AXE, ModItems.LIGHT_STAFF),
            "nether", List.of(ModItems.EMBER_SCYTHE, ModItems.STORM_STAFF, ModItems.EMBER_HELMET,
                    ModItems.EMBER_CHESTPLATE, ModItems.EMBER_LEGGINGS, ModItems.EMBER_BOOTS),
            "end", List.of(ModItems.VOID_SPEAR, ModItems.VOID_HELMET, ModItems.VOID_CHESTPLATE,
                    ModItems.VOID_LEGGINGS, ModItems.VOID_BOOTS)
    );

    private WayfarersCommand() {}

    public static void register(RegisterCommandsEvent event) {
        CommandDispatcher<CommandSourceStack> dispatcher = event.getDispatcher();
        dispatcher.register(Commands.literal("wayfarers")
                // ---- everyone (travel itself goes through the waystone screen, which checks you stand at a stone)
                .then(Commands.literal("warp").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                        .then(Commands.argument("id", StringArgumentType.word())
                        .executes(ctx -> warp(ctx, StringArgumentType.getString(ctx, "id")))))
                .then(Commands.literal("waystones").executes(ctx -> {
                    Waystones.list(ctx.getSource().getPlayerOrException(), "");
                    return 1;
                }))
                .then(Commands.literal("sort").executes(ctx -> {
                    ServerPlayer player = ctx.getSource().getPlayerOrException();
                    InventoryUtil.sortPlayer(player);
                    player.sendSystemMessage(Component.translatable("message.wayfarers.sorted").withStyle(ChatFormatting.GRAY));
                    return 1;
                }))
                .then(Commands.literal("magnet").executes(ctx -> {
                    ServerPlayer player = ctx.getSource().getPlayerOrException();
                    for (ItemStack stack : player.getInventory().getNonEquipmentItems()) {
                        if (stack.getItem() instanceof MagnetRingItem) {
                            MagnetRingItem.toggle(player, stack);
                            return 1;
                        }
                    }
                    return 0;
                }))
                .then(Commands.literal("atlas").executes(ctx -> {
                    QuestBook.print(ctx.getSource().getPlayerOrException());
                    return 1;
                }))
                // ---- operators
                .then(Commands.literal("kit").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                        .then(Commands.argument("kit", StringArgumentType.word())
                                .suggests((ctx, b) -> SharedSuggestionProvider.suggest(KITS.keySet(), b))
                                .executes(ctx -> kit(ctx, StringArgumentType.getString(ctx, "kit")))))
                .then(Commands.literal("demo").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                        .executes(WayfarersCommand::demo))
                .then(Commands.literal("locate").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                        .then(Commands.argument("structure", StringArgumentType.word())
                                .suggests((ctx, b) -> SharedSuggestionProvider.suggest(
                                        GeneratedContent.STRUCTURES.stream().map(GeneratedContent.StructureInfo::id), b))
                                .executes(ctx -> locate(ctx, StringArgumentType.getString(ctx, "structure"), false))))
                .then(Commands.literal("tp").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                        .then(Commands.argument("structure", StringArgumentType.word())
                                .suggests((ctx, b) -> SharedSuggestionProvider.suggest(
                                        GeneratedContent.STRUCTURES.stream().map(GeneratedContent.StructureInfo::id), b))
                                .executes(ctx -> locate(ctx, StringArgumentType.getString(ctx, "structure"), true))))
                .then(Commands.literal("boss").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                        .then(Commands.argument("boss", StringArgumentType.word())
                                .suggests((ctx, b) -> SharedSuggestionProvider.suggest(
                                        ModEntities.bosses().stream().map(r -> r.getId().getPath()), b))
                                .executes(ctx -> boss(ctx, StringArgumentType.getString(ctx, "boss")))))
                .then(Commands.literal("worldmap").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                        .executes(WorldMapCommand::run))
                .then(Commands.literal("progress").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                        .then(Commands.literal("reset").executes(ctx -> progress(ctx, false)))
                        .then(Commands.literal("complete").executes(ctx -> progress(ctx, true)))));
    }

    /** Demo: summon a boss 6 blocks in front of you, its arena centred where it appears (radius 20). */
    private static int boss(CommandContext<CommandSourceStack> ctx, String id) throws CommandSyntaxException {
        ServerPlayer player = ctx.getSource().getPlayerOrException();
        for (RegistryObject<? extends EntityType<? extends WayfarerBoss>> type : ModEntities.bosses()) {
            if (!type.getId().getPath().equals(id)) {
                continue;
            }
            WayfarerBoss boss = type.get().create(player.level(), EntitySpawnReason.COMMAND);
            if (boss == null) {
                return 0;
            }
            Vec3 at = player.position().add(player.getLookAngle().multiply(1, 0, 1).normalize().scale(6));
            boss.snapTo(at.x, player.getY(), at.z, player.getYRot() + 180.0F, 0.0F);
            boss.setArena(BlockPos.containing(at.x, player.getY(), at.z), 20, null);
            boss.setTarget(player);
            player.level().addFreshEntity(boss);
            return 1;
        }
        ctx.getSource().sendFailure(Component.literal("Unknown boss: " + id));
        return 0;
    }

    private static int warp(CommandContext<CommandSourceStack> ctx, String id) throws CommandSyntaxException {
        ServerPlayer player = ctx.getSource().getPlayerOrException();
        if (!Waystones.warp(player, id)) {
            ctx.getSource().sendFailure(Component.translatable("message.wayfarers.waystone.unknown"));
            return 0;
        }
        return 1;
    }

    private static int kit(CommandContext<CommandSourceStack> ctx, String name) throws CommandSyntaxException {
        ServerPlayer player = ctx.getSource().getPlayerOrException();
        List<java.util.function.Supplier<? extends Item>> items = KITS.get(name);
        if (items == null) {
            ctx.getSource().sendFailure(Component.literal("Unknown kit: " + name));
            return 0;
        }
        items.forEach(item -> give(player, new ItemStack(item.get())));
        if (name.equals("starter")) {
            give(player, new ItemStack(ModItems.MAP_FRAGMENT.get(), 16));
        }
        ctx.getSource().sendSuccess(() -> Component.translatable("message.wayfarers.kit", name), false);
        return 1;
    }

    private static int demo(CommandContext<CommandSourceStack> ctx) throws CommandSyntaxException {
        ServerPlayer player = ctx.getSource().getPlayerOrException();
        for (RegistryObject<? extends Item> item : ModItems.ALL) {
            give(player, new ItemStack(item.get(), item.get() == ModItems.MAP_FRAGMENT.get() ? 32 : 1));
        }
        give(player, new ItemStack(Items.SPYGLASS));
        ctx.getSource().sendSuccess(() -> Component.translatable("message.wayfarers.kit", "demo"), false);
        return 1;
    }

    private static void give(ServerPlayer player, ItemStack stack) {
        if (!player.getInventory().add(stack)) {
            player.drop(stack, false);
        }
    }

    private static int locate(CommandContext<CommandSourceStack> ctx, String id, boolean teleport) throws CommandSyntaxException {
        ServerPlayer player = ctx.getSource().getPlayerOrException();
        int index = -1;
        for (int i = 0; i < GeneratedContent.STRUCTURES.size(); i++) {
            if (GeneratedContent.STRUCTURES.get(i).id().equals(id)) {
                index = i;
            }
        }
        if (index < 0) {
            ctx.getSource().sendFailure(Component.literal("Unknown structure: " + id));
            return 0;
        }
        ServerLevel level = player.level();
        BlockPos from = player.blockPosition();
        StructureLocator.Found found = StructureLocator.nearest(level, from, index, 160);
        if (found == null) {
            ctx.getSource().sendFailure(Component.translatable("message.wayfarers.compass.none", StructureCompassItem.targetName(index)));
            return 0;
        }
        BlockPos pos = found.pos();
        int distance = (int) Math.sqrt(from.distSqr(new BlockPos(pos.getX(), from.getY(), pos.getZ())));
        ctx.getSource().sendSuccess(() -> Component.translatable("message.wayfarers.locate",
                StructureCompassItem.targetName(GeneratedContent.STRUCTURES.indexOf(GeneratedContent.STRUCTURES.stream()
                        .filter(s -> s.id().equals(found.structureId())).findFirst().orElseThrow())),
                pos.getX(), pos.getZ(), distance), false);
        if (teleport) {
            level.getChunk(pos);
            int y = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, pos.getX(), pos.getZ());
            player.teleportTo(level, pos.getX() + 0.5, y + 1, pos.getZ() + 0.5, Set.of(), player.getYRot(), player.getXRot(), true);
        }
        return 1;
    }

    private static int progress(CommandContext<CommandSourceStack> ctx, boolean complete) {
        MinecraftServer server = ctx.getSource().getServer();
        WayfarersData data = WayfarersData.get(server);
        if (!complete) {
            data.clearQuests();
        }
        for (AdvancementHolder holder : server.getAdvancements().getAllAdvancements()) {
            if (!holder.id().getNamespace().equals(Wayfarers.MODID)) {
                continue;
            }
            if (complete) {
                holder.value().criteria().keySet().forEach(c -> data.markCriterion(holder.id(), c));
            }
            for (ServerPlayer player : server.getPlayerList().getPlayers()) {
                for (String criterion : holder.value().criteria().keySet()) {
                    if (complete) {
                        player.getAdvancements().award(holder, criterion);
                    } else {
                        player.getAdvancements().revoke(holder, criterion);
                    }
                }
            }
        }
        ctx.getSource().sendSuccess(() -> Component.translatable(complete
                ? "message.wayfarers.progress.complete" : "message.wayfarers.progress.reset"), true);
        return 1;
    }
}
