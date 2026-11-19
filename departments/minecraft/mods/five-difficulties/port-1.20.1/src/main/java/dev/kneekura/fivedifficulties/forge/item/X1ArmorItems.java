package dev.kneekura.fivedifficulties.forge.item;

import net.minecraft.client.model.HumanoidModel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.ArmorMaterial;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.UseAnim;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.item.enchantment.Enchantments;
import net.minecraft.world.level.Level;
import net.minecraftforge.client.extensions.common.IClientItemExtensions;

import java.util.function.Consumer;

/** Ports of the X1 armour (P16i). Each item's own durability (X1 setMaxDamage) overrides the material's. */
public final class X1ArmorItems {
    private X1ArmorItems() {}

    /** EnumHelper.addArmorMaterial(name, durability, {helmet, chest, legs, boots}, enchantability 0). */
    public record X1ArmorMaterial(String name, int[] reduction) implements ArmorMaterial {
        @Override public int getDurabilityForType(ArmorItem.Type type) { return 0; }
        @Override public int getDefenseForType(ArmorItem.Type type) { return reduction[type.ordinal()]; }
        @Override public int getEnchantmentValue() { return 0; }
        @Override public SoundEvent getEquipSound() { return SoundEvents.ARMOR_EQUIP_GENERIC; }
        @Override public Ingredient getRepairIngredient() { return Ingredient.EMPTY; }
        @Override public String getName() { return "five_difficulties_port:" + name; }
        @Override public float getToughness() { return 0F; }
        @Override public float getKnockbackResistance() { return 0F; }
    }

    public static final ArmorMaterial HINEZUMI = new X1ArmorMaterial("hinezumi", new int[] {1, 2, 2, 2});
    public static final ArmorMaterial MARISA = new X1ArmorMaterial("marisa", new int[] {1, 1, 1, 1});
    public static final ArmorMaterial SUWAKO = new X1ArmorMaterial("suwako", new int[] {1, 1, 1, 1});

    private static String tex(String name) {
        return "five_difficulties_port:textures/models/armor/" + name + ".png";
    }

    abstract static class X1Armor extends ArmorItem {
        X1Armor(ArmorMaterial material, Type type, Properties p) {
            super(material, type, p);
        }

        @Override
        public int getEnchantmentValue() {
            return 0;
        }

        @Override
        public boolean isBookEnchantable(ItemStack stack, ItemStack book) {
            return false;
        }
    }

    /**
     * ItemFireRatRobe (火鼠の皮衣, chest, unbreakable, glint): wearing it puts out the wearer's fire; held, a hit sets
     * the target on fire for 20 s and right-click guards (and puts out the user's fire) instead of putting it on.
     * An unenchanted robe gets Fire Protection V.
     */
    public static final class FireRatRobe extends X1Armor {
        public FireRatRobe(Properties p) {
            super(HINEZUMI, Type.CHESTPLATE, p.durability(0));
        }

        @Override
        public boolean isDamageable(ItemStack stack) {
            return false;
        }

        @Override
        public String getArmorTexture(ItemStack stack, Entity entity, EquipmentSlot slot, String type) {
            return tex("hinezumi_1");
        }

        @Override
        public boolean hurtEnemy(ItemStack stack, LivingEntity target, LivingEntity attacker) {
            target.setSecondsOnFire(20);
            return true;
        }

        @Override
        public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
            player.startUsingItem(hand);
            player.clearFire();
            return InteractionResultHolder.consume(player.getItemInHand(hand));
        }

        @Override
        public UseAnim getUseAnimation(ItemStack stack) {
            return UseAnim.BLOCK;
        }

        @Override
        public int getUseDuration(ItemStack stack) {
            return 72000;
        }

        @Override
        public void inventoryTick(ItemStack stack, Level level, Entity entity, int slot, boolean selected) {
            if (!stack.isEnchanted()) stack.enchant(Enchantments.FIRE_PROTECTION, 5);
        }

        @Override
        public void onArmorTick(ItemStack stack, Level level, Player player) {
            player.clearFire();
        }

        @Override
        public boolean isFoil(ItemStack stack) {
            return true;
        }
    }

    /** ItemMarisaHat (魔理沙の帽子, helmet, durability 40): pulls in item entities within 5 as if touched. */
    public static final class MarisaHat extends X1Armor {
        public MarisaHat(Properties p) {
            super(MARISA, Type.HELMET, p.durability(40));
        }

        @Override
        public String getArmorTexture(ItemStack stack, Entity entity, EquipmentSlot slot, String type) {
            return tex("marisa_hat");
        }

        @Override
        public void onArmorTick(ItemStack stack, Level level, Player player) {
            for (Entity e : level.getEntities(player, player.getBoundingBox().inflate(5.0D))) {
                if (e instanceof ItemEntity item) item.playerTouch(player);
            }
        }

        @Override
        public void initializeClient(Consumer<IClientItemExtensions> consumer) {
            consumer.accept(new IClientItemExtensions() {
                @Override
                public HumanoidModel<?> getHumanoidArmorModel(LivingEntity living, ItemStack stack, EquipmentSlot slot,
                                                              HumanoidModel<?> original) {
                    return slot == EquipmentSlot.HEAD ? dev.kneekura.fivedifficulties.forge.client.X1HatModels.marisa() : original;
                }
            });
        }
    }

    /**
     * ItemKappaCap (河童の帽子, helmet, durability 500): in water it speeds the wearer up ×1.2 (capped at 0.5) and
     * mends 3; wet on land it mends 1; dry it wears 1 a tick until damage 498, so it never breaks.
     */
    public static final class KappaCap extends X1Armor {
        public KappaCap(Properties p) {
            super(HINEZUMI, Type.HELMET, p.durability(500));
        }

        @Override
        public String getArmorTexture(ItemStack stack, Entity entity, EquipmentSlot slot, String type) {
            return tex("hinezumi_1");
        }

        @Override
        public void onArmorTick(ItemStack stack, Level level, Player player) {
            if (player.isInWater()) {
                var m = player.getDeltaMovement();
                double x = m.x * 1.2D, y = m.y > 0.0D ? m.y * 1.2D : m.y, z = m.z * 1.2D;
                double max = 0.5D;
                if (x > max) x = max;
                else if (x < -max) x = -max;
                if (y > max) y = max;
                if (z > max) z = max;
                else if (z < -max) z = -max;
                player.setDeltaMovement(x, y, z);
                if (stack.isDamaged()) stack.setDamageValue(stack.getDamageValue() - 3);
            } else if (player.isInWaterOrRain()) {
                stack.setDamageValue(stack.getDamageValue() - 1);
            } else if (stack.getDamageValue() < 498) {
                stack.setDamageValue(stack.getDamageValue() + 1);
            }
        }
    }

    /** ItemKerobou (ケロ帽, helmet, durability 620): an unenchanted hat gets Thorns X (held or worn). */
    public static final class Kerobou extends X1Armor {
        public Kerobou(Properties p) {
            super(SUWAKO, Type.HELMET, p.durability(620));
        }

        @Override
        public String getArmorTexture(ItemStack stack, Entity entity, EquipmentSlot slot, String type) {
            return tex("suwako_hat");
        }

        @Override
        public void inventoryTick(ItemStack stack, Level level, Entity entity, int slot, boolean selected) {
            if (!stack.isEnchanted()) stack.enchant(Enchantments.THORNS, 10);
        }

        @Override
        public void onArmorTick(ItemStack stack, Level level, Player player) {
            if (!stack.isEnchanted()) stack.enchant(Enchantments.THORNS, 10);
        }

        @Override
        public void initializeClient(Consumer<IClientItemExtensions> consumer) {
            consumer.accept(new IClientItemExtensions() {
                @Override
                public HumanoidModel<?> getHumanoidArmorModel(LivingEntity living, ItemStack stack, EquipmentSlot slot,
                                                              HumanoidModel<?> original) {
                    return slot == EquipmentSlot.HEAD ? dev.kneekura.fivedifficulties.forge.client.X1HatModels.suwako() : original;
                }
            });
        }
    }
}
