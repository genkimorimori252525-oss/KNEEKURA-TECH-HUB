package dev.kneekura.fivedifficulties.forge.item;

import dev.kneekura.fivedifficulties.forge.entity.DivineSpiritEntity;
import dev.kneekura.fivedifficulties.forge.entity.mob.THFairyEntity;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MobType;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.animal.WaterAnimal;
import net.minecraft.world.entity.monster.Creeper;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.npc.AbstractVillager;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.SwordItem;
import net.minecraft.world.item.Tiers;
import net.minecraft.world.item.UseAnim;
import net.minecraft.world.item.enchantment.Enchantment;
import net.minecraft.world.level.Level;

import java.util.List;

/**
 * Port of X1 {@code ItemMikoSword} (豊聡耳の宝剣): an iron sword that cannot be enchanted. Hold right-click (it
 * blocks like a 1.7.10 sword) and release: the up to ten nearest living things within (ticks held, at most 50)
 * each leave a Divine Spirit at their eyes, coloured by kind; unless sneaking, each is also reported in chat
 * (number, name, direction, up / down, distance) coloured by monster / animal / other. The sword takes one damage
 * per spirit (not in creative), with no break until the next right-click finds it at or past its maximum.
 * X1 quirk kept: the ±180° wrap after computing a target's bearing adjusts the player's angle, not the bearing.
 */
public class MikoSwordItem extends SwordItem {
    public MikoSwordItem(Properties properties) {
        super(Tiers.IRON, 3, -2.4F, properties);
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        player.startUsingItem(hand);
        if (stack.getDamageValue() >= stack.getMaxDamage()) stack.shrink(1);
        return InteractionResultHolder.consume(stack);
    }

    @Override
    public int getUseDuration(ItemStack stack) { return 72000; }

    @Override
    public UseAnim getUseAnimation(ItemStack stack) { return UseAnim.BLOCK; }

    @Override
    public void releaseUsing(ItemStack stack, Level level, LivingEntity living, int timeLeft) {
        if (living instanceof Player player) release(stack, level, player, timeLeft);
    }

    /** onPlayerStoppedUsing; public for the scenario. Returns how many spirits were made. */
    public static int release(ItemStack stack, Level level, Player player, int usedTime) {
        Entity[] nearEntitys = new Entity[11];
        double[] nearDistance = new double[11];
        double recognizeDistance = 72000 - usedTime;
        if (recognizeDistance > 50D) recognizeDistance = 50D;
        for (int i = 0; i < 11; i++) {
            nearEntitys[i] = null;
            nearDistance[i] = 999.9D;
        }
        List<Entity> list = level.getEntities(player, player.getBoundingBox().inflate(recognizeDistance));
        for (Entity e : list) {
            double distance = player.distanceTo(e);
            if (e instanceof LivingEntity) {
                int n = 0;
                boolean flag = false;
                while (n < 10 && !flag) {
                    if (nearDistance[n] > distance) {
                        for (int k = 10; k > n; k--) {
                            nearEntitys[k] = nearEntitys[k - 1];
                            nearDistance[k] = nearDistance[k - 1];
                        }
                        nearEntitys[n] = e;
                        nearDistance[n] = distance;
                        flag = true;
                    }
                    n++;
                }
            }
        }
        float angle = (360F - player.getYRot()) % 360F;
        if (angle < -180F) angle += 360F;
        if (angle > 180F) angle -= 360F;
        int i = 0;
        while (i < 10 && nearEntitys[i] != null) {
            Entity near = nearEntitys[i];
            int color = colorOf(near, level);
            if (!level.isClientSide) {
                level.addFreshEntity(new DivineSpiritEntity(level, near.getX(), near.getY() + near.getEyeHeight(), near.getZ(), color));
            }
            if (!player.isShiftKeyDown()) {
                double dx = near.getX() - player.getX();
                double dz = near.getZ() - player.getZ();
                float angle2 = ((float) Math.atan2(dx, dz) / 3.141593F * 180F) % 360F;
                if (angle2 < -180F) angle += 360F;
                if (angle2 > 180F) angle -= 360F;
                angle2 -= angle;
                String pos = angle2 < -135F || angle2 > 135F ? "back" : angle2 < -45F ? "right" : angle2 < 45F ? "front" : "left";
                String upDown = player.getY() > near.getY() + 3.0D ? "down" : player.getY() < near.getY() - 3.0D ? "up" : null;
                ChatFormatting fmt = near instanceof Monster ? ChatFormatting.DARK_RED : near instanceof Animal ? ChatFormatting.GREEN
                        : ChatFormatting.DARK_AQUA;
                int num = i + 1;
                String strNum = num + ". ";
                if (num != 10) strNum = " " + strNum;
                MutableComponent line = Component.literal(strNum).withStyle(fmt).append(near.getDisplayName()).append(" ")
                        .append(Component.translatable("five_difficulties_port.direction." + pos)).append(" ");
                if (upDown != null) line.append(Component.translatable("five_difficulties_port.direction." + upDown));
                line.append("  " + (int) nearDistance[i] + "m" + "  ");
                if (!level.isClientSide) player.sendSystemMessage(line);
            }
            i++;
        }
        if (!player.getAbilities().instabuild) stack.setDamageValue(stack.getDamageValue() + i);
        return i;
    }

    /** The spirit colour by kind (X1 order of checks). */
    static int colorOf(Entity near, Level level) {
        if (near instanceof THFairyEntity) {
            int r = level.random.nextInt(100);
            return r < 85 ? 1 : r < 95 ? 2 : 4;
        }
        if (near instanceof Creeper) return 2;
        if (near instanceof AbstractVillager) return 1;
        if (near instanceof Animal) return near instanceof TamableAnimal t && t.isTame() ? 4 : 3;
        if (near instanceof WaterAnimal) return 5;
        if (near instanceof LivingEntity living) {
            if (living.getMobType() == MobType.UNDEAD) return 7;
            if (living.getMobType() == MobType.ARTHROPOD) return 6;
        }
        return 0;
    }

    @Override
    public int getEnchantmentValue() { return 0; }

    @Override
    public boolean isBookEnchantable(ItemStack stack, ItemStack book) { return false; }

    @Override
    public boolean canApplyAtEnchantingTable(ItemStack stack, Enchantment enchantment) { return false; }
}
