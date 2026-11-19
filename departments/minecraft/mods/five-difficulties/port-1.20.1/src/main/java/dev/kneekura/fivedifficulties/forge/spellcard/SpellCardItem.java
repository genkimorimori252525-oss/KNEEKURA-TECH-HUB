package dev.kneekura.fivedifficulties.forge.spellcard;

import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import org.jetbrains.annotations.Nullable;

import java.util.List;

/**
 * Port of X1 {@code ItemTHSpellCard}. X1 used one item whose damage value is the spell card ID;
 * here each registered card is its own item carrying that ID.
 */
public final class SpellCardItem extends Item {
    private final int number;

    public SpellCardItem(int number, Properties properties) {
        super(properties.stacksTo(1));
        this.number = number;
    }

    public int number() {
        return number;
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (level instanceof ServerLevel server) {
            X1SpellCardDeclaration.check(server, stack, player, number, X1SpellCardDeclaration.NORMAL, true);
        }
        return InteractionResultHolder.pass(stack);
    }

    /** ItemTHSpellCard.onUpdate: the miracle cards' Charge counts down every tick. */
    @Override
    public void inventoryTick(ItemStack stack, Level level, Entity entity, int slot, boolean selected) {
        CompoundTag nbt = stack.getTag();
        if (nbt == null) return;
        int charge = nbt.getInt("Charge");
        if (charge > 1) nbt.putInt("Charge", charge - 1);
        else nbt.remove("Charge");
    }

    public int needLevel() {
        X1SpellCardRegistry.Entry entry = X1SpellCardRegistry.get(number);
        return entry == null ? 1 : entry.create().getNeedLevel();
    }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> list, TooltipFlag flag) {
        list.add(Component.literal("Lv." + needLevel() + " Spell Card"));
        if (number >= 14 && number <= 18) {
            int charge = stack.getTag() == null ? 0 : stack.getTag().getInt("Charge");
            int lv = 20 - ((14 - number) * 5);
            list.add(Component.translatable("thKaguya.msg.sneSc1").append(String.valueOf(lv))
                    .append(Component.translatable("thKaguya.msg.sneSc2")).append(String.valueOf(number - 13))
                    .append(Component.translatable("thKaguya.msg.sneSc3")));
            list.add(Component.translatable("thKaguya.msg.sneSc4").append(charge / 10 + "%"));
        }
    }

    @Override
    public boolean isFoil(ItemStack stack) {
        return number >= 14 && number <= 18 && stack.getTag() != null && stack.getTag().getInt("Charge") > 0;
    }

    @Override
    public Component getName(ItemStack stack) {
        return Component.translatable("item.thSpellCard." + number + ".name");
    }
}
