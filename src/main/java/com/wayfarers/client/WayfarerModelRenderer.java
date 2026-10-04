package com.wayfarers.client;

import com.wayfarers.Wayfarers;
import com.wayfarers.entity.AnimatedMob;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.client.renderer.entity.layers.LivingEntityEmissiveLayer;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.AnimationState;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.phys.AABB;

/**
 * Renderer for every creature with a generated model: texture (one per colour variant), optional glowing layer
 * (steady or pulsing), action animations.
 */
public class WayfarerModelRenderer<T extends Mob & AnimatedMob>
        extends MobRenderer<T, WayfarerRenderState, EntityModel<WayfarerRenderState>> {
    private final Identifier[] textures;

    public WayfarerModelRenderer(EntityRendererProvider.Context context, EntityModel<WayfarerRenderState> model,
                                 float shadow, String name, boolean glow) {
        this(context, model, shadow, new String[] {name}, glow, 0.0F);
    }

    /**
     * @param names     texture of each variant (textures/entity/NAME.png, glow layer NAME_glow.png)
     * @param glowPulse 0 for a steady glow, else the angular speed (per tick) of a soft breathing pulse
     */
    public WayfarerModelRenderer(EntityRendererProvider.Context context, EntityModel<WayfarerRenderState> model,
                                 float shadow, String[] names, boolean glow, float glowPulse) {
        super(context, model, shadow);
        this.textures = new Identifier[names.length];
        Identifier[] glows = new Identifier[names.length];
        for (int i = 0; i < names.length; i++) {
            textures[i] = Wayfarers.id("textures/entity/" + names[i] + ".png");
            glows[i] = Wayfarers.id("textures/entity/" + names[i] + "_glow.png");
        }
        if (glow) {
            addLayer(new LivingEntityEmissiveLayer<>(this, state -> glows[Math.floorMod(state.variant, glows.length)],
                    (state, age) -> glowPulse > 0.0F ? 0.55F + 0.45F * Mth.sin(age * glowPulse) : 1.0F, model,
                    RenderTypes::entityTranslucentEmissive, false));
        }
    }

    @Override
    public WayfarerRenderState createRenderState() {
        return new WayfarerRenderState();
    }

    @Override
    public void extractRenderState(T entity, WayfarerRenderState state, float partialTicks) {
        super.extractRenderState(entity, state, partialTicks);
        state.variant = entity.modelVariant();
        AnimationState[] source = entity.actionStates();
        for (int i = 0; i < state.actions.length && i < source.length; i++) {
            state.actions[i].copyFrom(source[i]);
        }
    }

    @Override
    public Identifier getTextureLocation(WayfarerRenderState state) {
        return textures[Math.floorMod(state.variant, textures.length)];
    }

    @Override
    protected AABB getBoundingBoxForCulling(T entity) {
        // long creatures (sea serpent, whale) are drawn far outside their hitbox
        return entity.cullingBox(super.getBoundingBoxForCulling(entity));
    }
}
