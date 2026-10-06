package dev.kneekura.fivedifficulties.forge.item;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.HomingAmuletContract;
import dev.kneekura.fivedifficulties.core.x1.HomingAmuletShotContract;
import dev.kneekura.fivedifficulties.core.x1.X1HomingMath;
import dev.kneekura.fivedifficulties.core.x1.X1WideShotGeometry;
import dev.kneekura.fivedifficulties.forge.entity.HomingAmuletProjectile;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

import java.util.List;

/** Red X1 Homing Amulet only; the old blue diffusion metadata variant is a later port target. */
public final class HomingAmuletItem extends Item {
    public HomingAmuletItem(Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        boolean focused = player.isShiftKeyDown();
        HomingAmuletShotContract contract = HomingAmuletContract.resolve(focused);

        if (!level.isClientSide) {
            Vec3 look = player.getLookAngle();
            Vec3d lookPure = new Vec3d(look.x, look.y, look.z).normalized();

            double originY = X1HomingMath.legacyShotOriginY(
                    player.getY(),
                    player.getEyeHeight(),
                    player.getXRot()
            );
            Vec3d origin = new Vec3d(player.getX(), originY, player.getZ());

            List<X1WideShotGeometry.Ray> rays = X1WideShotGeometry.create(
                    lookPure,
                    contract.shotCount(),
                    contract.totalSpreadDegrees(),
                    contract.spawnDistance(),
                    contract.baseAngleDegrees()
            );

            for (X1WideShotGeometry.Ray ray : rays) {
                Vec3d spawn = origin.add(ray.spawnOffset());
                Vec3d direction = ray.direction();
                HomingAmuletProjectile projectile = new HomingAmuletProjectile(
                        level,
                        player,
                        new Vec3(spawn.x(), spawn.y(), spawn.z()),
                        new Vec3(direction.x(), direction.y(), direction.z()),
                        focused
                );
                level.addFreshEntity(projectile);
            }

            float pitch = 0.4F / (player.getRandom().nextFloat() * 4.0F + 0.8F);
            level.playSound(
                    null,
                    player.getX(), player.getY(), player.getZ(),
                    SoundEvents.ARROW_SHOOT,
                    SoundSource.PLAYERS,
                    0.5F,
                    pitch
            );

            // X1 consumes one amulet on the logical server even in creative mode.
            stack.shrink(1);
        }

        return InteractionResultHolder.sidedSuccess(stack, level.isClientSide);
    }
}
