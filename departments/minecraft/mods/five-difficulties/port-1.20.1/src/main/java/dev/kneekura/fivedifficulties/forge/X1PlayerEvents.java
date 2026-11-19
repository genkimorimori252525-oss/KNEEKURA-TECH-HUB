package dev.kneekura.fivedifficulties.forge;

import dev.kneekura.fivedifficulties.core.x1.X1ShotTables;
import dev.kneekura.fivedifficulties.forge.entity.SpellCardCircleEntity;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.event.entity.living.LivingDeathEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/** Ports of X1 {@code THKaguyaPlayerDeathEventHandler} and {@code THKaguyaLib.getPlayerPower}. */
@Mod.EventBusSubscriber(modid = FiveDifficultiesPort.MOD_ID, bus = Mod.EventBusSubscriber.Bus.FORGE)
public final class X1PlayerEvents {
    private X1PlayerEvents() {}

    /** getPlayerPower: small power items count 1, big ones 10, over the main inventory; at most 400. */
    public static float getPlayerPower(Player player) {
        float power = 0.0F;
        for (ItemStack s : player.getInventory().items) {
            if (s.is(PortRegistries.POWER_ITEM_SMALL.get())) power += 1.0F * s.getCount();
            else if (s.is(PortRegistries.POWER_ITEM_BIG.get())) power += 10.0F * s.getCount();
        }
        return Math.min(power, 400.0F);
    }

    /**
     * Every dying player plays "down". With an extend item in the main inventory, one is used, the player
     * is healed to full and gets 100 ticks of invulnerability inside a purple spell-card circle.
     * X1 does not cancel the 1.7.10 death event, so onDeath still ran (death message, inventory drop)
     * on a fully healed player; the port cancels the death, which is what the extend is for.
     */
    @SubscribeEvent
    public static void onLivingDeath(LivingDeathEvent event) {
        if (event.getEntity().level().isClientSide || !(event.getEntity() instanceof Player player)) return;
        player.level().playSound(null, player.getX(), player.getY(), player.getZ(), PortRegistries.SOUND_DOWN.get(),
                SoundSource.PLAYERS, X1Config.downVol(), 1.0F);
        for (ItemStack s : player.getInventory().items) {
            if (s.is(PortRegistries.EXTEND_ITEM.get())) {
                s.shrink(1);
                player.invulnerableTime = 100;
                player.setHealth(player.getMaxHealth());
                player.level().addFreshEntity(new SpellCardCircleEntity(player.level(), player, X1ShotTables.PURPLE,
                        player.invulnerableTime));
                event.setCanceled(true);
                break;
            }
        }
    }
}
