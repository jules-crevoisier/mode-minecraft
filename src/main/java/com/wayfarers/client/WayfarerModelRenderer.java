package com.wayfarers.client;

import com.wayfarers.Wayfarers;
import com.wayfarers.entity.AnimatedMob;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.client.renderer.entity.layers.LivingEntityEmissiveLayer;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.AnimationState;
import net.minecraft.world.entity.Mob;

/** Renderer for every creature with a generated model: texture, optional glowing layer, action animations. */
public class WayfarerModelRenderer<T extends Mob & AnimatedMob>
        extends MobRenderer<T, WayfarerRenderState, EntityModel<WayfarerRenderState>> {
    private final Identifier texture;

    public WayfarerModelRenderer(EntityRendererProvider.Context context, EntityModel<WayfarerRenderState> model,
                                 float shadow, String name, boolean glow) {
        super(context, model, shadow);
        this.texture = Wayfarers.id("textures/entity/" + name + ".png");
        if (glow) {
            Identifier glowTexture = Wayfarers.id("textures/entity/" + name + "_glow.png");
            addLayer(new LivingEntityEmissiveLayer<>(this, state -> glowTexture, (state, age) -> 1.0F, model,
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
        AnimationState[] source = entity.actionStates();
        for (int i = 0; i < state.actions.length && i < source.length; i++) {
            state.actions[i].copyFrom(source[i]);
        }
    }

    @Override
    public Identifier getTextureLocation(WayfarerRenderState state) {
        return texture;
    }
}
