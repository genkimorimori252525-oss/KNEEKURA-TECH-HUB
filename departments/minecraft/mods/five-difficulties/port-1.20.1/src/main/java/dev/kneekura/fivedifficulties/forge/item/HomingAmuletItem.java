package dev.kneekura.fivedifficulties.forge.item;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1ShotData;
import dev.kneekura.fivedifficulties.core.x1.X1ShotPatterns;
import dev.kneekura.fivedifficulties.core.x1.X1ShotTables;
import dev.kneekura.fivedifficulties.forge.shot.X1ShotSpawner;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

/**
 * Literal port of X1 {@code ItemHomingAmulet} (damage 0 = homing, 1 = diffusion).
 *
 * X1 fires generic {@code EntityTHShot} amulets (FORM_AMULET with HOMING01 / DIFFUSION01) through
 * {@code THShotLib.createWideShot}; they are drawn by {@code RenderTHShot.renderAmuletShot}.
 * (Until P9 this item fired the port of {@code EntityHomingAmulet}, which X1 uses for the Houtou
 * item; that projectile stays registered for Houtou.)
 */
public final class HomingAmuletItem extends Item {
    private final boolean diffusion;

    public HomingAmuletItem(boolean diffusion, Properties properties) {
        super(properties);
        this.diffusion = diffusion;
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (level instanceof ServerLevel server) {
            X1ShotPatterns patterns = X1ShotSpawner.patterns(server, player);
            Vec3d pos = X1ShotSpawner.posLiving(player);
            Vec3d look = X1ShotSpawner.pure(player.getLookAngle());
            if (!diffusion) {
                if (player.isShiftKeyDown()) { // slow mode
                    X1ShotData shot = X1ShotData.shot(X1ShotTables.FORM_AMULET, X1ShotTables.RED, 1.0F, 8.0F, 0, 90,
                            X1ShotTables.HOMING01);
                    patterns.createWideShot(pos, look, 0F, 9999, 0.7D, 0.7D, 0.7D, Vec3d.ZERO, shot, 2, 20F, 0.5D, 0F);
                } else {
                    X1ShotData shot = X1ShotData.shot(X1ShotTables.FORM_AMULET, X1ShotTables.RED, 0.4F, 5.0F, 0, 90,
                            X1ShotTables.HOMING01);
                    patterns.createWideShot(pos, look, 0F, 9999, 0.7D, 0.7D, 0.7D, Vec3d.ZERO, shot, 5, 100F, 0.5D, 0F);
                }
            } else {
                X1ShotData shot = X1ShotData.shot(X1ShotTables.FORM_AMULET, X1ShotTables.BLUE, 1.0F, 8.0F, 0, 16,
                        X1ShotTables.DIFFUSION01);
                patterns.createWideShot(pos, look, 0F, 9999, 0.5D, 0.0D, -0.03D, Vec3d.ZERO, shot, 2, 60F, 0.5D, 0F);
            }
            float pitch = 0.4F / (player.getRandom().nextFloat() * 4.0F + 0.8F);
            level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.ARROW_SHOOT,
                    SoundSource.PLAYERS, 0.5F, pitch);
            stack.shrink(1); // X1 consumes one amulet on the server even in creative mode
        }
        return InteractionResultHolder.sidedSuccess(stack, level.isClientSide);
    }
}
