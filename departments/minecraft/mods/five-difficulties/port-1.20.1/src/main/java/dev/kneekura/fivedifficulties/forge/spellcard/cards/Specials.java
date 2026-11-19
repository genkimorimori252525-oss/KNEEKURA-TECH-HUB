package dev.kneekura.fivedifficulties.forge.spellcard.cards;

import dev.kneekura.fivedifficulties.core.x1.X1ShotMotion;
import dev.kneekura.fivedifficulties.forge.PortRegistries;
import dev.kneekura.fivedifficulties.forge.entity.THShotEntity;
import dev.kneekura.fivedifficulties.forge.shot.X1SpecialShotRegistry;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.BlockHitResult;

import java.util.Random;

/** Lambda-friendly registration of X1 ISpecialShot handlers for the spell cards. */
final class Specials {
    /** X1 cards use their own Random for special shots. */
    static final Random RAND = new Random();

    interface Move { void move(THShotEntity shot, X1ShotMotion m, int id); }
    interface HitBlock { boolean hit(THShotEntity shot, X1ShotMotion m, int id, BlockHitResult hit); }
    interface HitEntity { boolean hit(THShotEntity shot, X1ShotMotion m, int id, Entity hit); }

    private Specials() {}

    static void register(int id, Move move, HitBlock block, HitEntity entity) {
        X1SpecialShotRegistry.register(new X1SpecialShotRegistry.SpecialShot() {
            @Override public void move(THShotEntity shot, X1ShotMotion m, int i) { if (move != null) move.move(shot, m, i); }
            @Override public boolean hitBlock(THShotEntity shot, X1ShotMotion m, int i, BlockHitResult hit) {
                return block != null && block.hit(shot, m, i, hit);
            }
            @Override public boolean hitEntity(THShotEntity shot, X1ShotMotion m, int i, Entity hit) {
                return entity != null && entity.hit(shot, m, i, hit);
            }
        }, id);
    }

    /** shot.user */
    static LivingEntity user(THShotEntity shot) {
        return shot.getOwner() instanceof LivingEntity l ? l : null;
    }

    /** "thKaguyaMod.masterspark" (X1 ships no audio for it, so this is silent as in X1). */
    static void playMasterSpark(LivingEntity user) {
        user.level().playSound(null, user.getX(), user.getY(), user.getZ(), PortRegistries.SOUND_MASTERSPARK.get(),
                SoundSource.PLAYERS, 1.0F, 1.0F);
    }
}
