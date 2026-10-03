package com.wayfarers.block;

import com.wayfarers.boss.WayfarerBoss;
import com.wayfarers.registry.ModBlockEntities;
import com.wayfarers.registry.ModBlocks;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/**
 * Boss seal: placed in the centre of an arena by the structure template, with NBT
 * {@code {boss: "wayfarers:<id>", radius: <blocks>}}.
 * <ol>
 *     <li>Ready: the first player who walks into the arena wakes the boss (health scaled to the group).</li>
 *     <li>Fight: the mist gates around the arena turn solid while players are inside, and reopen if the boss
 *     resets (everyone left or died).</li>
 *     <li>Defeated: the mist disappears for good and the seal goes quiet.</li>
 * </ol>
 */
public class BossSealBlockEntity extends BlockEntity {
    private static final int READY = 0;
    private static final int FIGHT = 1;
    private static final int DEFEATED = 2;

    private String boss = "";
    private int radius = 18;
    private int state = READY;
    private boolean sealed;
    private String bossId = "";
    private int missingChecks;
    private final List<BlockPos> gates = new ArrayList<>();
    private boolean scanned;

    public BossSealBlockEntity(BlockPos pos, BlockState blockState) {
        super(ModBlockEntities.BOSS_SEAL.get(), pos, blockState);
    }

    public void serverTick() {
        if (!(level instanceof ServerLevel server) || server.getGameTime() % 10 != 0 || state == DEFEATED) {
            return;
        }
        List<Player> inside = server.getEntitiesOfClass(Player.class, arena(radius * 0.8),
                p -> p.isAlive() && !p.isSpectator() && !p.isCreative());
        if (state == READY) {
            if (!inside.isEmpty()) {
                wake(server, inside);
            }
            return;
        }
        Entity entity = bossId.isEmpty() ? null : server.getEntity(UUID.fromString(bossId));
        if (entity == null) {
            if (++missingChecks > 120) { // the boss vanished (removed by a command...): start over
                state = READY;
                bossId = "";
                setGates(server, false);
                setChanged();
            }
            return;
        }
        missingChecks = 0;
        if (!inside.isEmpty()) {
            setGates(server, true); // also closes gates that a player was standing in last time
        }
    }

    private AABB arena(double r) {
        return new AABB(worldPosition).inflate(r, 10, r);
    }

    private void wake(ServerLevel server, List<Player> players) {
        var type = BuiltInRegistries.ENTITY_TYPE.getOptional(Identifier.tryParse(boss));
        if (type.isEmpty()) {
            return;
        }
        Entity entity = type.get().create(server, EntitySpawnReason.TRIGGERED);
        if (!(entity instanceof WayfarerBoss wb)) {
            if (entity != null) {
                entity.discard();
            }
            return;
        }
        Player first = players.get(0);
        double dx = first.getX() - (worldPosition.getX() + 0.5);
        double dz = first.getZ() - (worldPosition.getZ() + 0.5);
        float yaw = (float) (Math.atan2(dz, dx) * (180.0 / Math.PI)) - 90.0F;
        wb.snapTo(worldPosition.getX() + 0.5, worldPosition.getY() + 1, worldPosition.getZ() + 0.5, yaw, 0.0F);
        wb.setArena(worldPosition.above(), radius, worldPosition);
        wb.scaleForPlayers(players.size());
        wb.setTarget(first);
        server.addFreshEntity(wb);
        server.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, wb.getX(), wb.getY() + 1, wb.getZ(), 80, 1.0, 1.5, 1.0, 0.05);
        server.playSound(null, worldPosition, SoundEvents.WITHER_SPAWN, SoundSource.HOSTILE, 1.5F, 0.7F);
        bossId = wb.getUUID().toString();
        state = FIGHT;
        setGates(server, true);
        setChanged();
    }

    /** Called by the boss when the fight resets (nobody left in the arena). */
    public void onBossReset(WayfarerBoss boss) {
        if (level instanceof ServerLevel server) {
            setGates(server, false);
        }
    }

    /** Called by the boss when it dies: the mist fades for good. */
    public void onBossDefeated(WayfarerBoss boss) {
        if (level instanceof ServerLevel server) {
            scanGates(server);
            for (BlockPos p : gates) {
                if (server.getBlockState(p).is(ModBlocks.MIST_GATE.get())) {
                    server.setBlock(p, Blocks.AIR.defaultBlockState(), 3);
                    server.sendParticles(ParticleTypes.WHITE_ASH, p.getX() + 0.5, p.getY() + 0.5, p.getZ() + 0.5, 6, 0.3, 0.3, 0.3, 0.02);
                }
            }
            state = DEFEATED;
            sealed = false;
            setChanged();
        }
    }

    private void scanGates(ServerLevel server) {
        if (scanned) {
            return;
        }
        scanned = true;
        gates.clear();
        int r = radius + 8;
        for (BlockPos p : BlockPos.betweenClosed(worldPosition.offset(-r, -4, -r), worldPosition.offset(r, 14, r))) {
            if (server.getBlockState(p).is(ModBlocks.MIST_GATE.get())) {
                gates.add(p.immutable());
            }
        }
    }

    private void setGates(ServerLevel server, boolean solid) {
        scanGates(server);
        for (BlockPos p : gates) {
            BlockState st = server.getBlockState(p);
            if (!st.is(ModBlocks.MIST_GATE.get()) || st.getValue(MistGateBlock.SEALED) == solid) {
                continue;
            }
            if (solid && !server.getEntitiesOfClass(Player.class, new AABB(p)).isEmpty()) {
                continue; // never close the mist on someone standing in it
            }
            server.setBlock(p, st.setValue(MistGateBlock.SEALED, solid), 3);
        }
        if (solid != sealed && !gates.isEmpty()) {
            server.playSound(null, worldPosition, solid ? SoundEvents.BEACON_ACTIVATE : SoundEvents.BEACON_DEACTIVATE,
                    SoundSource.BLOCKS, 2.0F, 0.6F);
        }
        sealed = solid;
        setChanged();
    }

    @Override
    protected void saveAdditional(ValueOutput output) {
        super.saveAdditional(output);
        output.putString("boss", boss);
        output.putInt("radius", radius);
        output.putInt("state", state);
        output.putBoolean("sealed", sealed);
        output.putString("boss_uuid", bossId);
    }

    @Override
    protected void loadAdditional(ValueInput input) {
        super.loadAdditional(input);
        boss = input.getStringOr("boss", "");
        radius = input.getIntOr("radius", 18);
        state = input.getIntOr("state", READY);
        sealed = input.getBooleanOr("sealed", false);
        bossId = input.getStringOr("boss_uuid", "");
    }

    public String bossType() {
        return boss;
    }

    public void setBoss(EntityType<?> type, int radius) {
        this.boss = BuiltInRegistries.ENTITY_TYPE.getKey(type).toString();
        this.radius = radius;
        setChanged();
    }
}
