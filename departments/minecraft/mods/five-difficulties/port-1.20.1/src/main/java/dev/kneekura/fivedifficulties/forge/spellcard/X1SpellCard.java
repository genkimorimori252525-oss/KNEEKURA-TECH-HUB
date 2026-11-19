package dev.kneekura.fivedifficulties.forge.spellcard;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1ShotData;
import dev.kneekura.fivedifficulties.core.x1.X1ShotTables;
import dev.kneekura.fivedifficulties.forge.entity.SpellCardEntity;
import dev.kneekura.fivedifficulties.forge.shot.X1Danmaku;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.LivingEntity;

import java.util.Random;

/**
 * Port of X1 {@code THSpellCard} (+ {@code ITHSpellCard}). Subclasses override
 * {@link #spellcard_main()}; names follow X1 so each card reads like its original.
 */
public abstract class X1SpellCard {
    // Original user IDs (THSpellCard) used to sort the creative list.
    public static final int REIMU = 0, MARISA = 1, RUMIA = 2, CIRNO = 4, MEIRIN = 5, PATCHOULI = 7, SAKUYA = 8,
            REMILIA = 9, FLANDORE = 10, YUYUKO = 19, YUKARI = 21, WRIGGLE = 23, YUUKA = 33, NITORI = 39,
            SANAE = 41, KANAKO = 42, SUWAKO = 43, TENSHI = 45, MOKOU = 30, TOZIKO = 65, KAGUYA = 29, OTHER = 254;

    public final Random rand = new Random();
    protected ServerLevel world;
    private int end;
    private int remove;
    public int time;
    public int level;
    public SpellCardEntity card;
    public LivingEntity user;
    public LivingEntity target;
    protected double cardPosX, cardPosY, cardPosZ;
    protected double userPosX, userPosY, userPosZ;
    protected double targetPosX, targetPosY, targetPosZ;
    private int needLevel;
    private int originalUserName;

    protected X1SpellCard() {
        setNeedLevel(1);
    }

    public void init(ServerLevel world, SpellCardEntity card, LivingEntity user, LivingEntity target, int level) {
        this.world = world;
        this.card = card;
        this.user = user;
        this.target = target;
        this.time = 0;
        this.level = level;
    }

    /** THSpellCard.onUpdate: snapshot positions, run the card, advance time. */
    public boolean onUpdate() {
        cardPosX = card.getX();
        cardPosY = card.getY();
        cardPosZ = card.getZ();
        userPosX = user.getX();
        userPosY = X1Danmaku.getPosYFromEye(user);
        userPosZ = user.getZ();
        targetPosX = target.getX();
        targetPosY = target.getY() + target.getBbHeight() / 2.0D;
        targetPosZ = target.getZ();
        spellcard_main();
        time++;
        return true;
    }

    public void spellcard_main() {}

    /** In a Sakuya time stop that lets this card move, its end time is pushed back by a tick. */
    public void specialProcessInTimeStop() {
        if (canMoveInTimeStop()) setEndTime(getEndTime() + 1);
    }

    public boolean canMoveInTimeStop() {
        return false;
    }

    // ---- 1.7.10 field access used by the cards ----

    /** user.getLookVec() */
    protected Vec3d lookVec() { return X1Danmaku.look(user); }
    /** user.rotationYaw / rotationPitch */
    protected float userYaw() { return user.getYRot(); }
    protected float userPitch() { return user.getXRot(); }
    /** target.isDead */
    protected boolean targetDead() { return target == null || !target.isAlive(); }

    /** Special shots this card registers (ISpecialShot); called once at mod setup. */
    public void registerSpecialShots() {}

    // ---- helpers THSpellCard exposes directly ----

    public Vec3d pos(double x, double y, double z) { return new Vec3d(x, y, z); }
    public Vec3d pos_User() { return pos(userPosX, userPosY, userPosZ); }

    /** pos_User(angle, distance): X1 adds angle.y without the distance factor. */
    public Vec3d pos_User(Vec3d angle, double distance) {
        Vec3d a = dev.kneekura.fivedifficulties.core.x1.X1ShotSpecials.normalize(angle);
        return pos(userPosX + a.x() * distance, userPosY + a.y(), userPosZ + a.z() * distance);
    }

    public Vec3d pos_Card() { return pos(cardPosX, cardPosY, cardPosZ); }
    public Vec3d pos_Target() { return X1Danmaku.pos_Living(target); }
    // Static so they do not hide the X1Danmaku overloads the cards import statically.
    public static Vec3d angle(double x, double y, double z) { return X1Danmaku.angle(x, y, z); }
    public static Vec3d angle(float yaw, float pitch) { return X1Danmaku.angle(yaw, pitch); }
    public Vec3d angle_UserToTarget() { return X1Danmaku.angle_ToPos(pos_User(), pos_Target()); }
    public Vec3d angle_Random() { return X1Danmaku.angle_Random(rand); }
    public static Vec3d angle_Random(Random r) { return X1Danmaku.angle_Random(r); }
    public static Vec3d rotate_Default() { return X1Danmaku.rotate_Default(); }
    public static Vec3d gravity_Zero() { return X1Danmaku.gravity_Zero(); }
    public static Vec3d gravity_Default() { return X1Danmaku.gravity_Default(); }
    public static Vec3d getVecFromAngle(float yaw, float pitch) { return X1Danmaku.getVecFromAngle(yaw, pitch); }
    public static Vec3d getVecFromAngle(float yaw, float pitch, double force) {
        return X1Danmaku.getVecFromAngle(yaw, pitch, force);
    }

    public static X1ShotData shot(int form, int color, float size, float damage, int delay, int end, int special) {
        return X1ShotData.shot(form, color, size, damage, delay, end, special);
    }

    public static X1ShotData shot(int form, int color, float size, float damage, int delay, int end) {
        return shot(form, color, size, damage, delay, end, 0);
    }

    public static X1ShotData shot(int form, int color, float size, float damage) {
        return shot(form, color, size, damage, 0, 80);
    }

    public static X1ShotData shot(int form, int color, int delay, int end, int special) {
        return shot(form, color, X1ShotTables.SIZE[form], X1ShotTables.DAMAGE[form], delay, end, special);
    }

    public static X1ShotData shot(int form, int color, int delay, int end) {
        return shot(form, color, delay, end, 0);
    }

    public static X1ShotData shot(int form, int color) {
        return shot(form, color, 0, 80, 0);
    }

    // ---- data ----

    public int getNeedLevel() { return needLevel; }
    public int getRemoveTime() { return remove; }
    public int getEndTime() { return end; }
    public int getOriginalUserName() { return originalUserName; }
    public int getSpellCardCircleColor() { return X1ShotTables.RED; }
    public void setNeedLevel(int level) { needLevel = level; }
    public void setRemoveTime(int time) { remove = time; }
    public void setEndTime(int time) { end = time; }
    public void setOriginalUserName(int id) { originalUserName = id; }
}
