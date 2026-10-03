package com.wayfarers.client;

import com.wayfarers.generated.MobAnims;
import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;
import net.minecraft.world.entity.AnimationState;

/** Render state shared by every generated Wayfarers model: one animation state per action. */
public class WayfarerRenderState extends LivingEntityRenderState {
    public final AnimationState[] actions = new AnimationState[MobAnims.MAX_ACTIONS];

    public WayfarerRenderState() {
        for (int i = 0; i < actions.length; i++) {
            actions[i] = new AnimationState();
        }
    }
}
