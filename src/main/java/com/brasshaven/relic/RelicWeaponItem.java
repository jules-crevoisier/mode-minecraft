package com.brasshaven.relic;

import com.brasshaven.item.BossWeaponItem;
import com.brasshaven.item.BrassTooltip;
import com.brasshaven.util.Targets;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;

import java.util.List;
import java.util.function.Supplier;

/**
 * A relic weapon: one of the boss weapon abilities ({@link BossWeaponItem}), then its signature: effects for the
 * wielder, foes around frozen solid, or the recoil of a hand-cannon.
 */
public class RelicWeaponItem extends BossWeaponItem {
    /** What the weapon adds after its ability: self effects, freezing the foes in reach, a recoil push. */
    public record Signature(List<Supplier<MobEffectInstance>> self, boolean freeze, boolean recoil) {}

    private final String structure;
    private final Signature signature;
    private final float reach;

    public RelicWeaponItem(Properties properties, Ability ability, float power, float size, int cooldown,
                           ParticleOptions particle, int flags, String structure, Signature signature) {
        super(properties, ability, power, size, cooldown, particle, flags);
        this.structure = structure;
        this.signature = signature;
        this.reach = size;
    }

    @Override
    protected boolean activate(ServerLevel level, Player player, ItemStack stack) {
        if (!super.activate(level, player, stack)) {
            return false;
        }
        for (Supplier<MobEffectInstance> effect : signature.self()) {
            player.addEffect(effect.get());
        }
        if (signature.freeze()) {
            for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, player.getBoundingBox().inflate(reach, 2, reach),
                    e -> Targets.foe(player, e) && e.distanceTo(player) <= reach + 0.5)) {
                e.setTicksFrozen(Math.max(e.getTicksFrozen(), e.getTicksRequiredToFreeze() + 80));
                level.sendParticles(ParticleTypes.SNOWFLAKE, e.getX(), e.getY() + e.getBbHeight() / 2, e.getZ(),
                        10, 0.3, 0.5, 0.3, 0.02);
            }
        }
        if (signature.recoil()) {
            Vec3 back = player.getLookAngle().multiply(1, 0, 1).normalize().scale(-0.9);
            player.setDeltaMovement(back.x, 0.25, back.z);
            player.hurtMarked = true;
        }
        return true;
    }

    @Override
    public void facts(ItemStack stack, List<Component> facts, List<Component> details) {
        super.facts(stack, facts, details);
        for (Supplier<MobEffectInstance> s : signature.self()) {
            MobEffectInstance e = s.get();
            MutableComponent name = Component.translatable(e.getDescriptionId());
            if (e.getAmplifier() > 0) {
                name.append(" ").append(Component.translatable("potion.potency." + e.getAmplifier()));
            }
            details.add(BrassTooltip.detail(Component.translatable("tooltip.brasshaven.relic.self", name,
                    BrassTooltip.seconds(e.getDuration()))));
        }
        if (signature.freeze()) {
            details.add(BrassTooltip.detail(Component.translatable("tooltip.brasshaven.relic.freeze")));
        }
        details.add(RelicItem.origin(structure));
    }
}
