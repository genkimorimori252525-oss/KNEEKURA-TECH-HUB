package com.github.tartaricacid.touhoulittlemaid.sim.client;

import java.util.Map;

/** Standalone JDK-only regression for simple Molang literal assignment extraction. */
public final class SimMolangLiteralAssignmentsSelfTest {
    public static void main(String[] args) {
        var parsed = SimMolangLiteralAssignments.parse(
                "(v.wuqi = 0); variable.foo=+1.5; v.bar = -2e-1");
        require(parsed.size() == 3, "expected three simple assignments");
        require("wuqi".equals(parsed.get(0).variable()) && parsed.get(0).value() == 0.0d,
                "wuqi assignment mismatch");
        require("foo".equals(parsed.get(1).variable()) && parsed.get(1).value() == 1.5d,
                "foo assignment mismatch");
        require("bar".equals(parsed.get(2).variable()) && parsed.get(2).value() == -0.2d,
                "bar assignment mismatch");

        require(SimMolangLiteralAssignments.parse("v.roaming.c = 1").isEmpty(),
                "dotted variable must fail closed");
        require(SimMolangLiteralAssignments.parse("v.wuqi == 1").isEmpty(),
                "comparison must not be treated as assignment");
        require(SimMolangLiteralAssignments.parse("v.wuqi = math.random(0,1)").isEmpty(),
                "computed RHS must not be treated as literal evidence");

        require(SimMolangLiteralAssignments.containsWholeExpression(
                        "(v.wuqi=0); (v.foo=1)", "(v.wuqi = 0)"),
                "first merged handler expression should match");
        require(SimMolangLiteralAssignments.containsWholeExpression(
                        "(v.wuqi=0); (v.foo=1)", "(v.foo = 1)"),
                "last merged handler expression should match");
        require(!SimMolangLiteralAssignments.containsWholeExpression(
                        "v.foo=10", "v.foo=1"),
                "partial numeric prefix must not match another handler expression");

        Map<String, SimMolangLiteralAssignments.Assignment> last =
                SimMolangLiteralAssignments.lastByVariable("v.wuqi=0; v.wuqi=1");
        require(last.size() == 1 && last.get("wuqi").value() == 1.0d,
                "last assignment in one command must win");

        System.out.println("SimMolangLiteralAssignmentsSelfTest OK");
    }

    private static void require(boolean ok, String message) {
        if (!ok) throw new AssertionError(message);
    }
}
