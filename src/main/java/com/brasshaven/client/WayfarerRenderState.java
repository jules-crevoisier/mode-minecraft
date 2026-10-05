package com.brasshaven.client;

import com.brasshaven.generated.MobAnims;
import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;
import net.minecraft.world.entity.AnimationState;

/** Render state shared by every generated Brasshaven model: one animation state per action. */
public class WayfarerRenderState extends LivingEntityRenderState {
    public final AnimationState[] actions = new AnimationState[MobAnims.MAX_ACTIONS];
    /** Colour variant (index into the renderer's textures). */
    public int variant;

    public WayfarerRenderState() {
        for (int i = 0; i < actions.length; i++) {
            actions[i] = new AnimationState();
        }
    }
}
