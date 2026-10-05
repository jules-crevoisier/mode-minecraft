package com.brasshaven.entity.folk;

import com.brasshaven.entity.AnimatedMob;
import com.brasshaven.generated.GeneratedFolk;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AnimationState;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MoveTowardsRestrictionGoal;
import net.minecraft.world.entity.ai.goal.PanicGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.ai.util.DefaultRandomPos;
import net.minecraft.world.entity.monster.Creeper;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.npc.Npc;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.arrow.AbstractArrow;
import net.minecraft.world.entity.projectile.arrow.Arrow;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.SpawnEggItem;
import net.minecraft.world.item.alchemy.PotionContents;
import net.minecraft.world.item.trading.ItemCost;
import net.minecraft.world.item.trading.Merchant;
import net.minecraft.world.item.trading.MerchantOffer;
import net.minecraft.world.item.trading.MerchantOffers;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import java.util.function.Predicate;

/**
 * A resident of one of the great places (Dwarf, Sylvan, Clockwork Citizen, Monk): one entity type per people, a role
 * per texture variant ({@link GeneratedFolk}, from tools/wf/denizens.py).
 * <ul>
 *     <li><b>Traders and workers</b> open the vanilla trading screen ({@link Merchant} + the vanilla merchant menu) with
 *     their role's themed offers, which restock every half day. Workers walk between the job blocks around their home
 *     (anvils, ores, composters, lecterns...) and work there; traders keep to their stall.</li>
 *     <li><b>Guards</b> attack monsters near their home and whoever hurts a resident (the Sylvan Warden with a bow),
 *     and answer a few words instead of trading.</li>
 *     <li>Everybody stays within the home radius, never despawns, flees monsters and panics when hurt (guards excepted),
 *     heals slowly, and refuses to trade for three minutes with a player who hurt one of them.</li>
 * </ul>
 * The AI is light: the job blocks are scanned once a minute at most, fear checks run every 10 ticks, paths are
 * recomputed every 10 ticks only while fighting.
 */
public abstract class Resident extends PathfinderMob implements AnimatedMob, Merchant, Npc {
    private static final EntityDataAccessor<Integer> DATA_ROLE = SynchedEntityData.defineId(Resident.class, EntityDataSerializers.INT);
    private static final long GRUDGE_TICKS = 3600L;
    private static final long RESTOCK_TICKS = 12000L;
    private static final Map<String, Predicate<Identifier>> JOB_MATCHERS = new HashMap<>();

    private final AnimationState[] actionStates = AnimatedMob.createStates();
    private @Nullable Player tradingPlayer;
    private @Nullable MerchantOffers offers;
    private long lastRestock = -1;
    private final Map<UUID, Long> grudges = new HashMap<>();
    private final List<BlockPos> jobSpots = new ArrayList<>();
    private int jobScanCooldown;
    private int talkCooldown;
    private int attackCooldown;
    private boolean landed;
    private boolean statsApplied;
    /** The action being played on the server (-1: none) and its timer, for the attack's impact tick. */
    int action = -1;
    int actionTimer;

    protected Resident(EntityType<? extends PathfinderMob> type, Level level) {
        super(type, level);
        setPersistenceRequired();
    }

    /** Base attributes of a people (the guard role raises health, damage and armour, {@link #guardStats}). */
    protected static AttributeSupplier.Builder residentAttributes(double speed) {
        return Mob.createMobAttributes()
                .add(Attributes.MOVEMENT_SPEED, speed)
                .add(Attributes.FOLLOW_RANGE, 24.0)
                .add(Attributes.ATTACK_DAMAGE, 2.0)
                .add(Attributes.ARMOR, 0.0);
    }

    // ------------------------------------------------------------------ what each people says and does

    public abstract GeneratedFolk.People people();

    /** {health, damage, armour} of the guard role. */
    protected abstract double[] guardStats();

    /** Tick of the attack animation where the blow lands (or the arrow is loosed). */
    protected abstract int attackImpact();

    protected abstract SoundEvent voice();

    /** True when the guard shoots arrows instead of fighting up close. */
    protected boolean archer() {
        return false;
    }

    /** Extra knock-back of the guard's blow. */
    protected double knockback() {
        return 0.4;
    }

    public GeneratedFolk.Role role() {
        return people().role(entityData.get(DATA_ROLE));
    }

    public boolean isGuard() {
        return role().kind() == GeneratedFolk.Kind.GUARD;
    }

    public void setRole(String id) {
        int i = people().indexOf(id);
        entityData.set(DATA_ROLE, Math.max(0, i));
        statsApplied = false;
        offers = null;
        jobSpots.clear();
    }

    @Override
    public int modelVariant() {
        return Math.floorMod(entityData.get(DATA_ROLE), people().roles().size());
    }

    @Override
    protected Component getTypeName() {
        return Component.translatable("entity.brasshaven." + people().id() + "." + role().id());
    }

    private int homeRadius() {
        return switch (role().kind()) {
            case GUARD -> 14;
            case WORKER -> 10;
            case TRADER -> 6;
        };
    }

    private void applyStats() {
        statsApplied = true;
        if (!isGuard()) {
            return;
        }
        double[] s = guardStats();
        setBase(Attributes.MAX_HEALTH, s[0]);
        setBase(Attributes.ATTACK_DAMAGE, s[1]);
        setBase(Attributes.ARMOR, s[2]);
        setHealth(getMaxHealth());
    }

    private void setBase(net.minecraft.core.Holder<net.minecraft.world.entity.ai.attributes.Attribute> attr, double v) {
        AttributeInstance inst = getAttribute(attr);
        if (inst != null) {
            inst.setBaseValue(v);
        }
    }

    // ------------------------------------------------------------------ goals

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(1, new GuardFightGoal(this));
        goalSelector.addGoal(1, new FleeMonstersGoal(this));
        goalSelector.addGoal(2, new PanicGoal(this, 1.3) {
            @Override
            public boolean canUse() {
                return !isGuard() && super.canUse();
            }
        });
        goalSelector.addGoal(3, new TradeGoal(this));
        goalSelector.addGoal(4, new MoveTowardsRestrictionGoal(this, 0.7));
        goalSelector.addGoal(5, new WorkGoal(this));
        goalSelector.addGoal(6, new WaterAvoidingRandomStrollGoal(this, 0.55) {
            @Override
            public boolean canUse() {
                return !isTrading() && super.canUse();
            }
        });
        goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 8.0F));
        goalSelector.addGoal(8, new RandomLookAroundGoal(this));
        targetSelector.addGoal(1, new HurtByTargetGoal(this, Resident.class) {
            @Override
            public boolean canUse() {
                return isGuard() && super.canUse();
            }
        });
        targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Mob.class, 10, true, false,
                (target, level) -> isGuard() && target instanceof Enemy && !(target instanceof Creeper)
                        && target.blockPosition().closerThan(getHomePosition(), homeRadius() + 8)));
    }

    // ------------------------------------------------------------------ data, home, persistence

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(DATA_ROLE, 0);
    }

    @Override
    public @Nullable SpawnGroupData finalizeSpawn(ServerLevelAccessor level, DifficultyInstance difficulty,
                                                  EntitySpawnReason reason, @Nullable SpawnGroupData groupData) {
        SpawnGroupData data = super.finalizeSpawn(level, difficulty, reason, groupData);
        if (reason == EntitySpawnReason.SPAWN_ITEM_USE || reason == EntitySpawnReason.SPAWNER
                || reason == EntitySpawnReason.COMMAND) {
            // an egg (or a /summon without NBT) gives a random role, so every look of the people can be met in creative;
            // templates and /summon with {Role:"..."} keep theirs (finalizeSpawn is not called for NBT summons)
            entityData.set(DATA_ROLE, random.nextInt(people().roles().size()));
        }
        setHomeTo(blockPosition(), homeRadius());
        return data;
    }

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        output.putString("Role", role().id());
        if (offers != null) {
            output.store("Offers", MerchantOffers.CODEC, offers);
        }
        output.putLong("LastRestock", lastRestock);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        int i = people().indexOf(input.getStringOr("Role", people().role(0).id()));
        entityData.set(DATA_ROLE, Math.max(0, i));
        offers = input.read("Offers", MerchantOffers.CODEC).orElse(null);
        lastRestock = input.getLongOr("LastRestock", -1L);
        statsApplied = false;
    }

    @Override
    public boolean removeWhenFarAway(double distSqr) {
        return false;
    }

    @Override
    public boolean requiresCustomPersistence() {
        return true;
    }

    @Override
    public boolean canBeLeashed() {
        return false;
    }

    // ------------------------------------------------------------------ talking and trading

    @Override
    protected InteractionResult mobInteract(Player player, InteractionHand hand) {
        ItemStack held = player.getItemInHand(hand);
        if (held.getItem() instanceof SpawnEggItem || held.is(Items.NAME_TAG) || !isAlive() || getTarget() == player) {
            return super.mobInteract(player, hand);
        }
        if (!(player instanceof ServerPlayer sp) || hand != InteractionHand.MAIN_HAND) {
            return InteractionResult.SUCCESS;
        }
        getLookControl().setLookAt(player);
        if (isGuard()) {
            if (talkCooldown <= 0) {
                talkCooldown = 40;
                AnimatedMob.playAction(this, people().greetAction());
                playSound(voice(), 1.0F, getVoicePitch());
                sp.sendSystemMessage(Component.translatable("folk.brasshaven.says", getDisplayName(),
                        Component.translatable("folk.brasshaven." + people().id() + ".line" + random.nextInt(Math.max(1, people().lines())))));
            }
            return InteractionResult.SUCCESS;
        }
        Long until = grudges.get(player.getUUID());
        if (until != null && level().getGameTime() < until) {
            playSound(SoundEvents.VILLAGER_NO, 1.0F, getVoicePitch());
            sp.sendOverlayMessage(Component.translatable("folk.brasshaven.refuse", getDisplayName()));
            return InteractionResult.SUCCESS;
        }
        if (isTrading() || getOffers().isEmpty()) {
            return InteractionResult.SUCCESS;
        }
        if (talkCooldown <= 0) {
            talkCooldown = 60;
            AnimatedMob.playAction(this, people().greetAction());
            playSound(voice(), 1.0F, getVoicePitch());
        }
        getNavigation().stop();
        setTradingPlayer(player);
        openTradingScreen(player, getDisplayName(), 1);
        return InteractionResult.SUCCESS;
    }

    public boolean isTrading() {
        return tradingPlayer != null;
    }

    @Override
    public void setTradingPlayer(@Nullable Player player) {
        tradingPlayer = player;
    }

    @Override
    public @Nullable Player getTradingPlayer() {
        return tradingPlayer;
    }

    @Override
    public MerchantOffers getOffers() {
        if (offers == null) {
            offers = new MerchantOffers();
            if (!level().isClientSide()) {
                for (GeneratedFolk.Trade t : role().trades()) {
                    MerchantOffer o = offer(t);
                    if (o != null) {
                        offers.add(o);
                    }
                }
            }
        }
        return offers;
    }

    private static @Nullable MerchantOffer offer(GeneratedFolk.Trade t) {
        Item a = item(t.costA());
        ItemStack result = stack(t.result(), t.countR());
        if (a == null || result.isEmpty()) {
            return null;
        }
        Optional<ItemCost> b = Optional.empty();
        if (!t.costB().isEmpty()) {
            Item bi = item(t.costB());
            if (bi == null) {
                return null;
            }
            b = Optional.of(new ItemCost(bi, t.countB()));
        }
        return new MerchantOffer(new ItemCost(a, t.countA()), b, result, t.maxUses(), t.xp(), 0.05F);
    }

    private static @Nullable Item item(String id) {
        Identifier rl = Identifier.tryParse(id);
        return rl == null ? null : BuiltInRegistries.ITEM.getOptional(rl).orElse(null);
    }

    private static ItemStack stack(String id, int count) {
        if (id.startsWith("potion:")) {
            Identifier rl = Identifier.tryParse(id.substring(7));
            if (rl == null) {
                return ItemStack.EMPTY;
            }
            return BuiltInRegistries.POTION.get(rl)
                    .map(potion -> PotionContents.createItemStack(Items.POTION, potion))
                    .orElse(ItemStack.EMPTY);
        }
        Item item = item(id);
        return item == null ? ItemStack.EMPTY : new ItemStack(item, count);
    }

    @Override
    public void overrideOffers(MerchantOffers newOffers) {
        // the server owns the offers (the vanilla client-side merchant overrides its own copy)
    }

    @Override
    public void notifyTrade(MerchantOffer offer) {
        offer.increaseUses();
        ambientSoundTime = -getAmbientSoundInterval();
        playSound(SoundEvents.VILLAGER_YES, 0.8F, getVoicePitch());
        if (level() instanceof ServerLevel sl) {
            sl.sendParticles(ParticleTypes.HAPPY_VILLAGER, getX(), getY() + getBbHeight() * 0.8, getZ(), 3, 0.3, 0.2, 0.3, 0.0);
        }
    }

    @Override
    public void notifyTradeUpdated(ItemStack stack) {
        if (!level().isClientSide() && ambientSoundTime > -getAmbientSoundInterval() + 20) {
            ambientSoundTime = -getAmbientSoundInterval();
            playSound(stack.isEmpty() ? SoundEvents.VILLAGER_NO : voice(), 0.6F, getVoicePitch());
        }
    }

    @Override
    public int getVillagerXp() {
        return 0;
    }

    @Override
    public void overrideXp(int xp) {
    }

    @Override
    public boolean showProgressBar() {
        return false;
    }

    @Override
    public SoundEvent getNotifyTradeSound() {
        return SoundEvents.VILLAGER_YES;
    }

    @Override
    public boolean isClientSide() {
        return level().isClientSide();
    }

    @Override
    public boolean stillValid(Player player) {
        return tradingPlayer == player && isAlive() && player.isWithinEntityInteractionRange(this, 4.0);
    }

    private void stopTrading() {
        if (tradingPlayer instanceof ServerPlayer sp && sp.containerMenu instanceof net.minecraft.world.inventory.MerchantMenu) {
            sp.closeContainer();
        }
        tradingPlayer = null;
    }

    // ------------------------------------------------------------------ getting hurt: panic, grudges, the guards rally

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float damage) {
        boolean hurt = super.hurtServer(level, source, damage);
        if (hurt && source.getEntity() instanceof LivingEntity attacker && !(attacker instanceof Resident)) {
            stopTrading();
            rally(level, attacker);
        }
        return hurt;
    }

    /** Every guard around turns on ``attacker``; a player is also refused trade for a while by everyone around. */
    private void rally(ServerLevel level, LivingEntity attacker) {
        if (attacker instanceof Player p && (p.isCreative() || p.isSpectator())) {
            return;
        }
        long until = level.getGameTime() + GRUDGE_TICKS;
        for (Resident r : level.getEntitiesOfClass(Resident.class, getBoundingBox().inflate(24.0), Entity::isAlive)) {
            if (attacker instanceof Player) {
                r.grudges.put(attacker.getUUID(), until);
            }
            if (r.isGuard() && (r.getTarget() == null || !r.getTarget().isAlive())) {
                r.setTarget(attacker);
            }
        }
    }

    @Override
    public void die(DamageSource source) {
        super.die(source);
        stopTrading();
    }

    @Override
    public boolean killedEntity(ServerLevel level, LivingEntity entity, DamageSource source) {
        playSound(voice(), 1.0F, getVoicePitch() * 1.2F);
        return super.killedEntity(level, entity, source);
    }

    // ------------------------------------------------------------------ the server tick

    @Override
    protected void customServerAiStep(ServerLevel level) {
        super.customServerAiStep(level);
        if (!statsApplied) {
            applyStats();
        }
        if (talkCooldown > 0) {
            talkCooldown--;
        }
        if (attackCooldown > 0) {
            attackCooldown--;
        }
        if (jobScanCooldown > 0) {
            jobScanCooldown--;
        }
        if (!hasHome()) {
            setHomeTo(blockPosition(), homeRadius());
        }
        if (!landed && onGround()) {
            landed = true;
            if (!getHomePosition().closerThan(blockPosition(), 4.0)) {
                setHomeTo(blockPosition(), homeRadius()); // summoned in the air: home is where it lands
            }
        }
        if (tradingPlayer != null && (!tradingPlayer.isAlive() || !(tradingPlayer.containerMenu
                instanceof net.minecraft.world.inventory.MerchantMenu))) {
            tradingPlayer = null;
        }
        if ((tickCount + getId()) % 80 == 0) {
            if (getHealth() < getMaxHealth() && tickCount - getLastHurtByMobTimestamp() > 200) {
                heal(1.0F);
            }
            long now = level.getGameTime();
            if (lastRestock < 0) {
                lastRestock = now;
            } else if (offers != null && tradingPlayer == null && now - lastRestock > RESTOCK_TICKS) {
                lastRestock = now;
                offers.forEach(MerchantOffer::resetUses);
            }
            grudges.values().removeIf(t -> t < now);
            if (getTarget() != null && isGuard()
                    && !getTarget().blockPosition().closerThan(getHomePosition(), homeRadius() + 14)) {
                setTarget(null); // it does not chase far from home
            }
        }
        if (action >= 0 && ++actionTimer >= actionTicks()[action]) {
            action = -1;
        }
    }

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide()) {
            tickActionStates(this);
        }
    }

    void play(int anim) {
        action = anim;
        actionTimer = 0;
        AnimatedMob.playAction(this, anim);
    }

    // ------------------------------------------------------------------ job blocks

    private static Predicate<Identifier> matcher(GeneratedFolk.Role role) {
        return JOB_MATCHERS.computeIfAbsent(role.id() + "@" + role.jobs(), k -> {
            List<Predicate<Identifier>> parts = new ArrayList<>();
            for (String j : role.jobs()) {
                if (!j.contains("*")) {
                    Identifier exact = Identifier.tryParse(j);
                    if (exact != null) {
                        parts.add(exact::equals);
                    }
                    continue;
                }
                String ns = j.contains(":") ? j.substring(0, j.indexOf(':')) : null;
                String path = j.contains(":") ? j.substring(j.indexOf(':') + 1) : j;
                String pre = path.substring(0, path.indexOf('*'));
                String post = path.substring(path.indexOf('*') + 1);
                parts.add(id -> (ns == null || ns.equals(id.getNamespace())) && id.getPath().startsWith(pre)
                        && id.getPath().endsWith(post));
            }
            return id -> {
                for (Predicate<Identifier> p : parts) {
                    if (p.test(id)) {
                        return true;
                    }
                }
                return false;
            };
        });
    }

    /** Job blocks within the home (at most 8, the nearest first); scanned at most once a minute. */
    List<BlockPos> jobSpots() {
        if (jobSpots.isEmpty() && jobScanCooldown <= 0 && !role().jobs().isEmpty()) {
            jobScanCooldown = 1200 + random.nextInt(200);
            Predicate<Identifier> match = matcher(role());
            BlockPos home = hasHome() ? getHomePosition() : blockPosition();
            int r = Math.min(homeRadius(), 9);
            List<BlockPos> found = new ArrayList<>();
            for (BlockPos p : BlockPos.betweenClosed(home.offset(-r, -3, -r), home.offset(r, 3, r))) {
                BlockState s = level().getBlockState(p);
                if (!s.isAir() && match.test(BuiltInRegistries.BLOCK.getKey(s.getBlock()))) {
                    found.add(p.immutable());
                }
            }
            found.sort((a, b) -> Double.compare(a.distSqr(home), b.distSqr(home)));
            jobSpots.addAll(found.subList(0, Math.min(8, found.size())));
        }
        return jobSpots;
    }

    /** Sounds and particles of the work animation, on the job block. */
    void workEffect(ServerLevel level, BlockPos at) {
        String style = role().style();
        Vec3 c = Vec3.atCenterOf(at).add(0, 0.5, 0);
        SoundEvent sound;
        ParticleOptions particle;
        float pitch = 1.0F;
        switch (style) {
            case "hammer" -> {
                sound = SoundEvents.ANVIL_USE;
                particle = ParticleTypes.ELECTRIC_SPARK;
                pitch = 1.3F;
            }
            case "dig" -> {
                sound = SoundEvents.STONE_HIT;
                particle = new BlockParticleOption(ParticleTypes.BLOCK, level.getBlockState(at));
            }
            case "brew" -> {
                sound = SoundEvents.BREWING_STAND_BREW;
                particle = ParticleTypes.BUBBLE_POP;
            }
            case "carve" -> {
                sound = SoundEvents.WOOD_HIT;
                particle = new BlockParticleOption(ParticleTypes.BLOCK, level.getBlockState(at));
            }
            case "tend" -> {
                sound = SoundEvents.COMPOSTER_FILL;
                particle = ParticleTypes.HAPPY_VILLAGER;
            }
            case "tinker" -> {
                sound = SoundEvents.SMITHING_TABLE_USE;
                particle = ParticleTypes.ELECTRIC_SPARK;
                pitch = 1.5F;
            }
            case "wind" -> {
                sound = SoundEvents.CROSSBOW_LOADING_MIDDLE.value();
                particle = ParticleTypes.WAX_ON;
            }
            default -> {
                sound = SoundEvents.BOOK_PAGE_TURN;
                particle = ParticleTypes.ENCHANT;
            }
        }
        level.playSound(null, at, sound, SoundSource.NEUTRAL, 0.35F, pitch + random.nextFloat() * 0.2F);
        if (particle instanceof BlockParticleOption bpo && bpo.getState().isAir()) {
            return;
        }
        level.sendParticles(particle, c.x, c.y, c.z, 4, 0.25, 0.15, 0.25, 0.02);
    }

    // ------------------------------------------------------------------ sounds

    @Override
    protected @Nullable SoundEvent getAmbientSound() {
        return isTrading() ? null : voice();
    }

    @Override
    public int getAmbientSoundInterval() {
        return 300;
    }

    @Override
    protected @Nullable SoundEvent getHurtSound(DamageSource source) {
        return SoundEvents.VILLAGER_HURT;
    }

    @Override
    protected @Nullable SoundEvent getDeathSound() {
        return SoundEvents.VILLAGER_DEATH;
    }

    // ------------------------------------------------------------------ animation plumbing

    @Override
    public AnimationState[] actionStates() {
        return actionStates;
    }

    @Override
    public void handleEntityEvent(byte id) {
        if (!handleActionEvent(this, id)) {
            super.handleEntityEvent(id);
        }
    }

    // ================================================================== goals

    /** Stand still and look at the trading player. */
    static final class TradeGoal extends Goal {
        private final Resident r;

        TradeGoal(Resident r) {
            this.r = r;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
        }

        @Override
        public boolean canUse() {
            return r.tradingPlayer != null && r.isAlive() && !r.isInWater();
        }

        @Override
        public void start() {
            r.getNavigation().stop();
        }

        @Override
        public void tick() {
            if (r.tradingPlayer != null) {
                r.getLookControl().setLookAt(r.tradingPlayer, 30.0F, 30.0F);
            }
        }
    }

    /** Non-guards: run from a monster within 8 blocks (checked every 10 ticks). */
    static final class FleeMonstersGoal extends Goal {
        private final Resident r;
        private @Nullable Mob threat;
        private int timer;

        FleeMonstersGoal(Resident r) {
            this.r = r;
            setFlags(EnumSet.of(Flag.MOVE));
        }

        @Override
        public boolean canUse() {
            if (r.isGuard() || (r.tickCount + r.getId()) % 10 != 0) {
                return false;
            }
            AABB box = r.getBoundingBox().inflate(8.0, 3.0, 8.0);
            threat = null;
            for (Mob m : r.level().getEntitiesOfClass(Mob.class, box, e -> e instanceof Enemy && e.isAlive())) {
                if (threat == null || m.distanceToSqr(r) < threat.distanceToSqr(r)) {
                    threat = m;
                }
            }
            return threat != null;
        }

        @Override
        public void start() {
            timer = 60;
            run();
        }

        private void run() {
            if (threat == null) {
                return;
            }
            Vec3 away = DefaultRandomPos.getPosAway(r, 10, 4, threat.position());
            if (away != null) {
                r.getNavigation().moveTo(away.x, away.y, away.z, 1.25);
            }
        }

        @Override
        public boolean canContinueToUse() {
            return timer > 0 && threat != null && threat.isAlive() && threat.distanceToSqr(r) < 144.0;
        }

        @Override
        public void tick() {
            if (--timer % 20 == 0 && r.getNavigation().isDone()) {
                run();
            }
        }

        @Override
        public void stop() {
            threat = null;
        }
    }

    /** Workers and traders: walk to a job block now and then and work there for a while. */
    static final class WorkGoal extends Goal {
        private final Resident r;
        private @Nullable BlockPos spot;
        private int timer;
        private int nextSwing;
        private int stuck;
        private int rest = 100;

        WorkGoal(Resident r) {
            this.r = r;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            if (r.isGuard() || r.isTrading() || r.getTarget() != null) {
                return false;
            }
            if (rest > 0) {
                rest -= 2; // goals are polled every other tick
                return false;
            }
            rest = 120 + r.random.nextInt(160);
            List<BlockPos> spots = r.jobSpots();
            if (spots.isEmpty()) {
                return false;
            }
            spot = spots.get(r.random.nextInt(spots.size()));
            return true;
        }

        @Override
        public void start() {
            timer = 160 + r.random.nextInt(140);
            nextSwing = 0;
            stuck = 0;
            if (spot != null) {
                r.getNavigation().moveTo(spot.getX() + 0.5, spot.getY(), spot.getZ() + 0.5, 0.6);
            }
        }

        @Override
        public boolean canContinueToUse() {
            return spot != null && timer > 0 && !r.isTrading() && r.getTarget() == null && r.getLastHurtByMob() == null;
        }

        @Override
        public void tick() {
            timer -= 2;
            if (spot == null || !(r.level() instanceof ServerLevel level)) {
                return;
            }
            double d = r.position().distanceToSqr(Vec3.atBottomCenterOf(spot).add(0, r.getY() - spot.getY(), 0));
            if (d > 2.6 * 2.6) {
                if (r.getNavigation().isDone() && ++stuck > 15) {
                    timer = 0; // cannot reach it: forget it until the next scan
                    r.jobSpots.remove(spot);
                }
                return;
            }
            r.getNavigation().stop();
            r.getLookControl().setLookAt(spot.getX() + 0.5, spot.getY() + 0.5, spot.getZ() + 0.5);
            if (--nextSwing <= 0) {
                int work = r.role().workAction();
                r.play(work);
                nextSwing = r.actionTicks()[work] / 2 + 10 + r.random.nextInt(20);
                r.workEffect(level, spot);
            }
        }

        @Override
        public void stop() {
            spot = null;
            r.getNavigation().stop();
        }
    }

    /** Guards: chase and strike (or shoot) the target, never far from home. */
    static final class GuardFightGoal extends Goal {
        private final Resident r;
        private int repath;

        GuardFightGoal(Resident r) {
            this.r = r;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
        }

        @Override
        public boolean canUse() {
            LivingEntity t = r.getTarget();
            return r.isGuard() && t != null && t.isAlive();
        }

        @Override
        public boolean canContinueToUse() {
            return canUse() || r.action == r.people().attackAction();
        }

        @Override
        public boolean requiresUpdateEveryTick() {
            return true;
        }

        @Override
        public void stop() {
            r.getNavigation().stop();
        }

        @Override
        public void tick() {
            LivingEntity t = r.getTarget();
            if (!(r.level() instanceof ServerLevel level)) {
                return;
            }
            int attack = r.people().attackAction();
            if (r.action == attack) {
                r.getNavigation().stop();
                if (t != null) {
                    r.getLookControl().setLookAt(t, 30.0F, 30.0F);
                }
                if (r.actionTimer == r.attackImpact() && t != null && t.isAlive()) {
                    if (r.archer()) {
                        shoot(level, t);
                    } else if (r.distanceToSqr(t) <= reach(t) * reach(t) + 1.0) {
                        if (r.doHurtTarget(level, t)) {
                            Vec3 push = t.position().subtract(r.position()).multiply(1, 0, 1).normalize().scale(r.knockback());
                            t.push(push.x, 0.15, push.z);
                            t.hurtMarked = true;
                        }
                    }
                }
                return;
            }
            if (t == null) {
                return;
            }
            r.getLookControl().setLookAt(t, 30.0F, 30.0F);
            double dist = Math.sqrt(r.distanceToSqr(t));
            boolean sees = r.getSensing().hasLineOfSight(t);
            if (r.archer()) {
                if (dist <= 15.0 && sees && r.attackCooldown <= 0) {
                    r.attackCooldown = 30 + r.random.nextInt(15);
                    r.getNavigation().stop();
                    r.play(attack);
                    return;
                }
                if (--repath <= 0) {
                    repath = 10;
                    if (dist > 12.0 || !sees) {
                        r.getNavigation().moveTo(t, 1.0);
                    } else if (dist < 5.0) {
                        Vec3 away = DefaultRandomPos.getPosAway(r, 6, 3, t.position());
                        if (away != null) {
                            r.getNavigation().moveTo(away.x, away.y, away.z, 1.1);
                        }
                    } else {
                        r.getNavigation().stop();
                    }
                }
                return;
            }
            if (dist <= reach(t) && r.attackCooldown <= 0) {
                r.attackCooldown = 20;
                r.getNavigation().stop();
                r.play(attack);
                return;
            }
            if (--repath <= 0) {
                repath = 10;
                r.getNavigation().moveTo(t, 1.15);
            }
        }

        private double reach(LivingEntity t) {
            return r.getBbWidth() * 0.5 + t.getBbWidth() * 0.5 + 1.6;
        }

        private void shoot(ServerLevel level, LivingEntity t) {
            Arrow arrow = new Arrow(level, r, new ItemStack(Items.ARROW), null);
            Vec3 from = r.getEyePosition().add(r.getLookAngle().scale(0.4));
            arrow.setPos(from.x, from.y - 0.1, from.z);
            arrow.pickup = AbstractArrow.Pickup.DISALLOWED;
            arrow.setBaseDamage(r.getAttributeValue(Attributes.ATTACK_DAMAGE) * 0.3);
            double dx = t.getX() - from.x;
            double dy = t.getY(0.4) - from.y;
            double dz = t.getZ() - from.z;
            double flat = Math.sqrt(dx * dx + dz * dz);
            arrow.shoot(dx, dy + flat * 0.15, dz, 1.7F, 2.0F);
            level.addFreshEntity(arrow);
            level.playSound(null, r, SoundEvents.ARROW_SHOOT, SoundSource.NEUTRAL, 1.0F, 1.1F);
        }
    }
}
