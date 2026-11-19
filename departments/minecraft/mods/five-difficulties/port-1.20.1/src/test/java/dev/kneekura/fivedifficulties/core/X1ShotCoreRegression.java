package dev.kneekura.fivedifficulties.core;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1ShotData;
import dev.kneekura.fivedifficulties.core.x1.X1ShotMotion;
import dev.kneekura.fivedifficulties.core.x1.X1ShotPatterns;
import dev.kneekura.fivedifficulties.core.x1.X1ShotTables;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/** P8 regression for the generic X1 THShot kernel and the THShotLib emission helpers. */
public final class X1ShotCoreRegression {
    private static final Vec3d UP = new Vec3d(0, 1, 0);
    private static final Vec3d SOUTH = new Vec3d(0, 0, 1);

    private X1ShotCoreRegression() {}

    public static void main(String[] args) {
        lifetimeIncludesDelay();
        accelerationClampsAtLimit();
        decelerationSnapsToLimit();
        gravityAccumulates();
        frozenTickChangesNothing();
        yawRotationFollowsAxis();
        speedIsFloatRounded();
        tablesAreLiteral();
        wideShotSpreadsEvenly();
        wideShotWithOneWayUsesHalfWidthOffset();
        circleShotOffsetsEvenWays();
        ringShotKeepsConeAngle();
        randomRingStaysInsideCone();
        sphereShotCountsRings();
        rainbowAndRandomColours();
        System.out.println("X1_SHOT_CORE_REGRESSION_PASS");
    }

    /** Minimal 1.7.10/1.20.1 world loop: ticksExisted++ then onUpdate; death check first. */
    private static final class World implements X1ShotMotion.Hooks {
        int animation;
        int ticks;
        int moves;
        boolean dead;
        int deathTick = -1;

        World(int delay) {
            animation = X1ShotMotion.initialAnimationCount(delay);
        }

        public boolean authoritative() { return true; }
        public int animationCount() { return animation; }
        public void setAnimationCount(int value) { animation = value; }

        X1ShotMotion.Step step(X1ShotMotion m, int end) {
            ticks++;
            if (dead) return null; // removed by the world after the death tick
            if (X1ShotMotion.isPastEnd(animation, end)) {
                // X1 setDead() does not return: the rest of onUpdate still runs this tick.
                dead = true;
                deathTick = ticks;
            }
            Vec3d before = m.position;
            X1ShotMotion.Step s = m.tick(ticks, this);
            if (!m.position.equals(before)) moves++;
            return s;
        }
    }

    private static X1ShotMotion straight(double first, double limit, double accel, Vec3d gravity) {
        return new X1ShotMotion(Vec3d.ZERO, SOUTH, UP, 0F, 9999, first, limit, accel, gravity, 0);
    }

    private static void lifetimeIncludesDelay() {
        for (int delay : new int[] {0, 5}) {
            X1ShotMotion m = straight(0.5, 0.5, 0, Vec3d.ZERO);
            World w = new World(delay);
            int delaySteps = 0;
            while (!w.dead && w.ticks < 200) {
                if (w.step(m, 80) == X1ShotMotion.Step.DELAY) delaySteps++;
            }
            require(w.deathTick == 83, "delay " + delay + ": X1 shot with end=80 dies at tick 83, got " + w.deathTick);
            require(delaySteps == delay, "delay ticks " + delaySteps);
            require(w.moves == 83 - delay, "delay " + delay + ": moves " + w.moves);
            near(m.position.z(), (83 - delay) * (double) (float) 0.5, 1e-9, "distance");
        }
    }

    private static void accelerationClampsAtLimit() {
        X1ShotMotion m = straight(0.1, 0.5, 0.15, Vec3d.ZERO);
        World w = new World(0);
        double[] expected = {0.25, 0.40, 0.50, 0.50};
        for (double e : expected) {
            w.step(m, 80);
            near(m.motion.z(), e, 1e-6, "accelerated speed");
        }
    }

    private static void decelerationSnapsToLimit() {
        X1ShotMotion m = straight(1.0, 0.2, -0.3, Vec3d.ZERO);
        World w = new World(0);
        double[] expected = {0.7, 0.4, 0.2, 0.2};
        for (double e : expected) {
            w.step(m, 80);
            near(m.motion.z(), e, 1e-6, "decelerated speed");
        }
    }

    private static void gravityAccumulates() {
        X1ShotMotion m = straight(0.5, 0.5, 0, X1ShotPatterns.gravity(-0.03));
        World w = new World(0);
        for (int i = 1; i <= 4; i++) {
            w.step(m, 80);
            near(m.motion.y(), -0.03 * i, 1e-12, "gravity carried through lastMotion");
        }
        near(m.position.y(), -0.03 * (1 + 2 + 3 + 4), 1e-12, "gravity drop");
    }

    private static void frozenTickChangesNothing() {
        X1ShotMotion m = straight(0.5, 0.5, 0, Vec3d.ZERO);
        World w = new World(0);
        w.step(m, 80);
        w.step(m, 80);
        Vec3d pos = m.position;
        int anim = w.animation;
        // Time stop: the world does not advance ticksExisted.
        require(m.tick(w.ticks, w) == X1ShotMotion.Step.FROZEN, "same ticksExisted is frozen");
        require(m.position.equals(pos) && w.animation == anim, "frozen tick changed state");
    }

    private static void yawRotationFollowsAxis() {
        X1ShotMotion m = new X1ShotMotion(Vec3d.ZERO, SOUTH, UP, 10F, 9999, 0.5, 0.5, 0, Vec3d.ZERO, 0);
        World w = new World(0);
        w.step(m, 80);
        double expected = Math.toDegrees(Math.atan2(m.angle.x(), m.angle.z()));
        near(expected, 10.0, 1e-4, "one tick of 10 deg/tick rotation about +Y");
        near(m.yaw, 10.0, 1e-3, "X1 yaw follows motion");
    }

    private static void speedIsFloatRounded() {
        X1ShotMotion m = straight(0.1, 0.1, 0, Vec3d.ZERO);
        m.motion = new Vec3d(0.1, 0.2, 0.3);
        double raw = Math.sqrt(0.14);
        require(m.speed() == (double) (float) raw, "sqrt_double float rounding");
    }

    private static void tablesAreLiteral() {
        require(X1ShotTables.SIZE[X1ShotTables.FORM_BIG] == 0.90F, "BIG size");
        require(X1ShotTables.DAMAGE[X1ShotTables.FORM_BIGLIGHT] == 6.8F, "BIGLIGHT damage");
        require(X1ShotTables.ITEM_FORM[3] == X1ShotTables.FORM_BIG, "item 3 is bigShot");
        require(X1ShotTables.ITEM_SHOT_TYPE_TRANS[3] == 30, "item 3 spawn distance form");
        X1ShotData d = X1ShotData.shot(X1ShotTables.FORM_HEART, X1ShotTables.AQUA);
        require(d.shotId() == 12 * 8 + 5, "shot id");
        require(X1ShotTables.formOf(d.shotId()) == 12 && X1ShotTables.colorOf(d.shotId()) == 5, "id decode");
        require(d.end == 80 && d.delay == 0 && d.size == 0.50F && d.damage == 3.2F, "ShotData defaults");
    }

    private record Spawn(Vec3d pos, Vec3d angle, float slope, Vec3d rotate, X1ShotData shot) {}

    private static List<Spawn> capture(java.util.function.Consumer<X1ShotPatterns> emit) {
        List<Spawn> out = new ArrayList<>();
        X1ShotPatterns p = new X1ShotPatterns(new Random(1201L),
                (pos, angle, slope, rotate, rs, re, f, l, a, g, shot) -> out.add(new Spawn(pos, angle, slope, rotate, shot)));
        emit.accept(p);
        return out;
    }

    private static double angleBetween(Vec3d a, Vec3d b) {
        double dot = (a.x() * b.x() + a.y() * b.y() + a.z() * b.z()) / (a.length() * b.length());
        return Math.toDegrees(Math.acos(Math.max(-1, Math.min(1, dot))));
    }

    private static double signedYaw(Vec3d v) {
        return Math.toDegrees(Math.atan2(v.x(), v.z()));
    }

    private static void wideShotSpreadsEvenly() {
        List<Spawn> s = capture(p -> p.createWideShot(Vec3d.ZERO, SOUTH, 0.5, 0.5, 0, Vec3d.ZERO,
                X1ShotData.shot(0, 0), 5, 60F, 1.0));
        require(s.size() == 5, "5-way");
        double[] yaws = s.stream().mapToDouble(sp -> signedYaw(sp.angle())).toArray();
        for (int i = 0; i < 5; i++) {
            near(Math.abs(yaws[i]), Math.abs(-30 + 15 * i), 1e-4, "wide offset " + i);
            near(sp(s, i).pos().length(), 1.0, 1e-9, "spawn distance");
        }
        require(Math.signum(yaws[0]) == -Math.signum(yaws[4]), "wide spans both sides");
    }

    private static Spawn sp(List<Spawn> s, int i) { return s.get(i); }

    private static void wideShotWithOneWayUsesHalfWidthOffset() {
        // ItemTHShot "Sector" with Number=1 uses wide = 3 degrees; X1 then fires at -wide/2.
        List<Spawn> s = capture(p -> p.createWideShot(Vec3d.ZERO, SOUTH, 0.5, 0.5, 0, Vec3d.ZERO,
                X1ShotData.shot(0, 0), 1, 3F, 0.3));
        require(s.size() == 1, "one shot");
        near(angleBetween(s.get(0).angle(), SOUTH), 1.5, 1e-4, "X1 one-way sector offset");
    }

    private static void circleShotOffsetsEvenWays() {
        List<Spawn> s = capture(p -> p.createCircleShot(Vec3d.ZERO, SOUTH, 0.5, 0.5, 0, Vec3d.ZERO,
                X1ShotData.shot(0, 0), 4, 0.3, 0F));
        require(s.size() == 4, "4-way circle");
        // X1: wide = 360 - 360/way, base += 360/(2*way) for even ways, so one shot stays on the aim.
        boolean straightAhead = false;
        for (Spawn a : s) {
            near(Math.abs(a.angle().y()), 0, 1e-9, "level circle stays horizontal");
            near(Math.abs(signedYaw(a.angle())) % 90, 0, 1e-3, "4-way circle on 90-degree steps");
            if (angleBetween(a.angle(), SOUTH) < 1e-3) straightAhead = true;
        }
        require(straightAhead, "even-way circle keeps one shot on the aim");
    }

    private static void ringShotKeepsConeAngle() {
        Vec3d aim = new Vec3d(0.3, 0.2, 0.9).normalized();
        List<Spawn> s = capture(p -> p.createRingShot(Vec3d.ZERO, aim, 0F, 9999, 0.5, 0.5, 0, Vec3d.ZERO,
                X1ShotData.shot(0, 0), 6, 0.3, 30F, 0F));
        require(s.size() == 6, "6-way ring");
        for (Spawn a : s) near(angleBetween(a.angle(), aim), 15.0, 1e-3, "ring cone half-angle");
    }

    private static void randomRingStaysInsideCone() {
        Vec3d aim = new Vec3d(-0.4, 0.1, 0.8).normalized();
        List<Spawn> s = capture(p -> p.createRandomRingShot(Vec3d.ZERO, aim, 0F, 9999, 0.5, 0.5, 0, Vec3d.ZERO,
                X1ShotData.shot(0, 0), 40, 0.3, 120F));
        require(s.size() == 40, "40 random shots");
        for (Spawn a : s) require(angleBetween(a.angle(), aim) <= 60.0 + 1e-3, "random ring cone");
    }

    private static void sphereShotCountsRings() {
        List<Spawn> s = capture(p -> p.createSphereShot(Vec3d.ZERO, SOUTH, 0F, UP, 0F, 99999, 0.5, 0.5, 0,
                Vec3d.ZERO, X1ShotData.shot(0, 0), 8, 0.3, 0F));
        require(s.size() == 8, "sphere way 8 = {1,3,3,1}");
        near(angleBetween(s.get(0).angle(), SOUTH), 0, 1e-9, "front");
        near(angleBetween(s.get(7).angle(), SOUTH), 180, 1e-9, "back");
        require(capture(p -> p.createSphereShot(Vec3d.ZERO, SOUTH, 0F, UP, 0F, 1, 0.5, 0.5, 0, Vec3d.ZERO,
                X1ShotData.shot(0, 0), 45, 0, 0F)).isEmpty(), "way beyond table emits nothing");
    }

    private static void rainbowAndRandomColours() {
        X1ShotData rainbow = X1ShotData.shot(0, X1ShotTables.RAINBOW);
        List<Spawn> s = capture(p -> p.createCircleShot(Vec3d.ZERO, SOUTH, 0.5, 0.5, 0, Vec3d.ZERO, rainbow, 7, 0, 0F));
        java.util.Set<Integer> colours = new java.util.HashSet<>();
        for (Spawn a : s) colours.add(a.shot().color);
        require(colours.size() == 7, "rainbow circle of 7 uses all 7 pattern colours");
        require(rainbow.color == X1ShotTables.RAINBOW, "rainbow restored after pattern");

        X1ShotData random = X1ShotData.shot(0, X1ShotTables.RANDOM);
        List<Spawn> r = capture(p -> p.createWideShot(Vec3d.ZERO, SOUTH, 0.5, 0.5, 0, Vec3d.ZERO, random, 5, 40F, 0));
        require(r.stream().map(a -> a.shot().color).distinct().count() == 1, "X1 random fan shares one colour");
        require(random.color == X1ShotTables.RANDOM, "random restored after fan");

        X1ShotData sphereRandom = X1ShotData.shot(0, X1ShotTables.RANDOM);
        capture(p -> p.createSphereShot(Vec3d.ZERO, SOUTH, 0F, UP, 0F, 1, 0.5, 0.5, 0, Vec3d.ZERO, sphereRandom, 5, 0, 0F));
        require(sphereRandom.color != X1ShotTables.RANDOM, "X1 sphere leaves RANDOM resolved (literal quirk)");
    }

    private static void near(double actual, double expected, double tol, String what) {
        if (Math.abs(actual - expected) > tol) {
            throw new AssertionError(what + ": expected " + expected + " got " + actual);
        }
    }

    private static void require(boolean ok, String what) {
        if (!ok) throw new AssertionError(what);
    }
}
