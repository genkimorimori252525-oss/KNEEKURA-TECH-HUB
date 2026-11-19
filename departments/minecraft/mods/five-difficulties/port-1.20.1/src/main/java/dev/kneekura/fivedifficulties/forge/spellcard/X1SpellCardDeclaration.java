package dev.kneekura.fivedifficulties.forge.spellcard;

import dev.kneekura.fivedifficulties.forge.PortRegistries;
import dev.kneekura.fivedifficulties.forge.entity.SpellCardEntity;
import dev.kneekura.fivedifficulties.forge.shot.X1Danmaku;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.npc.Villager;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

import java.util.Optional;
import java.util.function.Supplier;

/** Port of THKaguyaLib.checkSpellCardDeclaration / spellCardDeclaration. */
public final class X1SpellCardDeclaration {
    /** DanmakuConstants.NORMAL: players always declare at level 2. */
    public static final int NORMAL = 2;
    /** Bomb item (P14); while it is not ported, no bombs are counted. */
    public static Supplier<Item> bombItem = () -> null;

    private X1SpellCardDeclaration() {}

    private static float rad(float deg) {
        return deg / 180F * (float) Math.PI;
    }

    /**
     * Declares spell card {@code number} for {@code user} at a living target within 32 blocks of its
     * line of sight. Returns true when a card was declared.
     */
    public static boolean check(ServerLevel world, ItemStack stack, LivingEntity user, int number, int level,
                                boolean firstAttack) {
        int needLevel = 0;
        if (user instanceof Player player && !player.getAbilities().instabuild) {
            if (stack.getItem() instanceof SpellCardItem && number >= 14 && number <= 18) {
                CompoundTag nbt = stack.getTag();
                if (nbt == null || nbt.getInt("Charge") <= 0) return false;
            }
            X1SpellCardRegistry.Entry entry = X1SpellCardRegistry.get(number);
            if (entry != null) needLevel = entry.create().getNeedLevel();
            if (player.experienceLevel + countBombs(player) < needLevel) return false;
        }

        double angleX = -Math.sin(rad(user.getYRot())) * Math.cos(rad(user.getXRot()));
        double angleY = -Math.sin(rad(user.getXRot()));
        double angleZ = Math.cos(rad(user.getYRot())) * Math.cos(rad(user.getXRot()));
        Vec3 start = new Vec3(user.getX(), user.getY() + user.getEyeHeight(), user.getZ());
        // X1 quirk: the far end is measured from the feet, not the eyes.
        Vec3 end = new Vec3(user.getX() + angleX * 32.0D, user.getY() + angleY * 32.0D, user.getZ() + angleZ * 32.0D);
        BlockHitResult block = world.clip(new ClipContext(start, end, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, user));
        if (block.getType() != HitResult.Type.MISS) end = block.getLocation();

        LivingEntity hit = null;
        double nearDistance = 0.0D;
        AABB search = user.getBoundingBox().expandTowards(angleX * 32.0D, angleY * 32.0D, angleZ * 32.0D).inflate(1.0D);
        for (Entity e : world.getEntities(user, search)) {
            if (!(e instanceof LivingEntity living) || e instanceof Animal || e instanceof Villager) continue;
            Optional<Vec3> intercept = e.getBoundingBox().inflate(0.3F).clip(start, end);
            if (intercept.isEmpty()) continue;
            double distance = start.distanceTo(intercept.get());
            if (distance < nearDistance || nearDistance == 0.0D) {
                hit = living;
                nearDistance = distance;
            }
        }
        for (SpellCardEntity active : world.getEntitiesOfClass(SpellCardEntity.class, user.getBoundingBox().inflate(64.0D))) {
            if (active.user == user) return false;
        }
        if (hit == null) return false;
        declare(world, user, hit, number, needLevel, level, firstAttack);
        return true;
    }

    private static int countBombs(Player player) {
        Item bomb = bombItem.get();
        if (bomb == null) return 0;
        int n = 0;
        for (ItemStack s : player.getInventory().items) if (s.is(bomb)) n += s.getCount();
        return n;
    }

    /** spellCardDeclaration. */
    public static void declare(ServerLevel world, LivingEntity user, LivingEntity target, int number, int needLevel,
                               int level, boolean firstAttack) {
        SpellCardEntity card = new SpellCardEntity(world, user, target, number, level);
        world.addFreshEntity(card);
        Component name = Component.translatable("item.thSpellCard." + number + ".name");
        if (user instanceof Player player) {
            player.sendSystemMessage(name);
            world.playSound(null, player.getX(), player.getY(), player.getZ(), PortRegistries.SOUND_SPELLCARD.get(),
                    SoundSource.PLAYERS, dev.kneekura.fivedifficulties.forge.X1Config.spellCardVol(), 1.0F);
            int bomb = 0;
            Item bombItemType = bombItem.get();
            while (bombItemType != null && bomb < needLevel && consumeOne(player, bombItemType)) bomb++;
            player.giveExperienceLevels(bomb - needLevel);
        }
        if (target instanceof Player targetPlayer && firstAttack) {
            targetPlayer.sendSystemMessage(name);
            world.playSound(null, targetPlayer.getX(), targetPlayer.getY(), targetPlayer.getZ(),
                    PortRegistries.SOUND_SPELLCARD.get(), SoundSource.PLAYERS, dev.kneekura.fivedifficulties.forge.X1Config.spellCardVol(), 1.0F);
        }
        if (firstAttack) X1Danmaku.danmakuRemove(user, 40.0F, "Enemy", true);
    }

    private static boolean consumeOne(Player player, Item item) {
        for (ItemStack s : player.getInventory().items) {
            if (s.is(item)) {
                s.shrink(1);
                return true;
            }
        }
        return false;
    }
}
