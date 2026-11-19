package dev.kneekura.fivedifficulties.forge.spellcard.cards;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1ShotData;
import dev.kneekura.fivedifficulties.core.x1.X1ShotMotion;
import dev.kneekura.fivedifficulties.forge.entity.THLaserEntity;
import dev.kneekura.fivedifficulties.forge.entity.THShotEntity;
import dev.kneekura.fivedifficulties.forge.spellcard.X1SpellCard;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.Level;

import static dev.kneekura.fivedifficulties.core.x1.X1ShotTables.*;
import static dev.kneekura.fivedifficulties.forge.shot.X1Danmaku.*;
import static dev.kneekura.fivedifficulties.forge.spellcard.cards.Specials.RAND;
import static dev.kneekura.fivedifficulties.forge.spellcard.cards.Specials.register;
import static dev.kneekura.fivedifficulties.forge.spellcard.cards.Specials.user;

/** X1 spell cards that also register ISpecialShot handlers, translated statement by statement. */
public final class SpecialCards {
    private SpecialCards() {}

    private static final int HARD = 3;
    /** THKaguyaConfig "Danmaku Level" default. */
    private static final int DANMAKU_LEVEL = 2;

    private static Vec3d rot(Vec3d axis, Vec3d v, float a) {
        return getVectorFromRotation(axis, v, a);
    }

    /** 凍符「パーフェクトフリーズ」 */
    public static final class PerfectFreeze extends X1SpellCard {
        public static final int SPECIAL_FREEZE = 900;

        public PerfectFreeze() {
            setNeedLevel(1);
            setRemoveTime(20);
            setEndTime(110);
            setOriginalUserName(CIRNO);
        }

        @Override
        public void registerSpecialShots() {
            register(SPECIAL_FREEZE, (shot, m, id) -> {
                if (shot.tickCount >= 20) {
                    m.shotSpeed = 0.01D;
                    m.limitSpeed = 0.3D;
                    m.acceleration = 0.03D;
                    m.special = 0;
                }
            }, null, null);
        }

        @Override
        public void spellcard_main() {
            if (time < 5) return;
            if (time < 58) {
                int num = Math.min(4 + level, 10);
                for (int i = 0; i < num; i++) {
                    Vec3d angle = angle_Random();
                    createShot(user, user, pos_User(angle, 1.0D), angle, 0F, level * 0.1D, 0.5D, 0.03D, gravity_Zero(),
                            shot(FORM_CIRCLE, RAINBOW, SIZE[FORM_CIRCLE], 4.0F, 5, 120));
                }
                playShotSound(user);
            }
            if (time == 64) {
                for (THShotEntity s : world.getEntitiesOfClass(THShotEntity.class, user.getBoundingBox().inflate(20.0D))) {
                    if (s instanceof THLaserEntity) continue;
                    createShot(user, user, pos_Entity(s), getVecFromAngle(rand.nextFloat() * 360F, rand.nextFloat() * 180F - 90F),
                            0F, 0.0001D, 0.0001D, 0.0D, gravity_Zero(),
                            shot(s.getShotForm(), WHITE, s.getShotSize(), s.shotDamage, 0,
                                    s.getShotEndTime() - s.tickCount + 50, SPECIAL_FREEZE));
                    s.discard();
                }
            }
        }
    }

    /** 魍魎「二重黒死蝶」 */
    public static final class NijuuKokushichou extends X1SpellCard {
        public static final int SPECIAL_KOKUSHICHOU01 = 500;

        public NijuuKokushichou() {
            setNeedLevel(3);
            setRemoveTime(20);
            setEndTime(200);
            setOriginalUserName(YUKARI);
        }

        @Override
        public void registerSpecialShots() {
            register(SPECIAL_KOKUSHICHOU01, (shot, m, id) -> {
                if (shot.tickCount < 25) {
                    m.motion = m.motion.scale(0.90D);
                } else if (shot.tickCount == 25) {
                    m.limitSpeed = 2.0D;
                    m.acceleration = 0.03D;
                } else if (shot.tickCount < 50) {
                    m.rotateYaw(shot.getShotColor() % 2 == 0 ? 10F : -10F);
                }
            }, null, null);
        }

        @Override
        public void spellcard_main() {
            if (time % 70 == 10 && time <= 100) {
                for (int i = 0; i < 30; i++) {
                    double speed = rand.nextDouble() * 2.0 + 0.5D;
                    float angleXZ = rand.nextFloat() * 360F;
                    float angleY = rand.nextFloat() * 180F - 90F;
                    createCircleShot(user, user, pos_User(), getVecFromAngle(angleXZ, angleY), speed, 0.0D, 1.0D,
                            gravity_Zero(), shot(FORM_BUTTERFLY, i % 2, SIZE[FORM_BUTTERFLY], 8.0F, 1, 120,
                                    SPECIAL_KOKUSHICHOU01), 8, 0.2D, 0F);
                }
                playShotSound(user);
            }
        }
    }

    /** 水符「河童のポロロッカ」 */
    public static final class KappaPororoca extends X1SpellCard {
        public static final int SPECIAL_KAPPA_POROROCA01 = 1100;

        public KappaPororoca() {
            setNeedLevel(3);
            setRemoveTime(30);
            setEndTime(140);
            setOriginalUserName(NITORI);
        }

        @Override
        public void registerSpecialShots() {
            register(SPECIAL_KAPPA_POROROCA01, (shot, m, id) -> {
                LivingEntity u = user(shot);
                if (shot.tickCount % 4 == 3 && u != null) {
                    X1ShotData data = X1ShotData.shot(FORM_LIGHT, BLUE, 0.3F, 5.0F, 0, 100, BOUND01);
                    createShot(u, shot, pos_Entity(shot), angle(u.getYRot() + RAND.nextFloat() * 30F - 15F, -15F), 0F,
                            0.7D, 0.7D, 0.0D, gravity_Default(), data);
                }
            }, (shot, m, id, hit) -> {
                shot.bound(m, 0.9D, 4);
                return true;
            }, null);
        }

        @Override
        public void spellcard_main() {
            if (time < 5) return;
            if (time % 10 == 0) {
                createShot(user, user, pos_User(), getVecFromAngle(userYaw() + 90F, -60F), 0F, 0.3D, 0.3D, 0.0D,
                        gravity_Default(), shot(FORM_LIGHT, BLUE, 0.45F, 8.0F, 2, 60, SPECIAL_KAPPA_POROROCA01));
                createShot(user, user, pos_User(), getVecFromAngle(userYaw() - 90F, -60F), 0F, 0.3D, 0.3D, 0.0D,
                        gravity_Default(), shot(FORM_LIGHT, BLUE, 0.45F, 8.0F, 2, 60, SPECIAL_KAPPA_POROROCA01));
            }
        }
    }

    /** 魔符「スターダストレヴァリエ」 */
    public static final class StardustReverie extends X1SpellCard {
        public static final int SPECIAL_STARDUST01 = 1200;

        public StardustReverie() {
            setNeedLevel(4);
            setRemoveTime(60);
            setEndTime(120);
            setOriginalUserName(MARISA);
        }

        @Override
        public void registerSpecialShots() {
            register(SPECIAL_STARDUST01, (shot, m, id) -> {
                X1ShotData data = X1ShotData.shot(shot.getShotForm(), shot.getShotColor(), 0.3F, 5.0F, 10, 50);
                m.rotateYaw(2.0F);
                Vec3d vec = rot(m.rotate, m.angle, shot.tickCount * 13F);
                createShot(user(shot), shot, pos_Entity(shot), angle(vec.x(), vec.y(), vec.z()), shot.getAngleZ(),
                        m.rotate, 0F, 9999, 0.1D, 0.3D, 0.03D, gravity_Zero(), data);
            }, null, (shot, m, id, hit) -> true);
        }

        @Override
        public void spellcard_main() {
            if (time < 5) return;
            if (time == 5) {
                int[] way = {4, 4, 7, 9, 10};
                createCircleShot(user, user, pos_User(), lookVec(), 0.3D, 0.3D, 0.0D, gravity_Zero(),
                        shot(FORM_STAR, RAINBOW, 1.2F, 7.0F, 2, 120, SPECIAL_STARDUST01), way[level], 0.2D, 0F);
            }
        }
    }

    /** 奇跡「ミラクルフルーツ」 */
    public static final class MiracleFruit extends X1SpellCard {
        public static final int SPECIAL_MIRACLE_FRUIT01 = 1400;

        public MiracleFruit() {
            setNeedLevel(1);
            setRemoveTime(30);
            setEndTime(60);
            setOriginalUserName(SANAE);
        }

        @Override
        public void registerSpecialShots() {
            register(SPECIAL_MIRACLE_FRUIT01, (shot, m, id) -> {
                if (shot.tickCount == shot.getShotEndTime()) {
                    float angle2 = RAND.nextFloat() * 360F;
                    for (int j = 0; j < 8; j++) {
                        Vec3d look = rot(m.rotate, m.angle, angle2);
                        for (int i = 0; i < 6; i++) {
                            createShot(user(shot), shot, pos_Entity(shot), look, 0.0F, m.rotate, 0.0F, 9999, 0.5D, 0.2D,
                                    0.8D, gravity_Zero(), X1ShotData.shot(FORM_SMALL, RED, 0.3F, 6.0F, 3 + i * 2, 90));
                        }
                        angle2 += 45F;
                    }
                }
            }, null, (shot, m, id, hit) -> {
                if (hit instanceof LivingEntity living) living.removeAllEffects();
                return false;
            });
        }

        @Override
        public void spellcard_main() {
            if (time == 1) user.removeAllEffects();
            if (time < 5) return;
            if (time % 30 == 6) {
                Vec3d angle = getRotationVectorFromAngle(userYaw(), userPitch(), 0F, 1.0D);
                playShotSound(user);
                createCircleShot(user, user, pos_User(), angle, 2.0D, 0.1D, -0.2D, gravity_Zero(),
                        shot(FORM_OVAL, RED, SIZE[FORM_OVAL], 7.0F, 3, 20, SPECIAL_MIRACLE_FRUIT01), 8, 0.2D,
                        rand.nextFloat() * 360F);
            }
        }
    }

    /** 妖怪退治「妖力スポイラー」 */
    public static final class YouryokuSpoiler extends X1SpellCard {
        public static final int SPECIAL_SPOILER01 = 1600;
        public static final int SPECIAL_SPOILER02 = 1601;

        public YouryokuSpoiler() {
            setNeedLevel(2);
            setRemoveTime(10);
            setEndTime(80);
            setOriginalUserName(SANAE);
        }

        private static void homeOnUser(THShotEntity shot, X1ShotMotion m, boolean vanishNearUser) {
            LivingEntity u = user(shot);
            if (shot.tickCount < 20 || u == null) return;
            m.limitSpeed = 1.0D;
            m.acceleration = 0.05D;
            double dx = u.getX() - shot.getX();
            double dz = u.getZ() - shot.getZ();
            m.yaw = (float) Math.atan2(dx, dz) / 3.141593F * 180F;
            m.pitch = (float) Math.atan2(u.getY() + 1.0D - shot.getY(), Math.sqrt(dx * dx + dz * dz)) / 3.141593F * 180F;
            m.setVector();
            if (vanishNearUser && shot.distanceTo(u) < 1.5F) shot.discard();
        }

        private static boolean spoiler02(THShotEntity shot, net.minecraft.world.entity.Entity hit) {
            LivingEntity u = user(shot);
            if (u != null && hit == u) {
                u.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 20 * 20, 1));
                u.addEffect(new MobEffectInstance(MobEffects.DAMAGE_BOOST, 20 * 20, 1));
                return false;
            }
            return true;
        }

        @Override
        public void registerSpecialShots() {
            THShotEntity.USER_HITTABLE_SPECIALS.add(SPECIAL_SPOILER01);
            THShotEntity.USER_HITTABLE_SPECIALS.add(SPECIAL_SPOILER02);
            register(SPECIAL_SPOILER01, (shot, m, id) -> homeOnUser(shot, m, true), null, (shot, m, id, hit) -> {
                if (hit instanceof LivingEntity living) {
                    if (living != user(shot)) {
                        living.addEffect(new MobEffectInstance(MobEffects.WITHER, 20 * 20, 1));
                        living.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 20 * 20, 1));
                        m.special = SPECIAL_SPOILER02;
                        return true;
                    }
                    return false;
                }
                return spoiler02(shot, hit); // X1 switch falls through for non-living targets
            });
            register(SPECIAL_SPOILER02, (shot, m, id) -> homeOnUser(shot, m, false), null,
                    (shot, m, id, hit) -> spoiler02(shot, hit));
        }

        @Override
        public void spellcard_main() {
            boolean first = time < 20, second = time > 40 && time < 60;
            if ((first || second) && target != null) {
                world.playSound(null, user.getX(), user.getY(), user.getZ(), SoundEvents.PORTAL_AMBIENT,
                        SoundSource.HOSTILE, 2.0F, 1.9F);
                createCircleShot(user, user, pos(targetPosX, targetPosY, targetPosZ),
                        getVecFromAngle(card.getYRot(), card.getXRot()), 2.0D, 0.2D, -0.1D, gravity_Zero(),
                        shot(FORM_SCALE, rand.nextInt(7), 0.3F, 3.0F, 6, 70, SPECIAL_SPOILER01), 7, 1.5D,
                        first ? time * 3F : -time * 3F);
            }
        }
    }

    /** 氷符「アイシクルフォール」 */
    public static final class IcicleFall extends X1SpellCard {
        public static final int SPECIAL_ICECLEFALL01 = 1900;
        public static final int SPECIAL_ICECLEFALL02 = 1901;

        public IcicleFall() {
            setNeedLevel(1);
            setRemoveTime(60);
            setEndTime(180);
            setOriginalUserName(CIRNO);
        }

        private static void turn(THShotEntity shot, X1ShotMotion m, float degrees) {
            m.rotateYaw(degrees);
            shot.setShotEndTime(120);
            m.gravity = new Vec3d(m.gravity.x(), GRAVITY_DEFAULT, m.gravity.z());
            m.acceleration = 0.01D;
            m.limitSpeed = 10.0D;
            m.updateMotion();
            m.special = 0;
        }

        @Override
        public void registerSpecialShots() {
            register(SPECIAL_ICECLEFALL01, (shot, m, id) -> {
                if (shot.tickCount >= shot.getShotEndTime()) turn(shot, m, 90F);
            }, null, null);
            register(SPECIAL_ICECLEFALL02, (shot, m, id) -> {
                if (shot.tickCount == shot.getShotEndTime()) turn(shot, m, -90F); // X1 uses == here
            }, null, null);
        }

        @Override
        public void spellcard_main() {
            if (time % 5 == 0) {
                float angle = (float) Math.sin(time * 13F / 180F * 3.141593F) * (30F + level * 30F) + 90F;
                int num = 4 + level * 2;
                float damage = 6.0F;
                for (int i = 1; i < num; i++) {
                    createShotEntity(user, user, pos_User(), getVecFromAngle(userYaw() + angle, -30F), 0F, i * 1.0D, 0.0D,
                            -i * 0.1D, gravity_Zero(), shot(FORM_CRYSTAL, BLUE, 0.5F, damage, 0, num, SPECIAL_ICECLEFALL01))
                            .motion().rotate = rotate_Default();
                    createShotEntity(user, user, pos_User(), getVecFromAngle(userYaw() - angle, -30F), 0F, i * 1.0D, 0.0D,
                            -i * 0.1D, gravity_Zero(), shot(FORM_CRYSTAL, BLUE, 0.5F, damage, 0, num, SPECIAL_ICECLEFALL02))
                            .motion().rotate = rotate_Default();
                }
            }
        }
    }

    /** 禁弾「スターボウブレイク」 */
    public static final class StarbowBreak extends X1SpellCard {
        public static final int SPECIAL_STARBOW_BRAKE01 = 2000;

        public StarbowBreak() {
            setNeedLevel(3);
            setRemoveTime(40);
            setEndTime(150);
            setOriginalUserName(FLANDORE);
        }

        @Override
        public void registerSpecialShots() {
            register(SPECIAL_STARBOW_BRAKE01, (shot, m, id) -> {
                if (shot.isShotEndTime()) {
                    m.yaw = -m.yaw + RAND.nextFloat() * 14F - 7F;
                    m.pitch = -m.pitch + RAND.nextFloat() * 14F - 7F;
                    double gravityLevel = RAND.nextDouble() * 0.1D + 0.02D;
                    X1ShotData data = X1ShotData.shot(shot.getShotForm(), shot.getShotColor(), shot.getShotSize(),
                            shot.shotDamage, 10, 90);
                    createShot(user(shot), shot, pos_Entity(shot), angle(m.yaw, m.pitch), 0F, -0.3D, 0.7D,
                            RAND.nextDouble() * 0.03D, gravity(m.gravity.x() * gravityLevel, m.gravity.y() * gravityLevel,
                                    m.gravity.z() * gravityLevel), data);
                }
            }, null, null);
        }

        @Override
        public void spellcard_main() {
            if (time % 60 >= 3 && time % 60 <= 23 && time % 3 == 0 && time < 119) {
                int[] rainbowPattern = {PURPLE, BLUE, AQUA, GREEN, YELLOW, ORANGE, RED};
                Vec3d look = lookVec();
                if (!targetDead()) look = angle_ToPos(pos_User(), pos_Target());
                int num = time % 60;
                Vec3d gravity = gravity(look.x() * 0.13D, look.y() * 0.13D, look.z() * 0.13D);
                int color = rainbowPattern[num / 3 - 1];
                createRingShot(user, user, pos(user.getX() + gravity.x() * num,
                                getPosYFromEye(user, -0.2D) + gravity.y() * num, user.getZ() + gravity.z() * num), look,
                        0.0F, 9999, 0.1D, 4.0D, 0.01D, gravity, shot(FORM_LIGHT, color, 0.3F, 8.0F, 5, 8,
                                SPECIAL_STARBOW_BRAKE01), num * 2, (float) num / 5F, 180F, rand.nextFloat() * 360F);
            }
        }
    }

    /** 「レッドマジック」 */
    public static final class RedMagic extends X1SpellCard {
        public static final int SPECIAL_REDMAGIC01 = 2300;
        public static final int SPECIAL_REDMAGIC02 = 2301;

        public RedMagic() {
            setNeedLevel(4);
            setRemoveTime(20);
            setEndTime(190);
            setOriginalUserName(REMILIA);
        }

        @Override
        public void registerSpecialShots() {
            register(SPECIAL_REDMAGIC01, (shot, m, id) -> {
                if (shot.tickCount % 3 == 0) {
                    Vec3d rotate2 = rot(m.rotate, m.angle, 90F + shot.tickCount * 3F);
                    X1ShotData data = X1ShotData.shot(FORM_LIGHT, RED, SIZE[FORM_LIGHT], 9.0F, 20,
                            30 - shot.tickCount + 120, SPECIAL_REDMAGIC02);
                    createShot(user(shot), shot, pos_Entity(shot), rotate2, shot.getAngleZ(), m.rotate, 0F, 9999, 0.001D,
                            0.0D, 0.02D, gravity_Zero(), data);
                }
            }, null, null);
            register(SPECIAL_REDMAGIC02, (shot, m, id) -> {
                if (shot.tickCount >= 30) {
                    m.shotSpeed = 0.1D;
                    m.limitSpeed = 0.3D;
                    m.special = 0;
                }
            }, null, null);
        }

        @Override
        public void spellcard_main() {
            if (time == 5 || time == 75) {
                float spin = time == 5 ? -5F : 5F;
                float angle2 = 0F;
                X1ShotData data = shot(FORM_BIG, PURPLE, SIZE[FORM_BIG], 14F, 3, 30, SPECIAL_REDMAGIC01);
                for (int i = 0; i < 3; i++) {
                    Vec3d angle = getVecFromAngle(userYaw(), userPitch() + angle2, 1.0D);
                    createCircleShot(user, user, pos_User(), angle, spin, 20, 0.9D, 0.2D, 0.0D, gravity_Zero(), data, 6, 0.7D);
                    angle = getVecFromAngle(userYaw() + 90F, userPitch() + 90F + angle2, 1.0D);
                    createCircleShot(user, user, pos_User(), angle, spin, 20, 0.9D, 0.2D, 0.0D, gravity_Zero(), data, 6, 0.7D);
                    angle2 += 60F;
                }
            }
        }
    }

    /** 蛍符「地上の流星」 */
    public static final class MeteorOnEarth extends X1SpellCard {
        public static final int SP_METEORONEARTH01 = 3500;
        public static final int SP_METEORONEARTH11 = 3510;

        public MeteorOnEarth() {
            setNeedLevel(1);
            setRemoveTime(25);
            setEndTime(120);
            setOriginalUserName(WRIGGLE);
        }

        @Override
        public void registerSpecialShots() {
            register(SP_METEORONEARTH01, (shot, m, id) -> {
                LivingEntity u = user(shot);
                if (shot.tickCount == 1 && u != null) m.rotate = look(u);
                if (shot.tickCount % 2 == 0) {
                    createShot(u, shot, pos_Entity(shot), rot(m.angle, m.rotate, shot.tickCount * 13.0F), 0.0F, 0.0D,
                            0.5D, 0.00D, gravity_Zero(), X1ShotData.shot(FORM_SMALL, AQUA, 5, 40, SP_METEORONEARTH11));
                }
            }, null, null);
            register(SP_METEORONEARTH11, (shot, m, id) -> {
                if (shot.tickCount == 30) {
                    m.acceleration = 0.03D;
                    m.updateMotion();
                }
            }, null, null);
        }

        @Override
        public void spellcard_main() {
            int[] way = {0, 5, 7, 4, 6};
            if (time == 5 || time == 65) {
                float spin = time == 5 ? 2.0F : -2.0F;
                Vec3d angle = angle_UserToTarget();
                createRingShot(user, user, pos_User(), angle, spin, 60, 0.3D, 0.3D, 1.0D, gravity_Zero(),
                        X1ShotData.shot(FORM_FAMILIAR, GREEN, 0, 60, SP_METEORONEARTH01), way[level], 0.5D, 30F,
                        rand.nextFloat() * 360F);
                if (level >= HARD) {
                    createRingShot(user, user, pos_User(), angle, spin, 60, 0.3D, 0.3D, 1.0D, gravity_Zero(),
                            X1ShotData.shot(FORM_FAMILIAR, GREEN, 0, 60, SP_METEORONEARTH01), 8, 0.5D, 70F,
                            rand.nextFloat() * 360F);
                }
                playShotSound(user);
            }
        }
    }

    /** 雷矢「ガゴウジサイクロン」 */
    public static final class GagoujiCyclone extends X1SpellCard {
        public static final int SPECIAL_GAGOUJI01 = 4000;
        public static final int SPECIAL_TOZIKO01 = 4020;

        public GagoujiCyclone() {
            setNeedLevel(2);
            setRemoveTime(30);
            setEndTime(120);
            setOriginalUserName(TOZIKO);
        }

        @Override
        public void registerSpecialShots() {
            register(SPECIAL_GAGOUJI01, (shot, m, id) -> {
                if (shot.tickCount == 1) {
                    m.rotateYaw(45F);
                    m.acceleration = -0.099D;
                    m.limitSpeed = 0.0D;
                    m.updateMotion();
                }
                if (shot.tickCount % 20 == 9) {
                    m.rotateYaw(-90F);
                    m.setSpeed(1.0D);
                    m.updateMotion();
                } else if (shot.tickCount % 20 == 19) {
                    m.rotateYaw(90F);
                    m.setSpeed(1.0D);
                    m.updateMotion();
                }
            }, null, null);
            register(SPECIAL_TOZIKO01, (shot, m, id) -> {
                if (shot.tickCount >= shot.getShotEndTime()) {
                    // X1 re-aims at an EntityDanmakuMob user's target here (mobs arrive in P17).
                    shot.setShotEndTime(90);
                    m.shotSpeed = 0.01D;
                    m.acceleration = 0.03D;
                    m.limitSpeed = 0.2D + DANMAKU_LEVEL * 0.1D;
                    m.special = 0;
                }
            }, null, null);
        }

        @Override
        public void spellcard_main() {
            boolean firstHalf = time % 120 <= 40 && time % 2 == 0;
            boolean secondHalf = time % 120 >= 60 && time % 120 < 100 && time % 2 == 0;
            if (firstHalf || secondHalf) {
                createRingShot(user, user, pos_User(), angle_UserToTarget(), 0F, 9999, 1.0D, 1.0D, 0.0D, gravity_Zero(),
                        X1ShotData.shot(FORM_ARROW, YELLOW, 0, 50, SPECIAL_GAGOUJI01), 9, 1.0D, 80F,
                        firstHalf ? time / 2F : -time / 2F);
                if (level >= 2) {
                    createShot(user, user, pos_User(), angle_UserToTarget(), 0F, angle(userYaw(), userPitch() + 90F), 0F,
                            99999, 1.0D, 0.0D, -0.1D, gravity_Zero(),
                            X1ShotData.shot(FORM_ARROW, YELLOW, SIZE[FORM_ARROW], 5.0F, 0, 60, SPECIAL_GAGOUJI01));
                }
            }
            if (level == 4 && time % 120 > 30 && time % 120 <= 90) {
                createRingShot(user, user, pos_User(), angle_UserToTarget(), 0F, 99999, 1.0D, 0.0D, -0.1D, gravity_Zero(),
                        X1ShotData.shot(FORM_ARROW, RED, 0, 60, SPECIAL_GAGOUJI01), 3, 1.0D, 10F, time / 2F);
            }
            if (time % 20 == 0) {
                createRingShot(user, user, pos_User(), angle_UserToTarget(), 0F, 99999, 1.2D, 0.15D + level * 0.05D,
                        -0.1D, gravity_Zero(), X1ShotData.shot(FORM_CIRCLE, YELLOW, SIZE[FORM_CIRCLE], 5.0F, 0, 90, 0),
                        8 + level * 4, 1.0D, 70F, 0F);
                createRingShot(user, user, pos_User(), angle_UserToTarget(), 0F, 99999, 1.2D, 0.15D + level * 0.05D,
                        -0.1D, gravity_Zero(), X1ShotData.shot(FORM_CIRCLE, YELLOW, SIZE[FORM_CIRCLE], 5.0F, 0, 90, 0),
                        4 + level * 2, 1.0D, 20F, 0F);
                if (level >= 3) {
                    createShot(user, user, pos_User(), angle_UserToTarget(), 0F, rotate_Default(), 0F, 99999, 1.2D,
                            0.15D + level * 0.05D, -0.1D, gravity_Zero(),
                            X1ShotData.shot(FORM_CIRCLE, YELLOW, SIZE[FORM_CIRCLE], 5.0F, 0, 90, 0));
                }
                playShotSound(user);
            }
        }
    }

    /** 蓬莱「凱風快晴 -フジヤマヴォルケイノ-」 */
    public static final class FujiyamaVolcano extends X1SpellCard {
        public static final int SPECIAL_FUJUYAMA01 = 3300, SPECIAL_FUJUYAMA02 = 3301, SPECIAL_FUJUYAMA03 = 3302,
                SPECIAL_FUJUYAMA04 = 3303;

        public FujiyamaVolcano() {
            setNeedLevel(5);
            setRemoveTime(20);
            setEndTime(120);
            setOriginalUserName(MOKOU);
        }

        private static void split(THShotEntity shot, X1ShotMotion m, int form, float damage, int end, int next) {
            if (!shot.isShotEndTime()) return;
            for (int i = 0; i < 2; i++) {
                createShot(user(shot), shot, pos_Entity(shot), angle_LimitRandom(RAND, m.angle, 50F), 0.0F, 0.5D, 0.5D,
                        1.0D, gravity_Zero(), X1ShotData.shot(form, RED, SIZE[form], damage, 0, end, next));
            }
            shot.discard();
        }

        @Override
        public void registerSpecialShots() {
            register(SPECIAL_FUJUYAMA01, (shot, m, id) -> {
                if (m.speed() <= 0.0D) {
                    createSphereShot(user(shot), shot, pos_Entity(shot), angle_Random(RAND), 0F, 0.5D, 0.5D, 0.0D,
                            gravity_Zero(), X1ShotData.shot(FORM_BIG, RED, SIZE[FORM_BIG], 10.0F, 0, 9, SPECIAL_FUJUYAMA02),
                            44, 0.0D, RAND.nextFloat() * 360F);
                    shot.level().explode(shot, shot.getX(), shot.getY(), shot.getZ(), 1.0F, Level.ExplosionInteraction.NONE);
                    shot.discard();
                }
            }, (shot, m, id, hit) -> {
                for (int i = 0; i < 40; i++) {
                    createShot(user(shot), shot, pos_Entity(shot), angle_Random(RAND), 0.0F, 0.5D, 0.5D, 1.0D,
                            gravity_Zero(), X1ShotData.shot(FORM_BIG, RED, SIZE[FORM_BIG], 10.0F, 0, 6, SPECIAL_FUJUYAMA02));
                }
                shot.discard();
                return false;
            }, null);
            register(SPECIAL_FUJUYAMA02, (shot, m, id) -> split(shot, m, FORM_MEDIUM, 7.0F, 5, SPECIAL_FUJUYAMA03), null, null);
            register(SPECIAL_FUJUYAMA03, (shot, m, id) -> split(shot, m, FORM_SMALL, 5.0F, 4, SPECIAL_FUJUYAMA04), null, null);
            register(SPECIAL_FUJUYAMA04, (shot, m, id) -> split(shot, m, FORM_TINY, 3.0F, 2, 0), null, null);
        }

        @Override
        public void spellcard_main() {
            if ((time < 45 && time % 15 == 0) || (time >= 60 && time <= 90 && time % 7 == 0)) {
                X1ShotData data = X1ShotData.shot(FORM_FAMILIAR, BLUE, 0, 40, SPECIAL_FUJUYAMA01);
                createShot(user, user, pos_User(), angle_UserToTarget(), 0F, 2.4D, 0.0D, -(2.4D / user.distanceTo(target)),
                        gravity_Zero(), data);
                playShotSound(user);
            }
        }
    }

    /** 蟲符「リトルバグストーム」 */
    public static final class LittleBugStorm extends X1SpellCard {
        public static final int SP_LITTLEBUGSTORM01 = 3400, SP_LITTLEBUGSTORM02 = 3401, SP_LITTLEBUGSTORM03 = 3402,
                SP_LITTLEBUGSTORM11 = 3410, SP_LITTLEBUGSTORM12 = 3411, SP_LITTLEBUGSTORM13 = 3412,
                SP_ATTACK01_01 = 3450, SP_ATTACK01_02 = 3451;
        private float yaw;
        private float pitch;

        public LittleBugStorm() {
            setNeedLevel(2);
            setRemoveTime(25);
            setEndTime(150);
            setOriginalUserName(WRIGGLE);
        }

        private static void stage1(THShotEntity shot, X1ShotMotion m, int next) {
            if (!shot.isShotEndTime()) return;
            shot.setShotColor(WHITE);
            shot.setShotSize(SIZE[FORM_SMALL]);
            m.special = next;
            shot.setShotEndTime(20);
            m.angle = rot(m.rotate, m.angle, 90);
            m.shotSpeed = 3.0;
            m.limitSpeed = 0.0;
            m.acceleration = -1.0;
            shot.reCreate();
            shot.delete();
        }

        private static void stage2(THShotEntity shot, X1ShotMotion m, int next) {
            if (!shot.isShotEndTime()) return;
            shot.setShotForm(FORM_LIGHT);
            shot.setShotColor(YELLOW);
            shot.shotDamage = 4.0F;
            shot.setShotSize(SIZE[FORM_TINY]);
            m.special = next;
            shot.reCreate();
            shot.delete();
        }

        private static void stage3(THShotEntity shot, X1ShotMotion m, int color, float turn) {
            if (shot.tickCount % 3 == 0) {
                if (shot.getShotColor() == YELLOW) {
                    shot.setShotColor(WHITE);
                    shot.setShotSize(SIZE[FORM_TINY]);
                } else {
                    shot.setShotColor(YELLOW);
                    shot.setShotSize(SIZE[FORM_TINY] * 2F);
                }
            }
            if (shot.isShotEndTime()) {
                shot.setShotForm(FORM_RICE);
                shot.setShotColor(color);
                shot.shotDamage = 6.0F;
                shot.setShotSize(SIZE[FORM_RICE] * 2F);
                m.special = 0;
                Vec3d a = rot(m.rotate, m.angle, turn);
                m.angle = new Vec3d(a.x(), Math.sin(getYawFromVector(a.x(), a.z()) * 23F / 180F * 3.141593F) * 30F * 0.01,
                        a.z());
                m.shotSpeed = 0.01;
                m.limitSpeed = 0.5;
                m.acceleration = 0.02;
                shot.setShotEndTime(80);
                shot.reCreate();
                shot.delete();
            }
        }

        private static void attack(THShotEntity shot, X1ShotMotion m, float turn) {
            if (!shot.isShotEndTime()) return;
            m.special = 0;
            shot.setShotEndTime(80);
            m.angle = rot(m.rotate, m.angle, turn);
            m.limitSpeed = 0.5;
            m.acceleration = 0.03;
            shot.reCreate();
            shot.delete();
        }

        @Override
        public void registerSpecialShots() {
            register(SP_LITTLEBUGSTORM01, (s, m, id) -> stage1(s, m, SP_LITTLEBUGSTORM02), null, null);
            register(SP_LITTLEBUGSTORM02, (s, m, id) -> stage2(s, m, SP_LITTLEBUGSTORM03), null, null);
            register(SP_LITTLEBUGSTORM03, (s, m, id) -> stage3(s, m, YELLOW, -45), null, null);
            register(SP_LITTLEBUGSTORM11, (s, m, id) -> stage1(s, m, SP_LITTLEBUGSTORM12), null, null);
            register(SP_LITTLEBUGSTORM12, (s, m, id) -> stage2(s, m, SP_LITTLEBUGSTORM13), null, null);
            register(SP_LITTLEBUGSTORM13, (s, m, id) -> stage3(s, m, GREEN, 135), null, null);
            register(SP_ATTACK01_01, (s, m, id) -> attack(s, m, 70), null, null);
            register(SP_ATTACK01_02, (s, m, id) -> attack(s, m, -70), null, null);
        }

        @Override
        public void spellcard_main() {
            int way = 1 + level * 2;
            if (time < 60) {
                yaw += 2.7F;
                pitch += 2.7F;
                int special = (time < 15 || (time >= 30 && time < 45)) ? SP_LITTLEBUGSTORM01 : SP_LITTLEBUGSTORM11;
                createSphereShot(user, user, pos_User(), angle(yaw, pitch), 1.0F, 1.0F, 0.0F, -0.05F - time * 0.001,
                        gravity_Zero(), shot(FORM_TINY, WHITE, SIZE[FORM_TINY], 2.0F, 0, 50, special), way, 0.3D, 1.4F);
                playShotSound(user);
            }
        }
    }
}
