package dev.kneekura.fivedifficulties.forge.spellcard.cards;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1LaserData;
import dev.kneekura.fivedifficulties.core.x1.X1ShotData;
import dev.kneekura.fivedifficulties.forge.entity.THShotEntity;
import dev.kneekura.fivedifficulties.forge.spellcard.X1SpellCard;
import net.minecraft.util.Mth;

import static dev.kneekura.fivedifficulties.core.x1.X1ShotTables.*;
import static dev.kneekura.fivedifficulties.forge.shot.X1Danmaku.*;

/**
 * X1 spell cards that only use shots and lasers, translated statement by statement
 * (class name = X1 THSC_ class). X1 user.rotationYaw / rotationPitch read as userYaw() / userPitch().
 */
public final class SimpleCards {
    private SimpleCards() {}

    /** 祟符「ミシャグジさま」 */
    public static final class Mishagujisama extends X1SpellCard {
        public Mishagujisama() {
            setNeedLevel(3);
            setRemoveTime(20);
            setEndTime(90);
            setOriginalUserName(SUWAKO);
        }

        @Override
        public void spellcard_main() {
            if (time % 9 == 3) {
                float angleBase = rand.nextFloat() * 360F;
                Vec3d angle = getVecFromAngle(userYaw(), 0F, 1.0D);
                Vec3d pos = pos(user.getX(), user.getY() + 0.2D, user.getZ());
                createCircleShot(user, user, pos, angle, 1.2F, 30, 1.9D, 0.2D, -0.15D, gravity_Zero(),
                        shot(FORM_RICE, GREEN, SIZE[FORM_RICE], 7.0F, 3, 120), 32, 0.7D, angleBase);
                createCircleShot(user, user, pos, angle, -1.2F, 30, 1.9D, 0.2D, -0.15D, gravity_Zero(),
                        shot(FORM_RICE, GREEN, SIZE[FORM_RICE], 7.0F, 3, 120), 32, 0.7D, angleBase);
            }
        }
    }

    /** 神槍「スピア・ザ・グングニル」: the card itself has no pattern in X1. */
    public static final class SpearTheGungnir extends X1SpellCard {
        public SpearTheGungnir() {
            setNeedLevel(3);
            setRemoveTime(10);
            setEndTime(50);
            setOriginalUserName(REMILIA);
        }
    }

    /** 「全人類の緋想天」: X1 only registers its special shot; the card fires nothing. */
    public static final class ZenzinruiNoHisouten extends X1SpellCard {
        public static final int SPECIAL_HISOUTEN01 = 700;

        public ZenzinruiNoHisouten() {
            setNeedLevel(5);
            setRemoveTime(30);
            setEndTime(150);
            setOriginalUserName(TENSHI);
        }

        @Override
        public void registerSpecialShots() {
            Specials.register(SPECIAL_HISOUTEN01, (shot, m, id) -> {
                if (shot.tickCount < 20) shot.setShotSize(shot.getShotSize() + 0.1F);
            }, (shot, m, id, hit) -> {
                X1ShotData data = X1ShotData.shot(FORM_KISHITU, RED, 0.3F, 4.0F, 0, 90);
                createShot(Specials.user(shot), shot, pos_Entity(shot), angle_Random(Specials.RAND), 0F, 0.01D, 0.15D,
                        0.01D, gravity_Zero(), data);
                return false;
            }, null);
        }
    }

    /** 土着神「ケロちゃん風雨に負けず」 */
    public static final class KerochanFuuuNiMakezu extends X1SpellCard {
        public KerochanFuuuNiMakezu() {
            setNeedLevel(2);
            setRemoveTime(40);
            setEndTime(200);
            setOriginalUserName(SUWAKO);
        }

        @Override
        public void spellcard_main() {
            if (time < 2) return;
            if (time < 140) {
                for (int i = 0; i < 4; i++) {
                    double speed = 0.5D;
                    createShot(user, user, pos(cardPosX, cardPosY - 0.4D, cardPosZ),
                            angle(card.getYRot() + i * 90F + Mth.cos((float) time * 4F) * 45F,
                                    Mth.cos((float) (time + i * 45F) * 2F / 180F * 3.141593F) * 19F - 70F),
                            0F, speed, speed, 0.0F, gravity(0.0F, -0.01F, 0.0F),
                            shot(FORM_LIGHT, BLUE, SIZE[FORM_LIGHT], 8.0F, 10, 120));
                }
            }
            for (int i = 0; i < 2; i++) {
                double speed2 = rand.nextDouble() * 0.2D + 0.45D;
                createShot(user, user, pos(cardPosX, cardPosY - 0.4D, cardPosZ),
                        angle(rand.nextFloat() * 360F, rand.nextFloat() * 14F - 75F), 0F, speed2, speed2, 0.0F,
                        gravity(0.0F, -0.018F, 0.0F), shot(FORM_RICE, AQUA, 0.15F, 9.0F, 4, 120));
            }
        }
    }

    /** 恋符「ノンディレクショナルレーザー」 */
    public static final class NonDirectionalLaser extends X1SpellCard {
        public NonDirectionalLaser() {
            setNeedLevel(3);
            setRemoveTime(60);
            setEndTime(103);
            setOriginalUserName(MARISA);
        }

        @Override
        public void spellcard_main() {
            if (time == 3 || time == 63) {
                Specials.playMasterSpark(user);
                for (int i = 0; i < 5; i++) {
                    Vec3d look = lookVec();
                    Vec3d rotate = getVecFromAngle(userYaw(), userPitch() - 90F);
                    Vec3d move = getVectorFromRotation(rotate, look, i * 72F);
                    createLaserB(user, user, pos(0.0D, getPosYFromEye(user) - user.getY(), 0.0D), move, rotate,
                            time == 3 ? -4F : 4F, 9999, X1LaserData.laser(RED + i, 0.7F, 20.8F, 7.0F, 25, 60, 0), user,
                            1.5D, 1.0F);
                }
            }
        }
    }

    /** 死蝶「華胥の永眠」 */
    public static final class KashoNoEimin extends X1SpellCard {
        public KashoNoEimin() {
            setNeedLevel(3);
            setRemoveTime(40);
            setEndTime(150);
            setOriginalUserName(YUYUKO);
        }

        @Override
        public void spellcard_main() {
            if (time % 6 == 3 && time < 90) {
                Vec3d angle = getVecFromAngle(userYaw(), userPitch(), 1.0D);
                if (!targetDead()) angle = angle_ToPos(pos_User(), pos_Target());
                int color = PURPLE;
                if (time % 9 == 0) color = YELLOW;
                float angleBase = rand.nextFloat() * 360F;
                createCircleShot(user, user, pos_User(), angle, 1.6F, 30, 0.2D, 0.7D, 0.01D, gravity_Zero(),
                        shot(FORM_BUTTERFLY, color, SIZE[FORM_BUTTERFLY], 6.0F, 3, 70), 15, 0.8D, angleBase);
                createCircleShot(user, user, pos_User(), angle, -1.6F, 30, 0.2D, 0.7D, 0.01D, gravity_Zero(),
                        shot(FORM_BUTTERFLY, color, SIZE[FORM_BUTTERFLY], 6.0F, 3, 70), 15, 0.8D, angleBase);
            }
        }
    }

    /** 奇術「エターナルミーク」 */
    public static final class EternalMeek extends X1SpellCard {
        public EternalMeek() {
            setNeedLevel(2);
            setRemoveTime(20);
            setEndTime(50);
            setOriginalUserName(SAKUYA);
        }

        @Override
        public void spellcard_main() {
            if (time < 40) {
                Vec3d angle = lookVec();
                if (!targetDead()) angle = angle_ToPos(pos_User(), pos_Target());
                createRandomRingShot(user, user, pos_User(angle, 0.7D), angle, 0F, 9999, 1.5D, 1.5D, 0.0D,
                        gravity_Zero(), shot(FORM_KNIFE, BLUE, SIZE[FORM_KNIFE], 3F, 3, 60, 0), 3, 0.1D, 50F);
                playShotSound(user);
            }
        }
    }

    /** 月符「ムーンライトレイ」 */
    public static final class MoonlightRay extends X1SpellCard {
        public MoonlightRay() {
            setNeedLevel(1);
            setRemoveTime(30);
            setEndTime(60);
            setOriginalUserName(RUMIA);
        }

        @Override
        public void spellcard_main() {
            if (time == 3) {
                Vec3d look = lookVec();
                Vec3d over = getVecFromAngle(userYaw(), userPitch() + 90F);
                int way = 7;
                float angle = 0F;
                float angleSpan = 360F / way;
                for (int i = 0; i < way; i++) {
                    Vec3d laserVec = getVectorFromRotation(look, over, angle);
                    Vec3d rotate = getOuterProduct(look, laserVec);
                    createLaserB(user, user, pos_User(), laserVec, rotate, -2F, 9999,
                            X1LaserData.laser(BLUE, 0.8F + level * 0.2F, 40.0F, 6.0F, 10, 29 + level * 5, 0), user,
                            1.0D, user.getBbHeight() / 2.0D);
                    angle += angleSpan;
                }
            }
        }
    }

    /** 境符「波と粒の境界」 */
    public static final class NamiToTubuNoKyoukai extends X1SpellCard {
        private float yaw;
        private float pitch;

        public NamiToTubuNoKyoukai() {
            setNeedLevel(5);
            setRemoveTime(40);
            setEndTime(320);
            setOriginalUserName(YUKARI);
        }

        @Override
        public void spellcard_main() {
            if (time == 0) {
                yaw = 0.0F;
                pitch = 0.0F;
            }
            if (time >= 5 && time < 280) {
                yaw += Mth.cos((float) (time + 75) / 50F) * 17F;
                pitch += Mth.sin(Mth.sin((time + 75) / 50F) * 3.14F) * 17F;
                X1ShotData shot = X1ShotData.shot(FORM_LIGHT, PURPLE, 0.3F, 9.0F, 0, 40);
                createSphereShot(user, user, pos_User(), getVecFromAngle(yaw, pitch), 0F, rotate_Default(), 0F, 9999,
                        0.2D, 0.6D, 0.05D, gravity_Zero(), shot, 12, 2.0D, 0F);
            }
        }
    }

    /** 星符「メテオニックシャワー」 */
    public static final class MeteonicShower extends X1SpellCard {
        public MeteonicShower() {
            setNeedLevel(1);
            setRemoveTime(10);
            setEndTime(60);
            setOriginalUserName(MARISA);
        }

        @Override
        public void spellcard_main() {
            if (time > 10 && time < 40 && time % 2 == 0) {
                Vec3d angle = lookVec();
                if (!targetDead()) angle = angle_ToPos(pos_User(), pos_Target());
                java.util.Random r = new java.util.Random();
                int[] colors = {0, 2, 3, 4};
                int color = colors[r.nextInt(4)];
                float size = 0.2F + r.nextFloat() * 0.4F;
                int damage = (int) (size * 15F);
                createRandomRingShot(user, card, pos_User(angle, 0.7D), angle, 0.0F, 9999, 0.4D, 0.6D, 0.1D,
                        gravity_Zero(), shot(FORM_STAR, color, size, damage, 3, 40), 1, 0.0D, 40F);
                playShotSound(user);
            }
        }
    }

    /** 開海「モーゼの奇跡」 */
    public static final class MosesMiracle extends X1SpellCard {
        public MosesMiracle() {
            setNeedLevel(2);
            setRemoveTime(80);
            setEndTime(180);
            setOriginalUserName(SANAE);
        }

        @Override
        public void spellcard_main() {
            if (time % 2 == 0) return;
            double angle = (double) time * 6.0D;
            float baseAngle = userYaw();
            if (target != null) {
                baseAngle = (float) Math.atan2(card.getX() - target.getX(), -(card.getZ() - target.getZ())) / 3.141593F * 180F;
            }
            for (int i = -5; i < 6; i++) {
                double baseX = cardPosX - Math.sin(angle / 180F * 3.141593F) * Math.cos(baseAngle / 180F * 3.141593F) * 3.0D;
                double baseZ = cardPosZ + Math.cos(angle / 180F * 3.141593F) * Math.sin(baseAngle / 180F * 3.141593F) * 3.0D;
                double sideX = -Math.sin((baseAngle + 90F) / 180F * 3.141593F);
                double sideZ = Math.cos((baseAngle + 90F) / 180F * 3.141593F);
                Vec3d toTarget = angle_ToPos(pos_Card(), pos_Living(target));
                createShot(user, user, pos(baseX + sideX * 2.5D, cardPosY + i, baseZ + sideZ * 2.5D), toTarget, 0F,
                        0.9D, 0.9D, 0.0D, gravity_Zero(), shot(FORM_LIGHT, BLUE, 0.8F, 7.0F, 0, 50));
                createShot(user, user, pos(baseX - sideX * 2.5D, cardPosY + i, baseZ - sideZ * 2.5D), toTarget, 0F,
                        0.9D, 0.9D, 0.0D, gravity_Zero(), shot(FORM_LIGHT, BLUE, 0.8F, 7.0F, 0, 50));
            }
        }
    }

    /** 大奇跡「八坂の神風」 */
    public static final class YasakaNoKamikaze extends X1SpellCard {
        public YasakaNoKamikaze() {
            setNeedLevel(3);
            setRemoveTime(100);
            setEndTime(270);
            setOriginalUserName(SANAE);
        }

        @Override
        public void spellcard_main() {
            if (time < 5 || user == null) return;
            Vec3d angle = getVecFromAngle(userYaw(), userPitch(), -1.0D);
            if (!targetDead()) angle = angle_ToPos(pos_Target(), pos_User());
            double distance = Math.cos((float) (time * 2) / 180F * (float) Math.PI - (float) Math.PI) * 2.0D + 3.0D;
            if (time % 46 < 23) {
                createRingShot(user, user, pos_User(), angle, 180F, 1, 0.0D, 1.6D, 0.1D, gravity_Zero(),
                        shot(FORM_RICE, GREEN, SIZE[FORM_RICE], 18F, 10, 40, WIND01), 8, distance,
                        Mth.sin((float) (time * 16) / 180F * (float) Math.PI) * 50F + 50F, time * 10F);
            } else {
                createRingShot(user, user, pos_User(), angle, -180F, 2, 0.0D, 1.6D, 0.1D, gravity_Zero(),
                        shot(FORM_RICE, AQUA, SIZE[FORM_RICE], 18F, 10, 40, WIND01), 8, distance,
                        Mth.sin((float) (-time * 16) / 180F * (float) Math.PI) * 50F + 50F, -time * 10F);
            }
        }
    }

    /** 華符「芳華絢爛」 */
    public static final class HoukaKenran extends X1SpellCard {
        public HoukaKenran() {
            setNeedLevel(2);
            setRemoveTime(60);
            setEndTime(170);
            setOriginalUserName(MEIRIN);
        }

        @Override
        public void spellcard_main() {
            if (time < 150 && time % 3 == 0) {
                Vec3d angle = lookVec();
                if (target.getHealth() > 0F) angle = angle_UserToTarget();
                createRingShot(user, pos_User(), angle, 0.4D, shot(FORM_CRYSTAL, YELLOW, SIZE[FORM_CRYSTAL], 5.0F), 6,
                        0.6D, 45.0F + Mth.sin(time / 20F) * 40F, (float) (time * 2F));
                createRingShot(user, pos_User(), angle, 0.4D, shot(FORM_CRYSTAL, YELLOW, SIZE[FORM_CRYSTAL], 5.0F), 6,
                        0.6D, 45.0F - Mth.sin(time / 20F) * 40F, (float) (time * -2F));
            }
            if (time < 150 && time % 20 == 19) {
                Vec3d angle = lookVec();
                if (target.getHealth() > 0F) angle = angle_UserToTarget();
                createRingShot(user, pos_User(), angle, 0.4D, shot(FORM_CRYSTAL, RED, SIZE[FORM_CRYSTAL], 5.0F), 32,
                        0.6D, 45.0F, (float) (time * -2F));
            }
        }
    }

    /** 彩符「彩光乱舞」 */
    public static final class SaikouRanbu extends X1SpellCard {
        public SaikouRanbu() {
            setNeedLevel(2);
            setRemoveTime(60);
            setEndTime(80);
            setOriginalUserName(MEIRIN);
        }

        @Override
        public void spellcard_main() {
            if (time > 60) return;
            if (time % 30 < 10 && time % 2 == 1) {
                int[] color = {YELLOW, AQUA, BLUE, GREEN};
                Vec3d angle = getVecFromAngle(card.getYRot(), -90);
                createRingShot(user, user, pos(userPosX, getPosYFromEye(user, 0.3D), userPosZ), angle, 0F, 9999, 0.7D,
                        0.7D, 0.0D, gravity_Default(), shot(FORM_CRYSTAL, color[time % 4], 0.2F, 2.5F, 0, 60), 15, 0.7,
                        40F + (time % 30) * 5F, 0F);
            }
            if (time % 30 >= 10 && time % 30 < 30) {
                float spin = time % 30 < 20 ? 3.0F : -3.0F;
                int[] color = {RED, ORANGE, PURPLE};
                for (int i = 1; i <= 14; i++) {
                    float randYaw = rand.nextFloat() * 360F;
                    float randPitch = rand.nextFloat() * 360F;
                    Vec3d move = getVecFromAngle(randYaw, randPitch);
                    Vec3d rotate = getVecFromAngle(randYaw, randPitch + 90F);
                    createShot(user, user, pos_User(), move, 0F, rotate, spin, 20, 1.5D, 0.4D, -0.4D, gravity_Zero(),
                            shot(FORM_CRYSTAL, color[rand.nextInt(3)], 0.2F, 3.5F, 0, 50));
                }
            }
        }
    }

    /** 幻想「花鳥風月、嘯風弄月」 */
    public static final class Kachoufuugetu extends X1SpellCard {
        public Kachoufuugetu() {
            setNeedLevel(5);
            setRemoveTime(40);
            setEndTime(90);
            setOriginalUserName(YUUKA);
        }

        @Override
        public void spellcard_main() {
            Vec3d look = getVecFromAngle(userYaw(), userPitch(), 1.0D);
            if (!targetDead()) look = angle_ToPos(pos_User(), pos_Target());
            float angle = time * 3F;
            if (time > 30) angle = -time * 3F;
            Vec3d rotate = getVecFromAngle(userYaw(), userPitch() + 5F + (float) Math.sin(time * 10F / 180F * 3.141593F) * 50F);
            for (int i = 0; i < 5; i++) {
                Vec3d look2 = getVectorFromRotation(look, rotate, angle);
                Vec3d look3 = getVectorFromRotation(look, rotate, -angle);
                if (time % 10 == 0) {
                    THShotEntity mother = createShotEntity(user, user, pos_User(look2, 2.0D), look2, 0F, rotate, 0F, 9999,
                            0.4D, 0.2D, 0.0D, gravity_Zero(), shot(FORM_MEDIUM, RED, SIZE[FORM_BIG], 14F, 3, 80));
                    float angle2 = 0F;
                    Vec3d motherOver = getVecFromAngle(mother.getYRot(), mother.getXRot() + 90F);
                    Vec3d motherAngle = mother.motion().angle;
                    for (int j = 0; j < 5; j++) {
                        Vec3d set = getVectorFromRotation(motherAngle, motherOver, angle2);
                        createLaserB(user, mother, pos(0.0D, 0.0D, 0.0D), set, motherAngle, 4F, 9999,
                                X1LaserData.laser(RED, 0.5F, 2.0F, 6.0F, 0, 120, 0), mother, 0.0D, 0.0D);
                        angle2 += 72F;
                    }
                } else if (time % 2 == 0) {
                    createShot(user, user, pos_User(look2, 2.0D), look2, 0F, rotate, 0F, 9999, 0.4D, 0.2D, 0.0D,
                            gravity_Zero(), shot(FORM_MEDIUM, YELLOW, SIZE[FORM_MEDIUM], 14F, 3, 80));
                    createShot(user, user, pos_User(look3, 2.0D), look3, 0F, rotate, 0F, 9999, 0.4D, 0.2D, 0.0D,
                            gravity_Zero(), shot(FORM_MEDIUM, YELLOW, SIZE[FORM_MEDIUM], 14F, 3, 80));
                }
                angle += 72F;
            }
        }
    }

    /** 紅符「スカーレットシュート」 */
    public static class ScarletShoot extends X1SpellCard {
        public ScarletShoot() {
            setNeedLevel(4);
            setRemoveTime(30);
            setEndTime(120);
            setOriginalUserName(REMILIA);
        }

        @Override
        public void spellcard_main() {
            if ((time % 25 == 20 && time < 60) || time == 80) {
                boolean fan = time != 80;
                Vec3d lookAt = getVecFromAngle(userYaw(), userPitch(), 1.0D);
                if (!targetDead()) lookAt = angle_ToPos(pos_User(), pos_Target());
                Vec3d rotate = getOverVector(lookAt);
                float angle = fan ? -90F : -3F;
                float angleSpan = fan ? 180F / 4F : 6F / 2F;
                for (int i = 0; i < (fan ? 5 : 3); i++) {
                    scarletShot(getVectorFromRotation(rotate, lookAt, angle), 1.0D, false);
                    angle += angleSpan;
                }
                playShotSound(user);
            }
        }

        public void scarletShot(Vec3d angle, double speed, boolean isCatadi) {
            int special = isCatadi ? BOUND04 : 0;
            int color = isCatadi ? BLUE : RED;
            createShot(user, user, pos_User(), angle, 0F, speed, speed, 0.0D, gravity_Zero(),
                    shot(FORM_BIG, color, SIZE[FORM_BIG], 6F, 0, 120, special));
            for (int i = 0; i < 11; i++) {
                double speed2 = (0.5D + rand.nextDouble() * 0.3D) * speed;
                createRandomRingShot(user, pos_User(), angle, speed2, speed2, 0.0D,
                        shot(FORM_MEDIUM, color, SIZE[FORM_MEDIUM], 4.0F, 0, 120, special), 1, 0.0D, 30F);
            }
            for (int i = 0; i < 22; i++) {
                double speed2 = (0.2D + rand.nextDouble() * 0.3D) * speed;
                createRandomRingShot(user, pos_User(), angle, speed2, speed2, 0.0D,
                        shot(FORM_SMALL, color, SIZE[FORM_SMALL], 2.0F, 0, 120, special), 1, 0.0D, 60F);
            }
        }
    }

    /** 禁弾「カタディオプトリック」 (extends Scarlet Shoot in X1) */
    public static final class Catadioptric extends ScarletShoot {
        public Catadioptric() {
            setNeedLevel(3);
            setRemoveTime(40);
            setEndTime(110);
            setOriginalUserName(FLANDORE);
        }

        @Override
        public void spellcard_main() {
            if (time % 25 == 1 && time < 75) {
                float angleSpan = 90F / 4F;
                float angleBase = 180F;
                if (time == 26) angleBase = 90F;
                else if (time == 51) angleBase = -90F;
                float angle = angleBase - angleSpan * 2;
                for (int i = 0; i < 5; i++) {
                    Vec3d look = getRotationVectorFromAngle(userYaw(), userPitch(), angle, 1.0D);
                    scarletShot(look, 0.6D, true);
                    angle += angleSpan;
                }
                playShotSound(user);
            }
        }
    }
}
