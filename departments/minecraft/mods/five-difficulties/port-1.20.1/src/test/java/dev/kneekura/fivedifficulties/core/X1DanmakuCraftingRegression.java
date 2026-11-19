package dev.kneekura.fivedifficulties.core;

import dev.kneekura.fivedifficulties.core.x1.X1DanmakuCrafting;
import dev.kneekura.fivedifficulties.core.x1.X1DanmakuCrafting.ColorInput;
import dev.kneekura.fivedifficulties.core.x1.X1DanmakuCrafting.Inputs;
import dev.kneekura.fivedifficulties.core.x1.X1DanmakuCrafting.Result;
import dev.kneekura.fivedifficulties.core.x1.X1DanmakuCrafting.Uses;
import dev.kneekura.fivedifficulties.core.x1.X1ShotTables;

/** X1 ContainerDanmakuCrafting / SlotDanmakuResult arithmetic, cases worked out from the X1 source. */
public final class X1DanmakuCraftingRegression {
    private X1DanmakuCraftingRegression() {}

    private static Inputs shot(int materialCount) {
        Inputs in = new Inputs();
        in.maxNumber = 32;
        in.materialCount = materialCount;
        return in;
    }

    private static void grid(Inputs in, String p) {
        for (int i = 0; i < 9; i++) in.matrix[i] = p.charAt(i) == '#';
    }

    private static void check(boolean ok, String what) {
        if (!ok) throw new AssertionError(what);
    }

    public static void main(String[] args) {
        // 1. untagged material, 3 small power for the number, a centre power: point form
        Inputs a = shot(1);
        a.wayCount = 3;
        grid(a, "....#....");
        Result r = X1DanmakuCrafting.result(a);
        check(r != null && r.number() == 4 && r.form() == 0 && r.color() == 8 && r.special() == 0 && r.count() == 1, "fresh: " + r);
        Uses u = X1DanmakuCrafting.uses(a);
        check(u.way() == 3 && u.material() == 1 && u.copy() == 0 && u.matrixEach() == 1, "fresh uses: " + u);

        // 2. tagged Number 30 + 10 → capped at 32; only 2 powers are taken
        Inputs b = shot(1);
        b.materialHasTag = true;
        b.number = 30;
        b.wayCount = 10;
        check(X1DanmakuCrafting.result(b).number() == 32, "number cap");
        check(X1DanmakuCrafting.uses(b).way() == 2, "number use: " + X1DanmakuCrafting.uses(b));

        // 3. bound: none + 2 → BOUND02 (41); BOUND02 + 3 → (byte) 44 → capped BOUND04 (43)
        Inputs c = shot(1);
        c.boundCount = 2;
        check(X1DanmakuCrafting.result(c).special() == X1ShotTables.BOUND01 + 1, "first bound");
        c.materialHasTag = true;
        c.number = 1;
        c.special = X1ShotTables.BOUND01 + 1;
        c.boundCount = 3;
        check(X1DanmakuCrafting.result(c).special() == X1ShotTables.BOUND01 + 3, "bound cap");
        check(X1DanmakuCrafting.uses(c).bound() == 2, "bound use 4 - 2: " + X1DanmakuCrafting.uses(c));

        // 4. the full grid needs more than 2 shots; otherwise the material's form stays
        Inputs d = shot(1);
        d.materialHasTag = true;
        d.number = 2;
        d.form = 3;
        grid(d, "#########");
        check(X1DanmakuCrafting.result(d).form() == 3, "sphere needs way > 2");
        d.wayCount = 1;
        check(X1DanmakuCrafting.result(d).form() == 4, "sphere with 3");
        Inputs d2 = shot(1);
        d2.maxNumber = 64;
        d2.wayCount = 40;
        grid(d2, "#########");
        check(X1DanmakuCrafting.result(d2) == null, "a sphere of more than 32 makes nothing");

        // 5. an unknown pattern makes nothing
        Inputs e = shot(1);
        grid(e, "#.......#");
        check(X1DanmakuCrafting.result(e) == null, "unknown pattern");

        // 6. colours: lapis (dye damage 4) → blue 1; gunpowder → RANDOM; diamond → RAINBOW
        Inputs f = shot(1);
        f.colorInput = ColorInput.DYE;
        f.dyeDamage = 4;
        check(X1DanmakuCrafting.result(f).color() == 1, "lapis is blue");
        f.colorInput = ColorInput.GUNPOWDER;
        check(X1DanmakuCrafting.result(f).color() == X1ShotTables.RANDOM, "gunpowder random");
        f.colorInput = ColorInput.DIAMOND;
        check(X1DanmakuCrafting.result(f).color() == X1ShotTables.RAINBOW, "diamond rainbow");

        // 7. copies: 5 materials, 10 points → 5 results, 5 materials and 4 points used
        Inputs g = shot(5);
        g.copyCount = 10;
        check(X1DanmakuCrafting.result(g).count() == 5, "copies capped by materials");
        Uses gu = X1DanmakuCrafting.uses(g);
        check(gu.material() == 5 && gu.copy() == 4, "copy uses: " + gu);

        // 8. speed is a byte: 60 + 70 wraps negative and becomes 64; 4 powers are used (64 - 60)
        Inputs h = shot(1);
        h.materialHasTag = true;
        h.number = 1;
        h.speed = 60;
        h.speedCount = 70;
        check(X1DanmakuCrafting.result(h).speed() == 64, "speed wrap");
        check(X1DanmakuCrafting.uses(h).speed() == 4, "speed use");

        // 9. laser table: Laser Max Number 8, no gravity / bound
        Inputs l = shot(1);
        l.laser = true;
        l.maxNumber = 8;
        l.wayCount = 20;
        l.gravityCount = 5;
        l.boundCount = 5;
        Result lr = X1DanmakuCrafting.result(l);
        check(lr.number() == 8 && lr.gravity() == 0 && lr.special() == 0, "laser: " + lr);
        check(X1DanmakuCrafting.uses(l).way() == 7, "untagged laser: 20 > 8 → 8 - 1 = 7 used");

        System.out.println("X1_DANMAKU_CRAFTING_REGRESSION_PASS");
    }
}
