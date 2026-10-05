package com.brasshaven.command;

import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import com.brasshaven.entity.WayfarerNpc;
import com.brasshaven.generated.GeneratedNpcs;
import com.brasshaven.registry.ModEntities;
import com.brasshaven.util.NpcQuests;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.commands.arguments.EntityArgument;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.phys.AABB;

import java.util.Comparator;
import java.util.List;

/**
 * Operators: place, move, re-role and remove quest givers, reset a player's contracts.
 * <pre>
 *   /brasshaven npc spawn &lt;role&gt;     a quest giver where you stand, facing you
 *   /brasshaven npc move               the nearest one (within 8 blocks) comes to where you stand: its new post
 *   /brasshaven npc role &lt;role&gt;      the nearest one takes another role (and texture, and contracts)
 *   /brasshaven npc remove             removes the nearest one
 *   /brasshaven contracts reset [player]
 * </pre>
 */
public final class NpcCommand {
    private static final double REACH = 8.0;

    private NpcCommand() {}

    /** {@code /brasshaven npc ...} under {@code root} (the "npc" literal, operators only). */
    public static LiteralArgumentBuilder<CommandSourceStack> npc(LiteralArgumentBuilder<CommandSourceStack> root) {
        return root
                .then(Commands.literal("spawn").then(Commands.argument("role", StringArgumentType.word())
                        .suggests((ctx, b) -> SharedSuggestionProvider.suggest(GeneratedNpcs.ROLES, b))
                        .executes(ctx -> spawn(ctx, StringArgumentType.getString(ctx, "role")))))
                .then(Commands.literal("move").executes(NpcCommand::move))
                .then(Commands.literal("role").then(Commands.argument("role", StringArgumentType.word())
                        .suggests((ctx, b) -> SharedSuggestionProvider.suggest(GeneratedNpcs.ROLES, b))
                        .executes(ctx -> role(ctx, StringArgumentType.getString(ctx, "role")))))
                .then(Commands.literal("remove").executes(NpcCommand::remove));
    }

    /** {@code /brasshaven contracts reset [player]} under {@code root} (the "contracts" literal). */
    public static LiteralArgumentBuilder<CommandSourceStack> contracts(LiteralArgumentBuilder<CommandSourceStack> root) {
        return root
                .then(Commands.literal("reset")
                        .executes(ctx -> reset(ctx, ctx.getSource().getPlayerOrException()))
                        .then(Commands.argument("player", EntityArgument.player())
                                .executes(ctx -> reset(ctx, EntityArgument.getPlayer(ctx, "player")))));
    }

    private static WayfarerNpc nearest(ServerPlayer player) {
        List<WayfarerNpc> near = player.level().getEntitiesOfClass(WayfarerNpc.class,
                new AABB(player.blockPosition()).inflate(REACH), Entity::isAlive);
        return near.stream().min(Comparator.comparingDouble(player::distanceToSqr)).orElse(null);
    }

    private static int spawn(CommandContext<CommandSourceStack> ctx, String role) throws CommandSyntaxException {
        ServerPlayer player = ctx.getSource().getPlayerOrException();
        if (!GeneratedNpcs.ROLES.contains(role)) {
            ctx.getSource().sendFailure(Component.literal("Unknown role: " + role + " " + GeneratedNpcs.ROLES));
            return 0;
        }
        ServerLevel level = (ServerLevel) player.level();
        WayfarerNpc npc = ModEntities.WAYFARER_NPC.get().create(level, EntitySpawnReason.COMMAND);
        if (npc == null) {
            return 0;
        }
        BlockPos pos = player.blockPosition();
        npc.snapTo(pos.getX() + 0.5, pos.getY(), pos.getZ() + 0.5, player.getYRot() + 180.0F, 0.0F);
        npc.setYHeadRot(player.getYRot() + 180.0F);
        npc.setRole(role);
        npc.finalizeSpawn(level, level.getCurrentDifficultyAt(pos), EntitySpawnReason.COMMAND, null);
        level.addFreshEntity(npc);
        ctx.getSource().sendSuccess(() -> Component.translatable("message.brasshaven.npc.spawned", npc.getDisplayName()), true);
        return 1;
    }

    private static int move(CommandContext<CommandSourceStack> ctx) throws CommandSyntaxException {
        ServerPlayer player = ctx.getSource().getPlayerOrException();
        WayfarerNpc npc = nearest(player);
        if (npc == null) {
            ctx.getSource().sendFailure(Component.translatable("message.brasshaven.npc.none_near"));
            return 0;
        }
        BlockPos pos = player.blockPosition();
        npc.snapTo(pos.getX() + 0.5, pos.getY(), pos.getZ() + 0.5, player.getYRot() + 180.0F, 0.0F);
        npc.getNavigation().stop();
        npc.setPost(pos);
        ctx.getSource().sendSuccess(() -> Component.translatable("message.brasshaven.npc.moved", npc.getDisplayName()), true);
        return 1;
    }

    private static int role(CommandContext<CommandSourceStack> ctx, String role) throws CommandSyntaxException {
        ServerPlayer player = ctx.getSource().getPlayerOrException();
        WayfarerNpc npc = nearest(player);
        if (npc == null || !GeneratedNpcs.ROLES.contains(role)) {
            ctx.getSource().sendFailure(Component.translatable("message.brasshaven.npc.none_near"));
            return 0;
        }
        npc.setRole(role);
        ctx.getSource().sendSuccess(() -> Component.translatable("message.brasshaven.npc.spawned", npc.getDisplayName()), true);
        return 1;
    }

    private static int remove(CommandContext<CommandSourceStack> ctx) throws CommandSyntaxException {
        ServerPlayer player = ctx.getSource().getPlayerOrException();
        WayfarerNpc npc = nearest(player);
        if (npc == null) {
            ctx.getSource().sendFailure(Component.translatable("message.brasshaven.npc.none_near"));
            return 0;
        }
        npc.discard();
        ctx.getSource().sendSuccess(() -> Component.translatable("message.brasshaven.npc.removed", 1), true);
        return 1;
    }

    private static int reset(CommandContext<CommandSourceStack> ctx, ServerPlayer target) {
        NpcQuests.reset(target);
        ctx.getSource().sendSuccess(() -> Component.translatable("message.brasshaven.npc.reset", target.getDisplayName()), true);
        return 1;
    }
}
