package dev.kneekura.fivedifficulties.forge.entity.mob;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.forge.PortRegistries;
import dev.kneekura.fivedifficulties.forge.X1Config;
import dev.kneekura.fivedifficulties.forge.entity.SpellCardCircleEntity;
import dev.kneekura.fivedifficulties.forge.entity.THItemEntity;
import dev.kneekura.fivedifficulties.forge.shot.X1Danmaku;
import dev.kneekura.fivedifficulties.forge.shot.X1Hit;
import dev.kneekura.fivedifficulties.forge.spellcard.X1SpellCardDeclaration;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.Difficulty;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.RandomStrollGoal;
import net.minecraft.world.entity.ai.targeting.TargetingConditions;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

import java.util.Optional;

/**
 * Port of X1 {@code EntityDanmakuMob}, the base of every danmaku mob. Without a target it wanders (X1's legacy
 * {@code updateEntityActionState}); with one (the nearest damageable player within the detection range, or
 * whoever hurt it) it hovers {@code flyingHeight} blocks up, faces the target, runs {@code danmakuPattern} each
 * tick it can see it, and keeps its attack distance with eased moves. Bat sounds, no fall damage while flying.
 */
public abstract class DanmakuMobEntity extends PathfinderMob {
    private static final EntityDataAccessor<Byte> DATA_FORM =
            SynchedEntityData.defineId(DanmakuMobEntity.class, EntityDataSerializers.BYTE);
    private static final EntityDataAccessor<Integer> DATA_PATTERN =
            SynchedEntityData.defineId(DanmakuMobEntity.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Byte> DATA_SPELL_MOTION =
            SynchedEntityData.defineId(DanmakuMobEntity.class, EntityDataSerializers.BYTE);
    private static final EntityDataAccessor<Byte> DATA_FLYING =
            SynchedEntityData.defineId(DanmakuMobEntity.class, EntityDataSerializers.BYTE);

    protected int lastTime;
    public int attackCounter = 0;
    public int attackInterval;
    public int lostTarget;
    protected Vec3d moveVec = Vec3d.ZERO;
    protected int moveTimer;
    protected int moveTimerMax;
    protected boolean stop;
    protected double attackDistance;
    protected double detectionDistance;
    public boolean isFlyingMode;
    public int danmakuSpan;
    public byte shotForm;
    public byte shotColor;
    public float speedRate;
    public short special;
    public boolean isSpellCardMode;
    private String danmakuMobName = "";
    protected int species_1;
    protected int species_2;
    public SpellCardCircleEntity circle;

    public static final int CIRCLE_COLOR_RED = 0, CIRCLE_COLOR_BLUE = 1, CIRCLE_COLOR_GREEN = 2, CIRCLE_COLOR_YELLOW = 3,
            CIRCLE_COLOR_PURPLE = 4, CIRCLE_COLOR_AQUA = 5, CIRCLE_COLOR_ORANGE = 6, CIRCLE_COLOR_WHITE = 7, CIRCLE_COLOR_RAINBOW = 8;
    public static final int SPECIES_HUMAN = 0, SPECIES_GOD = 32, SPECIES_FAIRY = 64, SPECIES_FAIRY_ICE = 65, SPECIES_PHANTOM = 92,
            SPECIES_PHANTOM_HALF = 93, SPECIES_PHANTOM_GHOST = 94, SPECIES_SHIKIGAMI = 108, SPECIES_SHIKIGAMI_DOLL = 109,
            SPECIES_SHIKIGAMI_FAMILIAR = 110, SPECIES_YOUKAI = 128, SPECIES_YOUKAI_BUG = 139, SPECIES_DRAGON = 192,
            SPECIES_HUMAN_SAINT = 6, SPECIES_GOD_ARAHITOGAMI = 33, SPECIES_HUMAN_HALF = 1, SPECIES_OTHERS = 255;
    public static final int NOT_ATTACK = 0, ATTACK_END = 127;
    public static final int NORMAL_ATTACK01 = 1, NORMAL_ATTACK02 = 2, NORMAL_ATTACK03 = 3, NORMAL_ATTACK04 = 4, NORMAL_ATTACK05 = 5;
    public static final int SPELLCARD_ATTACK01 = 101, SPELLCARD_ATTACK02 = 102, SPELLCARD_ATTACK03 = 103, SPELLCARD_ATTACK04 = 104,
            SPELLCARD_ATTACK05 = 105, SPELLCARD_ATTACK06 = 106;

    protected DanmakuMobEntity(EntityType<? extends DanmakuMobEntity> type, Level level) {
        super(type, level);
        this.isFlyingMode = true;
        this.setFlyingHeight(3);
        this.stop = false;
        this.setSpecies(SPECIES_OTHERS);
        this.xpReward = 1;
    }

    /** applyEntityAttributes: health 2, speed 0.25, no knock-back resistance, follow range 30. */
    public static AttributeSupplier.Builder createDanmakuAttributes() {
        return PathfinderMob.createMobAttributes().add(Attributes.MAX_HEALTH, 2.0D).add(Attributes.MOVEMENT_SPEED, 0.25D)
                .add(Attributes.KNOCKBACK_RESISTANCE, 0.0D).add(Attributes.FOLLOW_RANGE, 30.0D);
    }

    @Override
    protected void registerGoals() {
        // X1 legacy AI: wander only when there is no target (updateEntityActionState).
        this.goalSelector.addGoal(1, new RandomStrollGoal(this, 1.0D) {
            @Override
            public boolean canUse() {
                return DanmakuMobEntity.this.getTarget() == null && super.canUse();
            }

            @Override
            public boolean canContinueToUse() {
                return DanmakuMobEntity.this.getTarget() == null && super.canContinueToUse();
            }
        });
    }

    @Override
    protected void defineSynchedData() {
        super.defineSynchedData();
        this.entityData.define(DATA_FORM, (byte) 0);
        this.entityData.define(DATA_PATTERN, 0);
        this.entityData.define(DATA_SPELL_MOTION, (byte) 0);
        this.entityData.define(DATA_FLYING, (byte) 0);
    }

    public void setMaxHP(float hp) {
        this.getAttribute(Attributes.MAX_HEALTH).setBaseValue(hp);
    }

    public void setSpeed(double speed) {
        this.getAttribute(Attributes.MOVEMENT_SPEED).setBaseValue(speed);
    }

    public double getSpeedValue() {
        return this.getAttribute(Attributes.MOVEMENT_SPEED).getBaseValue();
    }

    public void setAttackDistance(double d) { attackDistance = d; }
    public double getAttackDistance() { return attackDistance; }
    public void setDetectionDistance(double d) { detectionDistance = d; }
    protected double getDetectionDistance() { return detectionDistance; }
    protected boolean canFairyCall() { return false; }
    protected double getFairyCallDistance() { return 10.0D; }

    protected void setSpellCardAttack() {
        setSpellCardMotion((byte) -30);
    }

    /** X1 getTarget: nothing while the danmaku level is 0. */
    public LivingEntity x1Target() {
        if (X1Config.danmakuLevel() <= 0) return null;
        return getTarget();
    }

    public Vec3d pos(double x, double y, double z) { return new Vec3d(x, y, z); }
    public Vec3d pos() { return X1Danmaku.pos_Living(this); }
    public Vec3d pos(LivingEntity living) { return X1Danmaku.pos_Living(living); }
    public Vec3d angle(float yaw, float pitch) { return X1Danmaku.angle(yaw, pitch); }
    public Vec3d gravity_Zero() { return Vec3d.ZERO; }

    public int getDanmakuPattern() { return this.entityData.get(DATA_PATTERN); }
    public void setDanmakuPattern(int p) { this.entityData.set(DATA_PATTERN, p); }
    public byte getSpellCardMotion() { return this.entityData.get(DATA_SPELL_MOTION); }
    public void setSpellCardMotion(byte m) { this.entityData.set(DATA_SPELL_MOTION, m); }
    public int getUsingSpellCardNo() { return -1; }
    public boolean isSpellCardAttack() { return getUsingSpellCardNo() >= 0; }
    public byte getFlyingHeight() { return this.entityData.get(DATA_FLYING); }
    public void setFlyingHeight(int h) { this.entityData.set(DATA_FLYING, (byte) h); }
    public String getDanmakuMobName() { return danmakuMobName; }
    public void setDanmakuMobName(String name) { danmakuMobName = name; }
    public byte getForm() { return this.entityData.get(DATA_FORM); }
    public void setForm(byte f) { this.entityData.set(DATA_FORM, f); }

    protected void setSpecies(int s1, int s2) {
        species_1 = s1;
        species_2 = s2;
    }

    protected void setSpecies(int s) {
        setSpecies(s, -1);
    }

    /** X1 returns SPECIES_OTHERS here regardless of setSpecies; subclasses override. */
    public int getSpecies_1() { return SPECIES_OTHERS; }
    public int getSpecies_2() { return SPECIES_OTHERS; }

    public boolean isHuman() { return getSpecies_1() < SPECIES_GOD || getSpecies_2() < SPECIES_GOD; }

    public boolean isPhantom() {
        return (getSpecies_1() >= SPECIES_PHANTOM && getSpecies_1() < SPECIES_SHIKIGAMI)
                || (getSpecies_2() >= SPECIES_PHANTOM && getSpecies_2() < SPECIES_SHIKIGAMI);
    }

    public boolean isFairy() { return getSpecies_1() == SPECIES_FAIRY || getSpecies_2() == SPECIES_FAIRY; }

    public boolean isYoukai() {
        return (getSpecies_1() >= SPECIES_YOUKAI && getSpecies_1() < SPECIES_DRAGON)
                || (getSpecies_2() >= SPECIES_YOUKAI && getSpecies_2() < SPECIES_DRAGON);
    }

    public boolean isInSpecies(int s) { return getSpecies_1() == s || getSpecies_2() == s; }

    protected void setStopStart() {
        stop = true;
        moveTimer = 0;
        moveTimerMax = 0;
    }

    protected void setStopEnd() { stop = false; }
    public boolean isStop() { return stop; }

    protected void move(Vec3d move, double speed, int time) {
        moveVec = new Vec3d(move.x() * speed, move.y() * speed, move.z() * speed);
        moveTimer = time;
        moveTimerMax = time;
    }

    protected void moveRight(double speed, int time) { move(X1Danmaku.getVecFromAngle(getYRot() + 90F, getXRot()), speed, time); }
    protected void moveLeft(double speed, int time) { move(X1Danmaku.getVecFromAngle(getYRot() - 90F, getXRot()), speed, time); }
    protected void moveForward(double speed, int time) { move(X1Danmaku.getVecFromAngle(getYRot(), getXRot()), speed, time); }
    protected void moveBack(double speed, int time) { move(X1Danmaku.getVecFromAngle(getYRot() + 180, getXRot()), speed, time); }

    protected void moveDanmakuAttack(int nextPattern, int interval, float maxHP, int invincibleTime) {
        setDanmakuPattern((byte) nextPattern);
        attackCounter = -interval;
        deathTime = 0;
        // 1.7.10 let onDeath run again for every phase; 1.20's die() is guarded by `dead`.
        this.dead = false;
        if (!this.level().isClientSide) {
            setMaxHP(maxHP);
            setHealth(maxHP);
        }
        attackInterval = invincibleTime;
        X1Danmaku.danmakuRemove(this, 40.0D, "Enemy", true);
        isSpellCardMode = false;
        if (circle != null) circle.discard();
    }

    public Vec3d look() { return X1Danmaku.angle(getYRot(), getXRot()); }
    public int getSpellCardCircleColor() { return CIRCLE_COLOR_RED; }

    protected void useSpellCard(int spellCardNo) {
        if (getTarget() != null && this.level() instanceof ServerLevel server) {
            X1SpellCardDeclaration.declare(server, this, getTarget(), spellCardNo, 0, X1Config.danmakuLevel(), !isSpellCardMode);
        }
        if (!isSpellCardMode) {
            isSpellCardMode = true;
            circle = new SpellCardCircleEntity(this.level(), this, 16 + getSpellCardCircleColor(), -100);
            if (!this.level().isClientSide) this.level().addFreshEntity(circle);
            this.setSpellCardAttack();
        }
    }

    @Override
    public void baseTick() {
        if (this.tickCount > lastTime) super.baseTick();
    }

    @Override
    public void tick() {
        if (!this.level().isClientSide && this.level().getDifficulty() == Difficulty.PEACEFUL) {
            this.discard();
            return;
        }
        if (X1Config.danmakuLevel() <= 0) setTarget(null);
        if (this.tickCount <= lastTime) {
            this.setDeltaMovement(0, 0, 0);
            this.setPos(this.xo, this.yo, this.zo);
            return;
        }
        super.tick();
        if (getHealth() <= 0.0F) return;
        if (attackInterval > 0) attackInterval--;
        if (isSpellCardAttack() && attackCounter == -20) setSpellCardAttack();
        if (getSpellCardMotion() < 0 && !this.level().isClientSide) setSpellCardMotion((byte) (getSpellCardMotion() + 2));
        if (moveTimer > 0) {
            double rate = Math.cos((double) moveTimer / (double) moveTimerMax * Math.PI / 2.0D);
            if (!this.level().isClientSide) this.move(MoverType.SELF, new Vec3(moveVec.x() * rate, moveVec.y() * rate, moveVec.z() * rate));
            moveTimer--;
        }
        LivingEntity target = getTarget();
        if (getFlyingHeight() > 0) {
            int heightCount = 0;
            while (this.level().isEmptyBlock(new BlockPos((int) getX(), (int) getY() - heightCount, (int) getZ())) && heightCount < 8) {
                heightCount++;
            }
            var m = getDeltaMovement();
            double my = m.y;
            if (target != null && heightCount > getFlyingHeight()) {
                my += (target.getY() - getY()) * 0.0006D;
            } else if (heightCount < getFlyingHeight()) {
                my += 0.006D; // X1's inner ">=" branch can never run here
            }
            this.setDeltaMovement(m.x, my, m.z);
            if (!stop) this.move(MoverType.SELF, new Vec3(0D, my, 0D));
        }
        if (target != null && !target.isAlive()) setTarget(null);
        if (getTarget() == null && !this.level().isClientSide) {
            Player found = this.level().getNearestPlayer(
                    TargetingConditions.forCombat().range(getDetectionDistance()).ignoreLineOfSight(), this);
            setTarget(found);
            if (found != null && canFairyCall()) {
                for (Entity e : this.level().getEntities(this, getBoundingBox().inflate(getFairyCallDistance()))) {
                    if (e instanceof THFairyEntity fairy && fairy.getTarget() == null) fairy.setTarget(found);
                }
            }
        }
        target = getTarget();
        if (target != null && this.isAlive()) {
            double dx = target.getX() - getX();
            double dy = (target.getY() + target.getEyeHeight()) - (getY() + this.getEyeHeight());
            double dz = target.getZ() - getZ();
            float yaw = -((float) Math.atan2(dx, dz)) / 3.141593F * 180F;
            float pitch = -(float) Math.atan2(dy, Math.sqrt(dx * dx + dz * dz)) / 3.141593F * 180F;
            if (!stop) {
                this.setYRot(yaw);
                this.setXRot(pitch);
                this.yHeadRot = yaw;
            }
            if (this.hasLineOfSight(target)) {
                lostTarget = 0;
                int level = X1Config.danmakuLevel();
                if (level != 0 && attackCounter >= 0 && !this.level().isClientSide) danmakuPattern(level);
                attackCounter++;
            } else if (++lostTarget > 200) {
                setTarget(null);
            }
            if (moveTimer <= 0 && lostTarget > 0) {
                move(X1Danmaku.getVecFromAngle(this.random.nextFloat() + 360F, this.random.nextFloat() * 360F), getSpeedValue(), 30);
            }
            LivingEntity t = getTarget();
            if (moveTimer <= 0 && t != null && getAttackDistance() > 0) {
                double d = this.distanceTo(t);
                if (d < getAttackDistance()) moveBack(getSpeedValue() * 0.3D * (1.0D - d / getAttackDistance()), 15);
                else moveForward(getSpeedValue() * 0.5D * (d / getAttackDistance()), 15);
            }
        }
        if (this.tickCount > lastTime) lastTime = this.tickCount;
    }

    /** X1 entityToAttack was set without line-of-sight checks; the client never had it. */
    @Override
    public boolean isInvulnerableTo(DamageSource source) {
        return attackInterval > 0 || super.isInvulnerableTo(source);
    }

    @Override
    public boolean hurt(DamageSource source, float damage) {
        // X1 passes applyPotionDamageCalculations(damage) into super, which applies it again.
        if (super.hurt(source, this.getDamageAfterMagicAbsorb(source, damage)) && source.getEntity() instanceof LivingEntity entity) {
            this.setDeltaMovement(getDeltaMovement().scale(0.0001D));
            if (!this.hasPassenger(entity) && this.getVehicle() != entity && entity instanceof Player) setTarget(entity);
            return true;
        }
        return false;
    }

    /** hitCheck: a contact hit along the current motion (blocks stop it, hit size 0.9). */
    public void hitCheck(float damage) {
        Vec3 from = position(), to = from.add(getDeltaMovement());
        var block = this.level().clip(new ClipContext(from, to, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, this));
        if (block.getType() != HitResult.Type.MISS) {
            X1Danmaku.playShotSound(this);
            to = block.getLocation();
        }
        Entity hit = hitEntityCheck(from, to);
        if (hit != null) onImpact(hit, damage);
    }

    public Entity hitEntityCheck(Vec3 from, Vec3 to) {
        Entity best = null;
        double d = 0.0D;
        float hitSize = 0.9F;
        for (Entity e : this.level().getEntities(this, getBoundingBox().expandTowards(getDeltaMovement()).inflate(hitSize))) {
            if (!e.isPickable()) continue;
            Optional<Vec3> at = X1Hit.intercept(e.getBoundingBox().inflate(hitSize), from, to);
            if (at.isPresent()) {
                double d1 = from.distanceTo(at.get());
                if (d1 < d || d == 0.0D) {
                    best = e;
                    d = d1;
                }
            }
        }
        return best;
    }

    protected void onImpact(Entity hit, float damage) {
        if (!this.level().isClientSide && hit != null) hit.hurt(this.damageSources().mobAttack(this), damage);
    }

    /** moveEntityWithHeading: flying mobs (flying height > 0) fly with air drag 0.91 and no gravity. */
    @Override
    public void travel(Vec3 input) {
        if (getFlyingHeight() <= 0) {
            super.travel(input);
            return;
        }
        if (this.isInWater()) {
            this.moveRelative(0.02F, input);
            this.moveRelative(0.02F, input);
            this.move(MoverType.SELF, getDeltaMovement());
            this.setDeltaMovement(getDeltaMovement().scale(0.800000011920929D));
        } else {
            this.moveRelative(0.02F, input);
            float f2 = 0.91F;
            if (this.onGround()) f2 = this.level().getBlockState(getBlockPosBelowThatAffectsMyMovement()).getFriction(level(), getBlockPosBelowThatAffectsMyMovement(), this) * 0.91F;
            float f3 = 0.16277136F / (f2 * f2 * f2);
            this.moveRelative(this.onGround() ? 0.1F * f3 : 0.02F, input);
            this.move(MoverType.SELF, getDeltaMovement());
            this.setDeltaMovement(getDeltaMovement().scale(f2));
        }
        this.calculateEntityAnimation(false);
    }

    /** Test hook: one death tick (X1 onDeathUpdate), where bosses move to their next phase. */
    public void deathStepForTest() {
        this.tickDeath();
    }

    /** Test hook: run this tick's pattern at the given level. */
    public void patternForTest(int level) {
        this.danmakuPattern(level);
    }

    public boolean deadFlag() {
        return this.dead;
    }

    /** Overridden by each mob: the danmaku for this tick at the given difficulty level. */
    protected void danmakuPattern(int level) {}

    @Override
    protected void tickDeath() {
        super.tickDeath();
        if (this.deathTime == 7) {
            float size = 1.0F + deathTime * 0.1F;
            if (this.level().isClientSide) {
                this.level().addParticle(size >= 2.0F ? ParticleTypes.EXPLOSION_EMITTER : ParticleTypes.EXPLOSION,
                        getX(), getY(), getZ(), 1.0D, 0.0D, 0.0D);
            } else {
                this.level().playSound(null, getX(), getY(), getZ(), SoundEvents.FIREWORK_ROCKET_BLAST, SoundSource.HOSTILE, 2.0F, 3.0F);
                banishExplosion(this, 5.0F, 5.0F);
            }
        }
    }

    /** THShotLib.explosionEffect: "random.explosion" at 2.0 / 3.0 and a large (size ≥ 2: huge) explosion particle. */
    public static void explosionEffect(Level level, double x, double y, double z, float size) {
        if (level.isClientSide) {
            level.addParticle(size >= 2.0F ? ParticleTypes.EXPLOSION_EMITTER : ParticleTypes.EXPLOSION, x, y, z, 1.0D, 0.0D, 0.0D);
        } else {
            level.playSound(null, x, y, z, SoundEvents.GENERIC_EXPLODE, SoundSource.HOSTILE, 2.0F, 3.0F);
        }
    }

    /** X1 isValidLightLevel + not peaceful: sky light at most a random 0..31, light at most 0..7 (thunder: sky 10). */
    public static boolean darkEnough(net.minecraft.world.level.ServerLevelAccessor level, BlockPos pos, net.minecraft.util.RandomSource random) {
        if (level.getDifficulty() == Difficulty.PEACEFUL) return false;
        if (level.getBrightness(net.minecraft.world.level.LightLayer.SKY, pos) > random.nextInt(32)) return false;
        int light = level.getLevel().isThundering() ? level.getMaxLocalRawBrightness(pos, 10) : level.getMaxLocalRawBrightness(pos);
        return light <= random.nextInt(8);
    }

    /** THShotLib.banishExplosion: nearby fairies (not familiars) take up to maxDamage, at least 2. */
    public static void banishExplosion(Entity dead, double range, float maxDamage) {
        for (Entity e : dead.level().getEntities(dead, dead.getBoundingBox().inflate(range))) {
            if (e instanceof THFairyEntity fairy && !(e instanceof FamiliarEntity)) {
                double distance = e.distanceTo(dead);
                if (distance <= range) {
                    float damage = Math.max(2.0F, maxDamage * (1.0F - (float) (distance / range)));
                    fairy.hurt(dead.damageSources().indirectMagic(e, dead), damage);
                }
            }
        }
    }

    @Override
    protected void dropCustomDeathLoot(DamageSource source, int looting, boolean hitByPlayer) {
        if (getUsingSpellCardNo() >= 0 && hitByPlayer) {
            var card = PortRegistries.SPELL_CARD_ITEMS.get(getUsingSpellCardNo());
            if (card != null) this.spawnAtLocation(new ItemStack(card.get()), 0.0F);
        }
    }

    public void dropItem(int type, Vec3d pos, Vec3d angle) {
        if (!this.level().isClientSide) {
            this.level().addFreshEntity(new THItemEntity(this.level(), pos.x(), pos.y(), pos.z(), angle, (byte) type));
        }
    }

    private Vec3d upwardRandom() {
        return X1Danmaku.angle_LimitRandom(new java.util.Random(), new Vec3d(0.0D, 1.0D, 0.0D), 90F);
    }

    public void dropPowerUpItem(int num) { for (int i = 1; i <= num; i++) dropItem(1, pos(), upwardRandom()); }
    public void dropPointItem(int num) { for (int i = 1; i <= num; i++) dropItem(4, pos(), upwardRandom()); }
    public void dropSpellCardItem(int num) { for (int i = 1; i <= num; i++) dropItem(10, pos(), upwardRandom()); }
    public void dropExtendItem(int num) { for (int i = 1; i <= num; i++) dropItem(11, pos(), upwardRandom()); }

    public void dropShotItem(int shotID, int stackNumber, int number, int speed, int color, int gravity, int special, int form) {
        if (shotID < 0 || shotID >= PortRegistries.SHOT_ITEMS.size()) return;
        ItemStack shot = new ItemStack(PortRegistries.SHOT_ITEMS.get(shotID).get(), stackNumber);
        CompoundTag nbt = shot.getOrCreateTag();
        nbt.putShort("Number", (short) number);
        nbt.putByte("Speed", (byte) (speed % 64));
        nbt.putByte("Color", (byte) (color % 16));
        nbt.putByte("Gravity", (byte) (gravity % 16));
        nbt.putInt("Special", special);
        nbt.putByte("DanmakuForm", (byte) (form % 8));
        this.spawnAtLocation(shot, 0.0F);
    }

    @Override
    public boolean causeFallDamage(float distance, float multiplier, DamageSource source) {
        return getFlyingHeight() > 0 && super.causeFallDamage(distance, multiplier, source);
    }

    @Override
    protected void checkFallDamage(double y, boolean onGround, net.minecraft.world.level.block.state.BlockState state, BlockPos pos) {}

    @Override
    protected float getSoundVolume() { return 0.3F; }

    @Override
    public float getVoicePitch() { return super.getVoicePitch() * 1.95F; }

    @Override
    protected SoundEvent getAmbientSound() { return this.random.nextInt(4) != 0 ? null : SoundEvents.BAT_AMBIENT; }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) { return SoundEvents.BAT_HURT; }

    @Override
    protected SoundEvent getDeathSound() { return SoundEvents.BAT_DEATH; }

    @Override
    public int getMaxSpawnClusterSize() { return 1; }

    /** Enderman-style teleports (X1 copied them). */
    protected boolean teleportRandomly(double range) {
        int count = 0;
        double x, y, z;
        do {
            x = getX() + (this.random.nextDouble() - 0.5D) * range;
            y = getY() + (double) (this.random.nextInt((int) range) - (int) (range / 2.0D));
            z = getZ() + (this.random.nextDouble() - 0.5D) * range;
            count++;
        } while (!x1TeleportTo(x, y, z) && count < 10);
        return true;
    }

    protected boolean teleportToEntity(Entity target) {
        Vec3 v = new Vec3(getX() - target.getX(), getBoundingBox().minY + getBbHeight() / 2.0F - target.getY() + target.getEyeHeight(),
                getZ() - target.getZ()).normalize();
        double d0 = 16.0D;
        return x1TeleportTo(getX() + (this.random.nextDouble() - 0.5D) * 8.0D - v.x * d0,
                getY() + (double) (this.random.nextInt(16) - 8) - v.y * d0,
                getZ() + (this.random.nextDouble() - 0.5D) * 8.0D - v.z * d0);
    }

    protected boolean x1TeleportTo(double x, double y, double z) {
        var event = net.minecraftforge.event.ForgeEventFactory.onEnderTeleport(this, x, y, z);
        if (event.isCanceled()) return false;
        double ox = getX(), oy = getY(), oz = getZ();
        double nx = event.getTargetX(), ny = event.getTargetY(), nz = event.getTargetZ();
        boolean ok = false;
        BlockPos.MutableBlockPos at = BlockPos.containing(nx, ny, nz).mutable();
        if (this.level().hasChunkAt(at)) {
            boolean found = false;
            while (!found && at.getY() > this.level().getMinBuildHeight()) {
                if (this.level().getBlockState(at.below()).blocksMotion()) found = true;
                else {
                    ny--;
                    at.move(0, -1, 0);
                }
            }
            if (found) {
                this.setPos(nx, ny, nz);
                if (this.level().noCollision(this) && !this.level().containsAnyLiquid(getBoundingBox())) ok = true;
            }
        }
        if (!ok) {
            this.setPos(ox, oy, oz);
            return false;
        }
        this.level().playSound(null, ox, oy, oz, SoundEvents.ENDERMAN_TELEPORT, SoundSource.HOSTILE, 1.0F, 1.0F);
        this.playSound(SoundEvents.ENDERMAN_TELEPORT, 1.0F, 1.0F);
        return true;
    }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        setForm(tag.getByte("Form"));
        setDanmakuPattern(tag.getInt("Danmaku"));
        danmakuSpan = tag.getShort("Span");
        shotForm = tag.getByte("ShotForm");
        shotColor = tag.getByte("ShotColor");
        speedRate = tag.getFloat("Speed");
        setAttackDistance(tag.getByte("AttackRange"));
        setDetectionDistance(tag.getByte("DetectRange"));
        setFlyingHeight(tag.getByte("Flying"));
        special = tag.getShort("Special");
        isFlyingMode = getFlyingHeight() > 0;
        if (shotForm < 0 || shotForm >= 32) shotForm = 0;
        if (shotColor < 0 || shotColor >= 10) shotColor = 8;
    }

    @Override
    public void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        tag.putByte("Form", getForm());
        tag.putInt("Danmaku", getDanmakuPattern());
        tag.putShort("Span", (short) danmakuSpan);
        tag.putByte("ShotForm", shotForm);
        tag.putByte("ShotColor", shotColor);
        tag.putFloat("Speed", speedRate);
        tag.putByte("AttackRange", (byte) getAttackDistance());
        tag.putByte("DetectRange", (byte) getDetectionDistance());
        tag.putByte("Flying", (byte) getFlyingHeight());
        tag.putShort("Special", special);
    }

    protected static float wrap(float a) {
        return Mth.wrapDegrees(a);
    }

    protected static AABB box(Entity e) {
        return e.getBoundingBox();
    }
}
