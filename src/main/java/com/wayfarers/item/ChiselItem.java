package com.wayfarers.item;

import com.wayfarers.chisel.ChiselFamilies;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.gameevent.GameEvent;
import net.minecraft.world.phys.Vec3;

/**
 * Engraver's Chisel: right-click a block to turn it into the next variant of its family (stone → stone bricks →
 * mossy → cracked → chiseled...), sneak-right-click for the previous one. Stairs, slabs and walls keep their shape;
 * copper keeps its oxidation and wax. Costs one durability per cut. Families: {@link ChiselFamilies}.
 */
public class ChiselItem extends TooltipItem {
    public ChiselItem(Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResult useOn(UseOnContext ctx) {
        Level level = ctx.getLevel();
        Player player = ctx.getPlayer();
        if (player == null) {
            return InteractionResult.PASS;
        }
        BlockPos pos = ctx.getClickedPos();
        BlockState state = level.getBlockState(pos);
        ChiselFamilies.Family family = ChiselFamilies.family(level, state.getBlock());
        if (family == null || state.hasBlockEntity()) {
            if (!level.isClientSide()) {
                player.sendOverlayMessage(Component.translatable("message.wayfarers.chisel.none", state.getBlock().getName())
                        .withStyle(ChatFormatting.GRAY));
            }
            return InteractionResult.FAIL;
        }
        if (!player.mayBuild() || !level.mayInteract(player, pos) || !player.mayUseItemAt(pos, ctx.getClickedFace(), ctx.getItemInHand())) {
            return InteractionResult.FAIL;
        }
        BlockState next = family.step(state, player.isShiftKeyDown() ? -1 : 1);
        if (next == state) {
            return InteractionResult.FAIL;
        }
        if (level instanceof ServerLevel server) {
            server.setBlock(pos, next, Block.UPDATE_ALL);
            server.gameEvent(GameEvent.BLOCK_CHANGE, pos, GameEvent.Context.of(player, next));
            Vec3 hit = ctx.getClickLocation();
            server.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, state), hit.x, hit.y, hit.z, 14, 0.18, 0.18, 0.18, 0.08);
            server.sendParticles(ParticleTypes.CRIT, hit.x, hit.y, hit.z, 4, 0.1, 0.1, 0.1, 0.25);
            float pitch = 0.9F + level.getRandom().nextFloat() * 0.3F;
            level.playSound(null, pos, next.getSoundType().getHitSound(), SoundSource.BLOCKS, 0.9F, pitch);
            level.playSound(null, pos, SoundEvents.UI_STONECUTTER_TAKE_RESULT, SoundSource.BLOCKS, 0.5F, pitch + 0.2F);
            ctx.getItemInHand().hurtAndBreak(1, player, ctx.getHand());
            int index = family.indexOf(next.getBlock()) + 1;
            player.sendOverlayMessage(Component.translatable("message.wayfarers.chisel.variant", next.getBlock().getName(),
                    index, family.blocks().size()).withStyle(ChatFormatting.GOLD));
        }
        return InteractionResult.SUCCESS;
    }
}
