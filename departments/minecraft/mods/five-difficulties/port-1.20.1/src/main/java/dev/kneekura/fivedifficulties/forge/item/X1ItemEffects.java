package dev.kneekura.fivedifficulties.forge.item;

import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

import javax.annotation.Nullable;

/** Ports of the item-effect helpers in X1 {@code THKaguyaLib}. */
public final class X1ItemEffects {
    private X1ItemEffects() {}

    /**
     * itemEffectFollowUser: put the effect entity {@code length} ahead of the user at {@code angle} off its yaw
     * (yFollow: tilted by pitch and set 0.5 below the eyes; otherwise at feet + yOffset); motion is the user's
     * motion plus the jump.
     */
    public static void followUser(Entity item, @Nullable Entity user, double length, float angle, boolean yFollow,
                                  double yOffset) {
        if (user == null) return;
        double x, y, z;
        float yaw = user.getYRot(), pitch = user.getXRot();
        if (yFollow) {
            x = user.getX() - Math.sin((yaw + angle) / 180F * 3.141593F) * Math.cos(pitch / 180F * 3.141593F) * length;
            z = user.getZ() + Math.cos((yaw + angle) / 180F * 3.141593F) * Math.cos(pitch / 180F * 3.141593F) * length;
            y = user.getY() - Math.sin(pitch / 180F * 3.141593F) * length + (double) user.getEyeHeight() - 0.5D;
        } else {
            x = user.getX() - Math.sin((yaw + angle) / 180F * 3.141593F) * length;
            z = user.getZ() + Math.cos((yaw + angle) / 180F * 3.141593F) * length;
            y = user.getY() + yOffset;
        }
        var m = user.getDeltaMovement();
        item.setDeltaMovement(m.x + (x - item.getX()), m.y + (y - item.getY()), m.z + (z - item.getZ()));
        item.setPos(x, y, z);
    }

    public static void followUser(Entity item, @Nullable Entity user, double length, float angle) {
        followUser(item, user, length, angle, true, 0.0D);
    }

    /**
     * itemEffectFinish: the effect entity turns back into its item. A creative player gets nothing back;
     * another player gets it in the inventory (dropped at the entity when full); a dead or missing user
     * leaves it on the ground. The entity always disappears.
     */
    public static boolean itemEffectFinish(Entity itemEntity, @Nullable LivingEntity user, Item item, int damage) {
        if (itemEntity.level().isClientSide) return true;
        if (user != null) {
            if (user instanceof Player player) {
                if (player.getAbilities().instabuild) {
                    itemEntity.discard();
                    return true;
                }
                if (!player.getInventory().add(stack(item, damage))) {
                    drop(itemEntity, item, damage);
                    itemEntity.discard();
                    return true;
                }
            }
            if (user.isRemoved()) drop(itemEntity, item, damage); // 1.7.10 isDead
        } else {
            drop(itemEntity, item, damage);
        }
        itemEntity.discard();
        return true;
    }

    public static boolean itemEffectFinish(Entity itemEntity, @Nullable LivingEntity user, Item item) {
        return itemEffectFinish(itemEntity, user, item, 0);
    }

    private static ItemStack stack(Item item, int damage) {
        ItemStack s = new ItemStack(item);
        if (damage != 0) s.setDamageValue(damage);
        return s;
    }

    private static void drop(Entity at, Item item, int damage) {
        at.level().addFreshEntity(new ItemEntity(at.level(), at.getX(), at.getY(), at.getZ(), stack(item, damage)));
    }
}
