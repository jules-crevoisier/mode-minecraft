package com.wayfarers.network;

import com.wayfarers.skill.PlayerSkills;
import com.wayfarers.skill.SkillEvents;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraftforge.event.network.CustomPayloadEvent;

/** Client → server: unlock a talent, choose the active ability, use it (V), or ask for a sync. */
public record SkillActionMsg(Action action, String id) {
    public enum Action { UNLOCK, SET_ACTIVE, USE_ACTIVE, REQUEST }

    public static final StreamCodec<RegistryFriendlyByteBuf, SkillActionMsg> STREAM_CODEC =
            StreamCodec.ofMember((m, buf) -> {
                buf.writeEnum(m.action);
                buf.writeUtf(m.id, 64);
            }, buf -> new SkillActionMsg(buf.readEnum(Action.class), buf.readUtf(64)));

    static void handle(SkillActionMsg msg, CustomPayloadEvent.Context ctx) {
        ServerPlayer p = ctx.getSender();
        // the V key may be held: abilities have their own cooldown, the bucket only stops a flood of syncs
        if (p == null || p.hasDisconnected() || !com.wayfarers.util.ServerGuard.allow(p, "skill", 10, 5.0)) {
            return;
        }
        if (msg.action != Action.REQUEST && !com.wayfarers.util.ServerGuard.canAct(p)) {
            return;
        }
        switch (msg.action) {
            case UNLOCK -> {
                if (PlayerSkills.unlock(p, msg.id)) {
                    p.level().playSound(null, p, SoundEvents.PLAYER_LEVELUP, SoundSource.PLAYERS, 0.7F, 1.4F);
                }
            }
            case SET_ACTIVE -> PlayerSkills.skill(msg.id)
                    .filter(s -> s.kind().equals("active") && PlayerSkills.unlocked(p).contains(s.id()))
                    .ifPresent(s -> PlayerSkills.setActive(p, s.ability()));
            case USE_ACTIVE -> SkillEvents.useActive(p);
            case REQUEST -> { }
        }
        SkillEvents.sync(p);
    }
}
