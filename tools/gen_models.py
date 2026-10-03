"""Generate entity models: Java model classes, animation ids, textures and preview sheets.

Every creature with a custom model lives in tools/wf/mobs/<name>.py and exposes ``build() -> Model``.
Outputs:
  src/main/java/com/wayfarers/generated/model/<Name>Model.java   (client: mesh + animations)
  src/main/java/com/wayfarers/generated/model/ModelRegistry.java (client: layer + renderer registration)
  src/main/java/com/wayfarers/generated/MobAnims.java            (common: action indices and lengths)
  src/main/resources/assets/wayfarers/textures/entity/<name>.png (+ <name>_glow.png)
  build/previews/models/<name>.png and <name>_tex.png             (with --preview)

Usage: python3 tools/gen_models.py [--preview] [--only name]
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from wf import mobs  # noqa: E402

ROOT = os.path.dirname(HERE)
JAVA = os.path.join(ROOT, "src/main/java/com/wayfarers/generated")
TEX = os.path.join(ROOT, "src/main/resources/assets/wayfarers/textures/entity")
PREVIEW = os.path.join(ROOT, "build/previews/models")
MAX_ACTIONS = 16


def camel(name):
    return "".join(p.capitalize() for p in name.split("_"))


def f(v):
    v = float(v)
    if v == int(v) and abs(v) < 1e7:
        return f"{int(v)}.0F"
    return f"{v:.6g}F"


def java_anim(field, a):
    target = {"rotation": "ROTATION", "position": "POSITION", "scale": "SCALE"}
    vec = {"rotation": "degreeVec", "position": "posVec", "scale": "scaleVec"}
    out = [f"    public static final AnimationDefinition {field} = AnimationDefinition.Builder.withLength({f(a.length)})"
           + (".looping()" if a.loop else "")]
    for part, tgt, frames in a.channels:
        keys = []
        for t, (x, y, z), interp in frames:
            comps = ", ".join(f"{c}" if tgt == "scale" else f(c) for c in (x, y, z))
            ip = "LINEAR" if interp == "linear" else "CATMULLROM"
            keys.append(f"                    new Keyframe({f(t)}, KeyframeAnimations.{vec[tgt]}({comps}), "
                        f"AnimationChannel.Interpolations.{ip})")
        out.append(f'            .addAnimation("{part}", new AnimationChannel(AnimationChannel.Targets.{target[tgt]},\n'
                   + ",\n".join(keys) + "))")
    out.append("            .build();")
    return "\n".join(out)


def java_model(m):
    cls = camel(m.name) + "Model"
    tw, th = m.tex_size
    body = []

    def emit(p, parent_var):
        var = "p_" + p.name
        cubes = "CubeListBuilder.create()"
        for c in p.cubes:
            x, y, z = c.origin
            w, h, d = c.size
            grow = f", new CubeDeformation({f(c.grow)})" if c.grow else ""
            cubes += f"\n                .texOffs({c.uv[0]}, {c.uv[1]}).addBox({f(x)}, {f(y)}, {f(z)}, {f(w)}, {f(h)}, {f(d)}{grow})"
        rx, ry, rz = (math.radians(r) for r in p.rot)
        pose = (f"new PartPose({f(p.pivot[0])}, {f(p.pivot[1])}, {f(p.pivot[2])}, {f(rx)}, {f(ry)}, {f(rz)}, "
                f"{f(p.scale[0])}, {f(p.scale[1])}, {f(p.scale[2])})")
        body.append(f'        PartDefinition {var} = {parent_var}.addOrReplaceChild("{p.name}", {cubes},\n                {pose});')
        for ch in p.children:
            emit(ch, var)
    for r in m.roots:
        emit(r, "root")

    anims = []
    if "idle" in m.anims:
        anims.append(java_anim("IDLE", m.anims["idle"]))
    if "walk" in m.anims:
        anims.append(java_anim("WALK", m.anims["walk"]))
    for a in m.actions:
        anims.append(java_anim(a.name.upper(), a))
    actions = ", ".join(a.name.upper() for a in m.actions)
    has_head = m.head and m.head in m.parts
    fields = []
    ctor = []
    setup = []
    if has_head:
        fields.append("    private final ModelPart head;")
        ctor.append(f'        this.head = root.createPartLookup().apply("{m.head}");')
        setup.append("        head.yRot += state.yRot * DEG;\n        head.xRot += state.xRot * DEG;")
    if "idle" in m.anims:
        fields.append("    private final KeyframeAnimation idle;")
        ctor.append("        this.idle = IDLE.bake(root);")
        setup.append("        idle.apply((long) (state.ageInTicks * 50.0F), 1.0F);")
    if "walk" in m.anims:
        fields.append("    private final KeyframeAnimation walk;")
        ctor.append("        this.walk = WALK.bake(root);")
        setup.append(f"        walk.applyWalk(state.walkAnimationPos, state.walkAnimationSpeed, {f(m.walk_speed)}, {f(m.walk_scale)});")
    fields.append("    private final KeyframeAnimation[] actions;")
    ctor.append("        this.actions = new KeyframeAnimation[ACTIONS.length];\n"
                "        for (int i = 0; i < ACTIONS.length; i++) {\n"
                "            this.actions[i] = ACTIONS[i].bake(root);\n"
                "        }")
    setup.append("        for (int i = 0; i < actions.length; i++) {\n"
                 "            actions[i].apply(state.actions[i], state.ageInTicks);\n"
                 "        }")
    return f"""package com.wayfarers.generated.model;

import com.wayfarers.Wayfarers;
import com.wayfarers.client.WayfarerRenderState;
import net.minecraft.client.animation.AnimationChannel;
import net.minecraft.client.animation.AnimationDefinition;
import net.minecraft.client.animation.Keyframe;
import net.minecraft.client.animation.KeyframeAnimation;
import net.minecraft.client.animation.KeyframeAnimations;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeDeformation;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.client.renderer.rendertype.RenderTypes;

/** Generated by tools/gen_models.py from tools/wf/mobs/{m.name}.py. Do not edit by hand. */
@SuppressWarnings("unused")
public final class {cls} extends EntityModel<WayfarerRenderState> {{
    public static final ModelLayerLocation LAYER = new ModelLayerLocation(Wayfarers.id("{m.name}"), "main");
    private static final float DEG = (float) (Math.PI / 180.0);

{chr(10).join(anims)}

    /** Actions in the order of MobAnims.{camel(m.name)}. */
    public static final AnimationDefinition[] ACTIONS = {{{actions}}};

{chr(10).join(fields)}

    public {cls}(ModelPart root) {{
        super(root, RenderTypes::entityCutout);
{chr(10).join(ctor)}
    }}

    public static LayerDefinition createBodyLayer() {{
        MeshDefinition mesh = new MeshDefinition();
        PartDefinition root = mesh.getRoot();
{chr(10).join(body)}
        return LayerDefinition.create(mesh, {tw}, {th});
    }}

    @Override
    public void setupAnim(WayfarerRenderState state) {{
        super.setupAnim(state);
{chr(10).join(setup)}
    }}
}}
"""


def java_registry(models):
    layers = "\n".join(f"        event.registerLayerDefinition({camel(m.name)}Model.LAYER, {camel(m.name)}Model::createBodyLayer);"
                       for m in models)
    rends = "\n".join(
        f"        event.registerEntityRenderer(ModEntities.{m.name.upper()}.get(), ctx -> new WayfarerModelRenderer<>(ctx,\n"
        f"                new {camel(m.name)}Model(ctx.bakeLayer({camel(m.name)}Model.LAYER)), {f(m.shadow)}, \"{m.name}\", "
        f"{'true' if m._has_glow else 'false'}));"
        for m in models)
    names = ", ".join(f'"{m.name}"' for m in models)
    return f"""package com.wayfarers.generated.model;

import com.wayfarers.client.WayfarerModelRenderer;
import com.wayfarers.registry.ModEntities;
import net.minecraftforge.client.event.EntityRenderersEvent;

import java.util.Set;

/** Generated by tools/gen_models.py: model layers and renderers of every custom-model creature. */
public final class ModelRegistry {{
    /** Creatures drawn with a generated model (the others keep the humanoid renderer). */
    public static final Set<String> NAMES = Set.of({names});

    private ModelRegistry() {{}}

    public static void registerLayers(EntityRenderersEvent.RegisterLayerDefinitions event) {{
{layers}
    }}

    public static void registerRenderers(EntityRenderersEvent.RegisterRenderers event) {{
{rends}
    }}
}}
"""


def java_anims(models):
    blocks = []
    for m in models:
        consts = "\n".join(f"        public static final int {a.name.upper()} = {i};" for i, a in enumerate(m.actions))
        ticks = ", ".join(str(max(1, round(a.length * 20))) for a in m.actions)
        blocks.append(f"""    public static final class {camel(m.name)} {{
{consts}
        public static final int COUNT = {len(m.actions)};
        /** Length of each action in ticks. */
        public static final int[] TICKS = {{{ticks}}};

        private {camel(m.name)}() {{}}
    }}""")
    return f"""package com.wayfarers.generated;

/** Generated by tools/gen_models.py: action animation indices (entity event 100 + index) and lengths. */
public final class MobAnims {{
    public static final int MAX_ACTIONS = {MAX_ACTIONS};

    private MobAnims() {{}}

{chr(10).join(blocks)}
}}
"""


def check(m):
    for a in m.anims.values():
        for part, _, frames in a.channels:
            if part not in m.parts:
                raise ValueError(f"{m.name}: animation '{a.name}' animates unknown part '{part}'")
            if frames[-1][0] > a.length + 1e-6:
                raise ValueError(f"{m.name}: animation '{a.name}' has a keyframe after its length")
    if len(m.actions) > MAX_ACTIONS:
        raise ValueError(f"{m.name}: at most {MAX_ACTIONS} actions")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--only")
    args = ap.parse_args()
    built = []
    for builder in mobs.MODELS:
        m = builder()
        check(m)
        m.pack()
        tex, glow = m.textures()
        m._has_glow = glow is not None
        built.append(m)
        if args.only and m.name != args.only:
            continue
        os.makedirs(TEX, exist_ok=True)
        tex.save(os.path.join(TEX, f"{m.name}.png"))
        glow_path = os.path.join(TEX, f"{m.name}_glow.png")
        if glow is not None:
            glow.save(glow_path)
        elif os.path.exists(glow_path):
            os.remove(glow_path)
        os.makedirs(os.path.join(JAVA, "model"), exist_ok=True)
        with open(os.path.join(JAVA, "model", f"{camel(m.name)}Model.java"), "w") as fh:
            fh.write(java_model(m))
        if args.preview:
            from wf import model_render
            os.makedirs(PREVIEW, exist_ok=True)
            model_render.sheet(m, tex, glow, os.path.join(PREVIEW, f"{m.name}.png"))
            model_render.texture_preview(m, tex, glow, os.path.join(PREVIEW, f"{m.name}_tex.png"))
        n_cubes = len(m.all_cubes())
        print(f"{m.name:22s} {n_cubes:4d} cubes  tex {m.tex_size[0]}x{m.tex_size[1]}  "
              f"anims: {', '.join(m.anims)}")
    with open(os.path.join(JAVA, "model", "ModelRegistry.java"), "w") as fh:
        fh.write(java_registry(built))
    with open(os.path.join(JAVA, "MobAnims.java"), "w") as fh:
        fh.write(java_anims(built))
    print(f"{len(built)} models")


if __name__ == "__main__":
    main()
