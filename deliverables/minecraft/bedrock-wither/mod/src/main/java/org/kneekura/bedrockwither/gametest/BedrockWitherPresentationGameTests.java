package org.kneekura.bedrockwither.gametest;

import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Consumer;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.world.damagesource.DamageTypes;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.animal.Cow;
import net.minecraft.world.entity.projectile.ThrownPotion;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.entity.living.LivingHurtEvent;
import net.minecraftforge.event.entity.living.LivingDropsEvent;
import net.minecraftforge.event.entity.ProjectileImpactEvent;
import net.minecraftforge.eventbus.api.EventPriority;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;
import org.kneekura.bedrockwither.BedrockWitherMod;
import org.kneekura.bedrockwither.entity.projectile.BedrockWitherSkullEntity;
import org.kneekura.bedrockwither.entity.BedrockWitherPresentation;

/** Production tick/impact tests; no direct call to the protected damage handler. */
@GameTestHolder(BedrockWitherMod.MOD_ID)
@PrefixGameTestTemplate(false)
public final class BedrockWitherPresentationGameTests {
    private BedrockWitherPresentationGameTests() {}

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_normalactualimpact")
    public static void normalTickDispatchesDirectImpactOnce(GameTestHelper helper) {
        assertActualImpact(helper, BedrockWitherSkullEntity.Kind.NORMAL);
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_dangerousactualimpact")
    public static void dangerousTickDispatchesDirectImpactOnce(GameTestHelper helper) {
        assertActualImpact(helper, BedrockWitherSkullEntity.Kind.DANGEROUS);
    }

    private static void assertActualImpact(GameTestHelper helper, BedrockWitherSkullEntity.Kind kind) {
        try (Fixture fixture = new Fixture(helper)) {
            Vec3 origin = origin(helper);
            Cow owner = fixture.cow(origin.add(-4, 0, 4));
            Cow target = fixture.cow(origin.add(1, 0, 0));
            BedrockWitherSkullEntity skull = fixture.skull(owner, origin.add(0, 0.5, 0), kind);
            AtomicInteger directHits = new AtomicInteger();
            Consumer<LivingHurtEvent> observer = event -> {
                if (event.getEntity() == target && event.getSource().is(DamageTypes.WITHER_SKULL)) {
                    directHits.incrementAndGet();
                    close(helper, BedrockWitherSkullEntity.impactDamageFor(helper.getLevel().getDifficulty()),
                            event.getAmount(), "direct collision damage");
                }
            };
            MinecraftForge.EVENT_BUS.addListener(EventPriority.NORMAL, false, LivingHurtEvent.class, observer);
            try {
                skull.tick();
                check(helper, directHits.get() == 1, "Actual projectile tick must dispatch one direct impact, got " + directHits);
                check(helper, skull.isRemoved(), "Impact must remove the skull");
                if (BedrockWitherSkullEntity.witherDurationFor(helper.getLevel().getDifficulty()) > 0) {
                    check(helper, target.hasEffect(MobEffects.WITHER), "Actual collision must apply Wither effect");
                }
                skull.tick();
                check(helper, directHits.get() == 1, "A removed skull must not apply a second direct hit");
            } finally {
                MinecraftForge.EVENT_BUS.unregister(observer);
            }
            helper.succeed();
        }
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_actualkillheal")
    public static void actualSkullKillHealsOwnerExactlyOnce(GameTestHelper helper) {
        try (Fixture fixture = new Fixture(helper)) {
            Vec3 origin = origin(helper);
            Cow owner = fixture.cow(origin.add(-4, 0, 4));
            owner.setHealth(2.0F);
            Cow target = fixture.cow(origin.add(1, 0, 0));
            target.setHealth(1.0F);
            BedrockWitherSkullEntity skull = fixture.skull(owner, origin.add(0, 0.5, 0), BedrockWitherSkullEntity.Kind.NORMAL);
            skull.tick();
            check(helper, !target.isAlive(), "The real impact must kill its target");
            close(helper, 7.0, owner.getHealth(), "Historical skull kill heals owner by five");
            skull.tick();
            close(helper, 7.0, owner.getHealth(), "Removed skull must not award a second heal");
            helper.succeed();
        }
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_liquidinertia")
    public static void skullPreservesVelocityInWaterAndAir(GameTestHelper helper) {
        try (Fixture fixture = new Fixture(helper)) {
            Vec3 origin = origin(helper);
            Cow owner = fixture.cow(origin.add(-4, 0, 4));
            for (int x = -1; x <= 2; x++) {
                for (int y = -1; y <= 1; y++) {
                    for (int z = -1; z <= 1; z++) {
                        fixture.placeWater(BlockPos.containing(origin).offset(x, y, z));
                    }
                }
            }
            for (BedrockWitherSkullEntity.Kind kind : BedrockWitherSkullEntity.Kind.values()) {
                BedrockWitherSkullEntity skull = fixture.skull(owner, origin, kind);
                Vec3 expected = new Vec3(0.2, 0.1, 0.05);
                skull.setDeltaMovement(expected);
                skull.tick();
                check(helper, skull.isInWater(), "Fixture must exercise Java's water branch");
                close(helper, 0.0, skull.getDeltaMovement().distanceTo(expected), "liquid_inertia=1 and gravity=0");
                skull.setPos(origin.add(0, 4, 0));
                skull.tick();
                check(helper, !skull.isInWater(), "Fixture must return to air");
                close(helper, 0.0, skull.getDeltaMovement().distanceTo(expected), "air inertia=1 and gravity=0");
            }
            helper.succeed();
        }
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_ownerlaunchimmunity")
    public static void ownerLaunchImmunityExpiresAfterFiveTicks(GameTestHelper helper) throws ReflectiveOperationException {
        try (Fixture fixture = new Fixture(helper)) {
            Vec3 origin = origin(helper);
            Cow owner = fixture.cow(origin);
            BedrockWitherSkullEntity skull = fixture.skull(owner, origin.add(0, 0.5, 0), BedrockWitherSkullEntity.Kind.NORMAL);
            Method canHit = findCanHit(skull.getClass());
            for (int ticks = 0; ticks < 5; ticks++) {
                skull.tickCount = ticks;
                check(helper, !(boolean) canHit.invoke(skull, owner), "Shooter must be immune during first five launch ticks");
            }
            skull.tickCount = 5;
            check(helper, (boolean) canHit.invoke(skull, owner), "Shooter grace must expire at five ticks even without leaving its box");
            helper.succeed();
        }
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_immediatereflection")
    public static void dangerousSkullReflectsAtLaunchWithoutInventedCooldown(GameTestHelper helper) {
        try (Fixture fixture = new Fixture(helper)) {
            Vec3 origin = origin(helper);
            Cow owner = fixture.cow(origin.add(-4, 0, 4));
            Cow hitter = fixture.cow(origin.add(0, 0, 3));
            hitter.setYRot(0);
            BedrockWitherSkullEntity dangerous = fixture.skull(owner, origin, BedrockWitherSkullEntity.Kind.DANGEROUS);
            check(helper, dangerous.tickCount == 0, "Fixture must hit immediately after launch");
            check(helper, dangerous.hurt(helper.getLevel().damageSources().mobAttack(hitter), 1), "Default reflect_immunity=0 allows an immediate reflection");
            check(helper, dangerous.getOwner() == hitter, "Reflection transfers owner");
            close(helper, 0.6, dangerous.getDeltaMovement().length(), "Explicit Java reflection-speed adapter");
            close(helper, 0.0, dangerous.getDeltaMovement().normalize().distanceTo(hitter.getLookAngle()), "Damage reflection uses attacker look adapter");
            BedrockWitherSkullEntity normal = fixture.skull(owner, origin, BedrockWitherSkullEntity.Kind.NORMAL);
            check(helper, !normal.hurt(helper.getLevel().damageSources().mobAttack(hitter), 1), "Normal skull must not reflect");
            helper.succeed();
        }
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_nondamagingreflection")
    public static void nonDamagingPotionImpactReflectsDangerousSkull(GameTestHelper helper) {
        try (Fixture fixture = new Fixture(helper)) {
            Vec3 origin = origin(helper);
            Cow owner = fixture.cow(origin.add(-4, 0, 4));
            Cow hitter = fixture.cow(origin.add(-4, 0, -4));
            BedrockWitherSkullEntity dangerous = fixture.skull(owner, origin, BedrockWitherSkullEntity.Kind.DANGEROUS);
            dangerous.setDeltaMovement(0, 0, -0.6);
            helper.getLevel().addFreshEntity(dangerous);
            ThrownPotion potion = fixture.track(new ThrownPotion(helper.getLevel(), hitter));
            potion.setPos(origin.add(-1, 0, 0));
            potion.setDeltaMovement(1.5, 0, 0);
            potion.tick();
            check(helper, potion.isRemoved(), "Potion must actually collide and complete its own impact");
            check(helper, !dangerous.isRemoved(), "Reflecting skull survives the incoming impact");
            check(helper, dangerous.getOwner() == hitter, "1.26.0 non-damaging projectile impact must reflect and transfer ownership");
            close(helper, 0.6, dangerous.getDeltaMovement().x, "Projectile direction adapter follows incoming motion");
            close(helper, 0.0, dangerous.getDeltaMovement().z, "Projectile reflection replaces old direction");
            helper.succeed();
        }
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_skippedprojectilereflection")
    public static void skippedProjectileImpactDoesNotReflectSkull(GameTestHelper helper) {
        try (Fixture fixture = new Fixture(helper)) {
            Vec3 origin = origin(helper);
            Cow owner = fixture.cow(origin.add(-4, 0, 4));
            Cow hitter = fixture.cow(origin.add(-4, 0, -4));
            BedrockWitherSkullEntity dangerous = fixture.skull(owner, origin, BedrockWitherSkullEntity.Kind.DANGEROUS);
            dangerous.setDeltaMovement(0, 0, -0.6);
            helper.getLevel().addFreshEntity(dangerous);
            ThrownPotion potion = fixture.track(new ThrownPotion(helper.getLevel(), hitter));
            potion.setPos(origin.add(-1, 0, 0));
            potion.setDeltaMovement(1.5, 0, 0);
            AtomicInteger skipped = new AtomicInteger();
            Consumer<ProjectileImpactEvent> skip = event -> {
                if (event.getProjectile() == potion) {
                    skipped.incrementAndGet();
                    event.setImpactResult(ProjectileImpactEvent.ImpactResult.SKIP_ENTITY);
                }
            };
            MinecraftForge.EVENT_BUS.addListener(EventPriority.LOW, false, ProjectileImpactEvent.class, skip);
            try {
                potion.tick();
                check(helper, skipped.get() == 1 && !potion.isRemoved(), "Fixture must exercise a real Forge-skipped impact");
                check(helper, dangerous.getOwner() == owner, "Skipped incoming impact must not transfer skull ownership");
                close(helper, -0.6, dangerous.getDeltaMovement().z, "Skipped impact must preserve skull trajectory");
            } finally {
                MinecraftForge.EVENT_BUS.unregister(skip);
            }
            helper.succeed();
        }
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_armorsourcepasses")
    public static void armorPassesMatchPinnedUvLightingAndPartialTicks(GameTestHelper helper) {
        var passes = BedrockWitherPresentation.armorPasses(true, 123, 0.25F, 0);
        check(helper, passes.size() == 2, "Pinned controller declares both white and blue armor passes");
        var white = passes.get(0);
        var blue = passes.get(1);
        close(helper, Math.cos(Math.toRadians((123.25 / 20.0) * 22.92)) * 3.0,
                white.u(), "White armor uses 22.92 degrees per second");
        close(helper, 1.2325, white.v(), "White armor vertical UV");
        close(helper, 1.2325, blue.u(), "Blue armor uses whole lifetime ticks plus frame alpha once");
        close(helper, 1.2325, blue.v(), "Blue armor vertical UV");
        check(helper, white.packedLight() == 0x00F000F0 && blue.packedLight() == 0x00F000F0,
                "Both official armor controllers ignore lighting");
        check(helper, white.red() == white.blue() && blue.blue() > blue.red(),
                "Java texture substitute keeps white and blue passes distinct");
        check(helper, BedrockWitherPresentation.armorPasses(false, 123, 0.25F, 0).isEmpty(),
                "Both armor layers hide immediately when shield query is false, including death flicker");
        check(helper, BedrockWitherPresentation.armorPasses(true, 123, 0.25F, 12345).equals(passes),
                "Scene lighting must not affect either armor pass");
        helper.succeed();
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_swellsourcemath")
    public static void swellAndBodyRotationUseLiteralMolangDegrees(GameTestHelper helper) {
        for (float swell : new float[]{0.0F, 0.5F, 1.0F, 1.5F, 7.0F}) {
            double clamped = Math.max(0, Math.min(1, swell));
            double adjustment = Math.pow(clamped, 4);
            double wobble = 1 + Math.sin(Math.toRadians(swell * 5730.0)) * swell * 0.01;
            var scale = BedrockWitherPresentation.scale(swell);
            close(helper, 2 * (1 + adjustment * 0.4) * wobble, scale.xz(), "Literal 5730-degree swell XZ");
            close(helper, 2 * (1 + adjustment * 0.1) / wobble, scale.y(), "Literal 5730-degree swell Y");
        }
        close(helper, Math.cos(Math.toRadians(123.25 / 20 * 114.6)),
                BedrockWitherPresentation.bodyRotation(123.25F), "Literal 114.6-degree body motion");
        helper.succeed();
    }

    @GameTest(template = "empty", timeoutTicks = 40, batch = "bwr_skinmolangboundary")
    public static void skinTimingUsesMolangFloatingPointModulo(GameTestHelper helper) {
        for (int ticks : new int[]{220, 81, 80, 79, 76, 74, 6, 4, 1}) {
            check(helper, !BedrockWitherPresentation.displayNormalSkin(ticks), "Normal skin must be hidden at " + ticks);
        }
        for (int ticks : new int[]{75, 65, 15, 5, 0, -1}) {
            check(helper, BedrockWitherPresentation.displayNormalSkin(ticks), "Normal skin must be visible at " + ticks);
        }
        helper.succeed();
    }

    private static Method findCanHit(Class<?> type) throws ReflectiveOperationException {
        for (Class<?> cursor = type; cursor != null; cursor = cursor.getSuperclass()) {
            try {
                Method result = cursor.getDeclaredMethod("canHitEntity", Entity.class);
                result.setAccessible(true);
                return result;
            } catch (NoSuchMethodException ignored) {
                // Exercise the production predicate, whichever class currently owns it.
            }
        }
        throw new NoSuchMethodException("canHitEntity");
    }

    private static Vec3 origin(GameTestHelper helper) {
        BlockPos pos = helper.absolutePos(new BlockPos(0, 5, 0));
        return new Vec3(pos.getX() + 0.5, pos.getY(), pos.getZ() + 0.5);
    }

    private static final class Fixture implements AutoCloseable {
        private final GameTestHelper helper;
        private final List<Entity> entities = new ArrayList<>();
        private final Map<BlockPos, BlockState> originalBlocks = new LinkedHashMap<>();
        private final Consumer<LivingDropsEvent> drops = event -> {
            if (entities.contains(event.getEntity())) entities.addAll(event.getDrops());
        };

        private Fixture(GameTestHelper helper) {
            this.helper = helper;
            MinecraftForge.EVENT_BUS.addListener(EventPriority.NORMAL, false, LivingDropsEvent.class, drops);
        }

        private <T extends Entity> T track(T entity) {
            entities.add(entity);
            return entity;
        }

        private Cow cow(Vec3 pos) {
            Cow cow = EntityType.COW.create(helper.getLevel());
            if (cow == null) throw new IllegalStateException("Could not create cow fixture");
            track(cow);
            cow.setNoAi(true);
            cow.setNoGravity(true);
            cow.setPos(pos);
            helper.getLevel().addFreshEntity(cow);
            return cow;
        }

        private BedrockWitherSkullEntity skull(Cow owner, Vec3 origin, BedrockWitherSkullEntity.Kind kind) {
            var skull = track(BedrockWitherSkullEntity.create(helper.getLevel(), owner, origin,
                    new Vec3(1, 0, 0), kind));
            skull.setDeltaMovement(1.2, 0, 0); // Deterministic impact fixture, separate from launch spread.
            return skull;
        }

        private void placeWater(BlockPos pos) {
            originalBlocks.putIfAbsent(pos.immutable(), helper.getLevel().getBlockState(pos));
            helper.getLevel().setBlock(pos, Blocks.WATER.defaultBlockState(), 3);
        }

        @Override
        public void close() {
            MinecraftForge.EVENT_BUS.unregister(drops);
            entities.forEach(Entity::discard);
            originalBlocks.forEach((pos, state) -> helper.getLevel().setBlock(pos, state, 3));
        }
    }

    private static void close(GameTestHelper helper, double expected, double actual, String label) {
        check(helper, Math.abs(expected - actual) < 0.00001, label + ": expected " + expected + ", got " + actual);
    }

    private static void check(GameTestHelper helper, boolean condition, String message) {
        if (!condition) helper.fail(message);
    }
}
