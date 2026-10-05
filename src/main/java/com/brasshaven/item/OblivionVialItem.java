package com.brasshaven.item;

import com.brasshaven.skill.PlayerSkills;
import com.brasshaven.skill.SkillEvents;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;

/** Vial of Oblivion: drink to forget every talent and get all the points back. */
public class OblivionVialItem extends TooltipItem {
    public OblivionVialItem(Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResult use(Level level, Player player, InteractionHand hand) {
        if (player instanceof ServerPlayer sp) {
            if (PlayerSkills.unlocked(sp).isEmpty()) {
                sp.sendOverlayMessage(Component.translatable("message.brasshaven.skill.nothing_to_forget").withStyle(ChatFormatting.GRAY));
                return InteractionResult.FAIL;
            }
            PlayerSkills.reset(sp);
            SkillEvents.sync(sp);
            if (!sp.isCreative()) {
                player.getItemInHand(hand).shrink(1);
            }
            sp.sendSystemMessage(Component.translatable("message.brasshaven.skill.reset").withStyle(ChatFormatting.LIGHT_PURPLE));
            level.playSound(null, player, SoundEvents.ZOMBIE_VILLAGER_CURE, SoundSource.PLAYERS, 0.6F, 1.6F);
        }
        return InteractionResult.SUCCESS;
    }
}
