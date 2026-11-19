package dev.kneekura.fivedifficulties.core;

import dev.kneekura.fivedifficulties.core.math.Vec3d;
import dev.kneekura.fivedifficulties.core.x1.X1LaserData;
import dev.kneekura.fivedifficulties.core.x1.X1LaserPatterns;
import dev.kneekura.fivedifficulties.core.x1.X1ShotMotion;
import dev.kneekura.fivedifficulties.core.x1.X1ShotTables;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/** P10 regression for the X1 laser emitters and the EntityTHLaser angle rule. */
public final class X1LaserCoreRegression {
    private static final Vec3d SOUTH = new Vec3d(0, 0, 1);

    private record Spawn(Vec3d pos, Vec3d angle, X1LaserData laser) {}

    private X1LaserCoreRegression() {}

    public static void main(String[] args) {
        circleEmitsWayPlusOne();
        sphereBackLaserUsesFrontPosition();
        createLaserAResolvesRandomPermanently();
        wideReRollsRandomPerRay();
        ringKeepsConeAngle();
        laserAngleWrapsYaw();
        shotIdCarriesForm();
        System.out.println("X1_LASER_CORE_REGRESSION_PASS");
    }

    private static List<Spawn> capture(java.util.function.Consumer<X1LaserPatterns> emit) {
        List<Spawn> out = new ArrayList<>();
        emit.accept(new X1LaserPatterns(new Random(7L), (pos, angle, f, l, a, g, laser) -> out.add(new Spawn(pos, angle, laser))));
        return out;
    }

    private static double angleBetween(Vec3d a, Vec3d b) {
        double dot = (a.x() * b.x() + a.y() * b.y() + a.z() * b.z()) / (a.length() * b.length());
        return Math.toDegrees(Math.acos(Math.max(-1, Math.min(1, dot))));
    }

    private static void circleEmitsWayPlusOne() {
        List<Spawn> s = capture(p -> p.createCircleLaserA(Vec3d.ZERO, SOUTH, 0.6, 0.6, 0, Vec3d.ZERO,
                X1LaserData.laser(1, 0.1F, 5F, 5F), 4, 0.1));
        require(s.size() == 5, "circle laser way 4 emits 5");
        require(angleBetween(s.get(0).angle(), s.get(4).angle()) < 1e-4, "first and last coincide");
        near(angleBetween(s.get(0).angle(), s.get(1).angle()), 90, 1e-3, "90 degree steps");
    }

    private static void sphereBackLaserUsesFrontPosition() {
        List<Spawn> s = capture(p -> p.createSphereLaserA(Vec3d.ZERO, SOUTH, 0.6, 0.6, 0, Vec3d.ZERO,
                X1LaserData.laser(2, 0.1F, 5F, 5F), 8, 0.2, 0F));
        require(s.size() == 8, "sphere way 8 = {1,3,3,1}");
        Spawn back = s.get(7);
        near(angleBetween(back.angle(), SOUTH), 180, 1e-9, "back laser points backwards");
        near(back.pos().z(), 0.2, 1e-12, "X1 spawns the back laser at the front position");
    }

    private static void createLaserAResolvesRandomPermanently() {
        X1LaserData laser = X1LaserData.laser(X1ShotTables.RANDOM, 0.1F, 5F, 5F);
        List<Spawn> s = capture(p -> {
            p.createLaserA(Vec3d.ZERO, SOUTH, 0.6, 0.6, 0, Vec3d.ZERO, laser);
            p.createLaserA(Vec3d.ZERO, SOUTH, 0.6, 0.6, 0, Vec3d.ZERO, laser);
        });
        require(laser.color != X1ShotTables.RANDOM, "createLaserA does not restore RANDOM");
        require(s.get(0).laser().color == s.get(1).laser().color, "second laser reuses the resolved colour");
    }

    private static void wideReRollsRandomPerRay() {
        X1LaserData laser = X1LaserData.laser(X1ShotTables.RANDOM, 0.1F, 5F, 5F);
        List<Spawn> s = capture(p -> p.createWideLaserA(Vec3d.ZERO, SOUTH, 0.6, 0.6, 0, Vec3d.ZERO, laser, 12, 60F, 0.1));
        require(s.stream().map(x -> x.laser().color).distinct().count() > 1, "wide laser re-rolls per ray");
    }

    private static void ringKeepsConeAngle() {
        Vec3d aim = new Vec3d(0.2, 0.3, 0.9).normalized();
        List<Spawn> s = capture(p -> p.createRingLaserA(Vec3d.ZERO, aim, 0.6, 0.6, 0, Vec3d.ZERO,
                X1LaserData.laser(3, 0.1F, 5F, 5F), 6, 0.1, 30F, 0F));
        require(s.size() == 6, "6 ring lasers");
        for (Spawn x : s) near(angleBetween(x.angle(), aim), 15, 1e-3, "ring cone half-angle");
    }

    private static void laserAngleWrapsYaw() {
        X1ShotMotion m = new X1ShotMotion(Vec3d.ZERO, new Vec3d(0, 0, -1), new Vec3d(0, 1, 0), 0F, 9999, 0, 0, 0,
                Vec3d.ZERO, 0);
        m.laserAngle = true;
        m.updateAngle();
        near(m.yaw, -180.0, 1e-4, "yaw 180 wraps to -180");
        m.angle = new Vec3d(1, 1, 0);
        m.updateAngle();
        near(m.yaw, 90.0, 1e-4, "laser yaw follows the angle, not the (zero) motion");
        near(m.pitch, 45.0, 1e-4, "laser pitch follows the angle");
    }

    private static void shotIdCarriesForm() {
        require(X1LaserData.laser(X1LaserData.LASER_GUNGNIR, 1, 0.1F, 5F, 5F, 0, 80, 0).shotId() == 9, "gungnir id");
        require(X1LaserData.laser(X1ShotTables.RED + 16, 0.6F, 20.8F, 7.0F, 0, 30, X1ShotTables.FIRE).shotId() == 16,
                "Laevateinn passes RED + 16 as the colour");
    }

    private static void near(double actual, double expected, double tol, String what) {
        if (Math.abs(actual - expected) > tol) throw new AssertionError(what + ": expected " + expected + " got " + actual);
    }

    private static void require(boolean ok, String what) {
        if (!ok) throw new AssertionError(what);
    }
}
