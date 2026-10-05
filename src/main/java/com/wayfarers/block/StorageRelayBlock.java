package com.wayfarers.block;

import com.mojang.serialization.MapCodec;
import com.wayfarers.config.WayfarersConfig;
import com.wayfarers.util.StorageNetwork;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;

/**
 * Storage Relay: extends a Guild Terminal's network. Every container within reach of the relay is linked, as long as
 * the relay is within reach of the terminal or of another linked relay. Right-click: tells whether it is linked.
 */
public class StorageRelayBlock extends BaseEntityBlock {
    public static final MapCodec<StorageRelayBlock> CODEC = simpleCodec(StorageRelayBlock::new);

    public StorageRelayBlock(Properties properties) {
        super(properties);
    }

    @Override
    protected MapCodec<? extends BaseEntityBlock> codec() {
        return CODEC;
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new StorageRelayBlockEntity(pos, state);
    }

    @Override
    protected RenderShape getRenderShape(BlockState state) {
        return RenderShape.MODEL;
    }

    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        // following the relay chain walks every block entity around up to 64 relays: a few times a second at most
        if (level instanceof ServerLevel serverLevel && player instanceof net.minecraft.server.level.ServerPlayer sp
                && com.wayfarers.util.ServerGuard.allow(sp, "relay_use", 3, 1.0)) {
            BlockPos terminal = StorageNetwork.findTerminal(serverLevel, pos);
            if (terminal != null) {
                player.sendOverlayMessage(Component.translatable("message.wayfarers.relay.linked",
                        terminal.getX(), terminal.getY(), terminal.getZ()).withStyle(ChatFormatting.GOLD));
                serverLevel.sendParticles(ParticleTypes.WAX_ON, pos.getX() + 0.5, pos.getY() + 1.1, pos.getZ() + 0.5,
                        8, 0.3, 0.2, 0.3, 0.0);
            } else {
                player.sendOverlayMessage(Component.translatable("message.wayfarers.relay.unlinked",
                        StorageNetwork.terminalRange(), WayfarersConfig.RELAY_RANGE.get()).withStyle(ChatFormatting.RED));
            }
        }
        return InteractionResult.SUCCESS;
    }
}
