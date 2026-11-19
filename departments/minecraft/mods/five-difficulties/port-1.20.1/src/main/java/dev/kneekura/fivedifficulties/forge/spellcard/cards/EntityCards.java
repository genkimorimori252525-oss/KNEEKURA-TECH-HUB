package dev.kneekura.fivedifficulties.forge.spellcard.cards;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1ShotData;
import dev.kneekura.fivedifficulties.forge.PortRegistries;
import dev.kneekura.fivedifficulties.forge.entity.DanmakuCreeperEntity;
import dev.kneekura.fivedifficulties.forge.entity.MiniHakkeroEntity;
import dev.kneekura.fivedifficulties.forge.entity.MusouFuuinEntity;
import dev.kneekura.fivedifficulties.forge.entity.NuclearShotEntity;
import dev.kneekura.fivedifficulties.forge.entity.SakuyaTimeControllerEntity;
import dev.kneekura.fivedifficulties.forge.entity.SukimaEntity;
import dev.kneekura.fivedifficulties.forge.entity.THShotEntity;
import dev.kneekura.fivedifficulties.forge.spellcard.X1SpellCard;
import dev.kneekura.fivedifficulties.forge.timestop.SakuyaTimeStopRuntime;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.animal.Chicken;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.monster.Creeper;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

import java.time.LocalDate;

import static dev.kneekura.fivedifficulties.core.x1.X1ShotTables.*;
import static dev.kneekura.fivedifficulties.forge.shot.X1Danmaku.*;
import static dev.kneekura.fivedifficulties.forge.spellcard.cards.Specials.RAND;
import static dev.kneekura.fivedifficulties.forge.spellcard.cards.Specials.register;
import static dev.kneekura.fivedifficulties.forge.spellcard.cards.Specials.user;

/** X1 spell cards that spawn their own entities (P12), translated statement by statement. */
public final class EntityCards {
    private EntityCards() {}

    /** 霊符「夢想封印」 */
    public static final class MusouFuuin extends X1SpellCard {
        public MusouFuuin() {
            setNeedLevel(5);
            setEndTime(90);
            setRemoveTime(70);
            setOriginalUserName(REIMU);
        }

        @Override
        public void spellcard_main() {
            if (time % 2 == 0 && time >= 15 && time < 49 && user != null && target != null) {
                world.addFreshEntity(new MusouFuuinEntity(world, user, pos_User(), angle(time * 33F, 0F), 0F,
                        rotate_Default(), 0F, 9999, 2.0D, 0.0D, -0.1D, gravity_Zero(), 2.0F, 9.0F, target));
            }
        }

        @Override
        public int getSpellCardCircleColor() {
            return RAINBOW;
        }
    }

    /** 恋符「マスタースパーク」 */
    public static final class MasterSpark extends X1SpellCard {
        private Vec3d tgVec;

        public MasterSpark() {
            setNeedLevel(5);
            setRemoveTime(99);
            setEndTime(109);
            setOriginalUserName(MARISA);
        }

        @Override
        public void spellcard_main() {
            if (time == 1) {
                tgVec = lookVec();
                world.addFreshEntity(new MiniHakkeroEntity(world, user, target));
            }
            if (time >= 30 && time < 99) {
                float cy = card.getYRot(), cp = card.getXRot();
                // X1 overwrites tgVec in place; rotateAroundY(2π) is the identity with the 1.7.10 sine table.
                double lookX = -Mth.sin(cy / 180F * 3.141593F) * Mth.cos((cp + 90F) / 180F * 3.141593F);
                double lookZ = Mth.cos(cy / 180F * 3.141593F) * Mth.cos((cp + 90F) / 180F * 3.141593F);
                tgVec = new Vec3d(lookX, -Mth.sin((cp + 90F) / 180F * 3.141593F), lookZ);
                float angle = (float) time * 6F;
                float angleSpan = 360F / 7F;
                double gRate = 0.034 + 0.03D * Math.sin(angle / 180F * 3.141593F);
                double xG = -Mth.sin(cy / 180F * 3.141593F) * Mth.cos(cp / 180F * 3.141593F) * gRate;
                double yG = -Mth.sin(cp / 180F * 3.141593F) * gRate;
                double zG = Mth.cos(cy / 180F * 3.141593F) * Mth.cos(cp / 180F * 3.141593F) * gRate;
                for (int i = 0; i < 7; i++) {
                    double angleXZ = angle;
                    double angleY = 0;
                    double x1 = Math.sin(angleXZ / 180.0F * Math.PI) * Math.cos(cy / 180.0F * Math.PI);
                    double z1 = Math.sin(angleXZ / 180.0F * Math.PI) * Math.sin(cy / 180.0F * Math.PI);
                    double x2 = Math.cos(angleXZ / 180.0F * Math.PI) * Math.sin(angleY / 180.0F * Math.PI)
                            * Math.sin((cp + 90F) / 180.0F * Math.PI) * Math.sin(cy / 180.0F * Math.PI);
                    double z2 = Math.cos(angleXZ / 180.0F * Math.PI) * Math.sin(angleY / 180.0F * Math.PI)
                            * Math.sin((cp + 90F) / 180.0F * Math.PI) * Math.cos(cy / 180.0F * Math.PI);
                    double yVector = -Math.cos(angleXZ / 180.0F * Math.PI) * Math.sin((cp + 90F - angleY) / 180.0F * Math.PI);
                    double xVector = Math.cos(angleXZ / 180.0F * Math.PI) * Math.cos(angleY / 180.0F * Math.PI) * tgVec.x() + x1 - x2;
                    double zVector = Math.cos(angleXZ / 180.0F * Math.PI) * Math.cos(angleY / 180.0F * Math.PI) * tgVec.z() + z1 + z2;
                    X1ShotData shot = X1ShotData.shot(FORM_STAR, time % 7, 0.4F, 8.0F, 0, 55);
                    createShot(user, card, pos_Card(), angle(xVector, yVector, zVector), 0F, 0.2D, 0.3D, 0.05D,
                            gravity(xG, yG, zG), shot);
                    angle += angleSpan;
                }
            }
        }
    }

    /** メイド秘技「殺人ドール」 */
    public static final class SatuzinDoll extends X1SpellCard {
        public SatuzinDoll() {
            setNeedLevel(4);
            setRemoveTime(30);
            setEndTime(110);
            setOriginalUserName(SAKUYA);
        }

        @Override
        public void spellcard_main() {
            if (time < 5) return;
            if (time < 15) {
                createSphereShot(user, user, pos_User(), lookVec(), 0F, rotate_Default(), 0F, 9999, 0.4D, 0.4D, 0.0D,
                        gravity_Zero(), shot(FORM_KNIFE, BLUE, SIZE[FORM_KNIFE], 12.0F, 3, 80), 32, 1.0D, time * 6F);
            }
            if (time > 14 && time < 24 && time % 4 == 0) {
                int way = 9;
                float angleXZ = userYaw();
                float angleY = userPitch();
                createCircleShot(user, user, pos_User(), getVecFromAngle(angleXZ, angleY), 0.4D, 0.4D, 0.0D,
                        gravity_Zero(), shot(FORM_KNIFE, RED, SIZE[FORM_KNIFE], 12.0F, 3, 80), way, 1.0D, 0F);
                createCircleShot(user, user, pos_User(), getVecFromAngle(angleXZ + 5F, angleY), 0.4D, 0.4D, 0.0D,
                        gravity_Zero(), shot(FORM_KNIFE, RED, SIZE[FORM_KNIFE], 12.0F, 3, 80), way, 1.0D, 0F);
            }
            if (time == 36) {
                boolean flag = true;
                for (SakuyaTimeControllerEntity watch : world.getEntitiesOfClass(SakuyaTimeControllerEntity.class,
                        card.getBoundingBox().inflate(20.0D))) {
                    if (watch.getSourceEntity() == user) flag = false;
                }
                // new EntitySakuyaWatch(world, user, TIME_STOP_IN_SPELLCARD)
                if (flag) SakuyaTimeStopRuntime.startSpellCardX1(world, user);
            }
        }

        /** Runs only while the card is inside its user's time stop. */
        @Override
        public void specialProcessInTimeStop() {
            super.specialProcessInTimeStop();
            if (time > 44 && time < 68 && time % 8 == 3) {
                for (THShotEntity s : world.getEntitiesOfClass(THShotEntity.class, card.getBoundingBox().inflate(20.0D))) {
                    if (s.getShotForm() == FORM_KNIFE && (s.getShotColor() == BLUE || s.getShotColor() == RED)
                            && s.getOwner() == user && rand.nextInt(100) < 25) {
                        Vec3d angle = target != null ? angle_ToPos(pos_Entity(s), pos_Target()) : angle_Random();
                        createShot(user, user, pos(s.getX(), s.getY() - ((double) user.getEyeHeight() - 0.25D), s.getZ()),
                                angle, 0F, 0.2D + rand.nextDouble() * 0.5D, 0.7D, 0.02D, gravity_Zero(),
                                shot(FORM_KNIFE, GREEN, SIZE[FORM_KNIFE], 12.0F, 0, 80));
                        s.discard();
                    }
                }
            }
        }

        @Override
        public boolean canMoveInTimeStop() {
            return true;
        }
    }

    /** 幻巣「飛光虫ネスト」 */
    public static final class HikouchuuNest extends X1SpellCard {
        public HikouchuuNest() {
            setNeedLevel(4);
            setRemoveTime(50);
            setEndTime(160);
            setOriginalUserName(YUKARI);
        }

        @Override
        public void spellcard_main() {
            boolean flag = false;
            int count = 0;
            while (!flag && count < 4) {
                double length = rand.nextDouble() * 5.0D + 1.0D;
                float angleXZ = (card.getYRot() + 90F) / 180F * (float) Math.PI + rand.nextFloat() * (float) Math.PI;
                float angleY = rand.nextFloat() * (float) Math.PI - (float) Math.PI / 2.0F;
                double xVector = Math.sin(angleXZ) * Math.cos(angleY) * length;
                double yVector = Math.sin(angleY) * length;
                double zVector = Math.cos(angleXZ) * Math.cos(angleY) * length;
                // func_147447_a(start, end, false, true, true): from the user's feet, solid blocks only.
                Vec3 start = new Vec3(user.getX(), user.getY(), user.getZ());
                Vec3 end = start.add(xVector, yVector, zVector);
                if (world.clip(new ClipContext(start, end, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, user))
                        .getType() != HitResult.Type.MISS) {
                    count++;
                } else {
                    world.addFreshEntity(new SukimaEntity(world, user, end.x, end.y, end.z, userYaw(), 17));
                    flag = true;
                }
            }
        }
    }

    /** 奇跡「ファフロッキーズの奇跡」 */
    public static final class Fafrotskies extends X1SpellCard {
        public static final int SPECIAL_FAFUROTSKIES01 = 1500;
        /** World.getCurrentDate (the real clock); the runtime scenario swaps it to reach the dated branches. */
        public static java.util.function.Supplier<LocalDate> today = LocalDate::now;

        public Fafrotskies() {
            setNeedLevel(1);
            setRemoveTime(20);
            setEndTime(40);
            setOriginalUserName(SANAE);
        }

        @Override
        public void registerSpecialShots() {
            register(SPECIAL_FAFUROTSKIES01, (shot, m, id) -> {
                if (shot.tickCount != shot.getShotEndTime()) return;
                int pattern = (int) m.limitSpeed; // the card hides its roll in limitSpeed
                Level level = shot.level();
                LivingEntity shotUser = user(shot);
                LocalDate date = today.get();
                if (date.getMonthValue() == 12 && date.getDayOfMonth() == 25) {
                    DanmakuCreeperEntity creeper = PortRegistries.DANMAKU_CREEPER.get().create(level);
                    creeper.moveTo((int) shot.getX(), (int) shot.getY(), (int) shot.getZ(), RAND.nextFloat() * 360F, 0.0F);
                    level.addFreshEntity(creeper);
                    shot.discard();
                    return;
                }
                if (date.getMonthValue() == 1 && date.getDayOfMonth() >= 1 && date.getDayOfMonth() <= 3) {
                    if (shotUser == null) return;
                    NuclearShotEntity nuclear = new NuclearShotEntity(level, shotUser, pos(shot.getX(), shot.getY(), shot.getZ()),
                            angle_Random(RAND), 0.0F, rotate_Default(), 0.0F, 9999, 0.2D, 0.8D, 0.00D, gravity_Default(),
                            X1ShotData.shot(0, RAND.nextInt(7), 3.2F, 10.0F, 0, 70, 0));
                    nuclear.shootingFlag = true;
                    level.addFreshEntity(nuclear);
                    shot.discard();
                    return;
                }
                if (pattern <= 70) {
                    if (shotUser != null) {
                        for (int i = 0; i < 8; i++) {
                            X1ShotData knife = X1ShotData.shot(FORM_KNIFE, RANDOM, 0.6F, 10.0F, 3, 120);
                            createShot(shotUser, shot, pos_Entity(shot), angle(RAND.nextFloat() * 360F, RAND.nextFloat() * 180 - 90F),
                                    0F, 0.6D, 0.6D, 0.0D, gravity_Default(), knife);
                        }
                    }
                    shot.discard();
                } else if (pattern <= 80) {
                    level.addFreshEntity(new ItemEntity(level, shot.getX(), shot.getY(), shot.getZ(), new ItemStack(Items.COD)));
                    shot.discard();
                } else if (pattern <= 90) {
                    Creeper creeper = EntityType.CREEPER.create(level);
                    creeper.moveTo((int) shot.getX(), (int) shot.getY(), (int) shot.getZ(), RAND.nextFloat() * 360F, 0.0F);
                    level.addFreshEntity(creeper);
                    shot.discard();
                } else {
                    Chicken chicken = EntityType.CHICKEN.create(level);
                    chicken.moveTo((int) shot.getX(), (int) shot.getY(), (int) shot.getZ(), RAND.nextFloat() * 360F, 0.0F);
                    level.addFreshEntity(chicken);
                    shot.discard();
                }
            }, null, null);
        }

        @Override
        public void spellcard_main() {
            if (time == 1) {
                int pattern = rand.nextInt(100);
                for (int i = 0; i < 10; i++) {
                    Vec3d angle = getVecFromAngle(userYaw() + rand.nextFloat() * 50F - 25F, rand.nextFloat() * 20F - 69F);
                    Vec3d angle2 = angle(userYaw(), 0.0F);
                    Vec3d from = pos_User();
                    Vec3d at = pos(from.x() + angle2.x() * 0.5D, from.y() + angle2.y() * 0.5D, from.z() + angle2.z() * 0.5D);
                    createShot(user, user, at, angle, 0F, 1.2D, pattern, 0.0D, gravity_Default(),
                            shot(FORM_CIRCLE, AQUA, 0.4F, 6.0F, i, 20, SPECIAL_FAFUROTSKIES01));
                }
                playShotSound(user);
            }
        }
    }
}
