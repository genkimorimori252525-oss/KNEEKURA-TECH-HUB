package org.kneekura.staff;

import com.mojang.authlib.GameProfile;
import java.util.UUID;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.common.util.FakePlayer;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;

/** Direct handler/subsystem assertions; no physical input or client/network evidence. */
@GameTestHolder("kneekura")
@PrefixGameTestTemplate(false)
public final class StaffGameTests {
    private enum Fault { NONE, REFRESH_EFFECT, ATTEMPT_DAMAGE }

    private static void assertHandler(GameTestHelper helper, Fault fault) {
        var player = new TickableStaffPlayer(helper.getLevel());
        var item = StaffMod.STAFF.get();
        var stack = new ItemStack(item);
        player.setItemInHand(InteractionHand.MAIN_HAND, stack);
        float health = player.getHealth();
        int count = stack.getCount();
        int damage = stack.getDamageValue();
        int hurtAttempts = player.hurtAttempts;
        var result = item.use(helper.getLevel(), player, InteractionHand.MAIN_HAND);
        helper.assertTrue(result.getResult() == InteractionResult.CONSUME, "Server handler must consume successful use");
        var effect = player.getEffect(MobEffects.GLOWING);
        helper.assertTrue(effect != null && effect.getDuration() == 60 && effect.getAmplifier() == 0,
                          "Handler must grant the invoking player exactly Glowing I for 60 ticks");
        helper.assertTrue(player.getCooldowns().isOnCooldown(item), "Handler must start cooldown");
        helper.assertTrue(player.getCooldowns().getCooldownPercent(item, 0) == 1.0F, "Initial cooldown must be full");
        player.advanceAbilityTick();
        int remainingEffect = effect.getDuration();
        int amplifier = effect.getAmplifier();
        helper.assertTrue(remainingEffect == 59, "Real effect ticking must decrement duration before repeat");
        float remainingCooldown = player.getCooldowns().getCooldownPercent(item, 0);
        var repeat = item.use(helper.getLevel(), player, InteractionHand.MAIN_HAND);
        // Optional negative controls deliberately corrupt the result before the
        // SAME assertions below. They must be retained as actual FAIL results.
        if (fault == Fault.REFRESH_EFFECT) player.addEffect(new MobEffectInstance(MobEffects.GLOWING, 60, 0));
        if (fault == Fault.ATTEMPT_DAMAGE) player.hurt(player.damageSources().generic(), 1.0F);
        helper.assertTrue(repeat.getResult() == InteractionResult.FAIL, "Cooldown rejects repeated use");
        helper.assertTrue(player.getCooldowns().getCooldownPercent(item, 0) == remainingCooldown,
                          "Repeated use must not refresh cooldown");
        var after = player.getEffect(MobEffects.GLOWING);
        helper.assertTrue(after != null && after.getDuration() == remainingEffect && after.getAmplifier() == amplifier,
                          "Repeated use must not refresh effect duration/amplifier, including in-place updates");
        helper.assertTrue(player.hurtAttempts == hurtAttempts && player.getHealth() == health,
                          "Ability must not attempt damage, even when FakePlayer is invulnerable");
        helper.assertTrue(stack.getCount() == count && stack.getDamageValue() == damage,
                          "Ability must not consume or wear the staff");
        helper.succeed();
    }

    private static void assertExpiry(GameTestHelper helper, boolean shortenCooldown) {
        var player = new TickableStaffPlayer(helper.getLevel());
        var item = StaffMod.STAFF.get();
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(item));
        item.use(helper.getLevel(), player, InteractionHand.MAIN_HAND);
        if (shortenCooldown) player.getCooldowns().addCooldown(item, 99);
        // FakePlayer.tick is intentionally a no-op. Advance only real effect
        // and cooldown subsystem methods; this is not wall-clock scheduling.
        for (int tick = 0; tick < 59; tick++) player.advanceAbilityTick();
        var effect = player.getEffect(MobEffects.GLOWING);
        helper.assertTrue(effect != null && effect.getDuration() == 1, "Glowing must still exist at tick 59");
        player.advanceAbilityTick();
        helper.assertTrue(!player.hasEffect(MobEffects.GLOWING), "Glowing must expire at subsystem tick 60");
        helper.assertTrue(player.getCooldowns().isOnCooldown(item), "Cooldown must remain at tick 60");
        for (int tick = 60; tick < 99; tick++) player.advanceAbilityTick();
        helper.assertTrue(player.getCooldowns().isOnCooldown(item), "Cooldown must still be active at tick 99");
        player.advanceAbilityTick();
        helper.assertTrue(!player.getCooldowns().isOnCooldown(item), "Cooldown must expire at tick 100");
        helper.succeed();
    }

    @GameTest(template="empty", timeoutTicks=40)
    public static void staff_handler(GameTestHelper helper) { assertHandler(helper, Fault.NONE); }

    @GameTest(template="empty", timeoutTicks=40)
    public static void staff_expiry(GameTestHelper helper) { assertExpiry(helper, false); }

    @GameTest(template="empty", required=false, timeoutTicks=40)
    public static void staff_refresh_negative(GameTestHelper helper) { assertHandler(helper, Fault.REFRESH_EFFECT); }

    @GameTest(template="empty", required=false, timeoutTicks=40)
    public static void staff_short_cooldown_negative(GameTestHelper helper) { assertExpiry(helper, true); }

    @GameTest(template="empty", required=false, timeoutTicks=40)
    public static void staff_damage_negative(GameTestHelper helper) { assertHandler(helper, Fault.ATTEMPT_DAMAGE); }

    /** All test-only instrumentation stays outside the production staff classes. */
    private static final class TickableStaffPlayer extends FakePlayer {
        int hurtAttempts;
        TickableStaffPlayer(ServerLevel level) {
            super(level, new GameProfile(UUID.randomUUID(), "StaffAssertions"));
        }
        @Override
        public boolean hurt(DamageSource source, float amount) {
            hurtAttempts++;
            return super.hurt(source, amount);
        }
        void advanceAbilityTick() {
            tickEffects();
            getCooldowns().tick();
        }
    }
}
