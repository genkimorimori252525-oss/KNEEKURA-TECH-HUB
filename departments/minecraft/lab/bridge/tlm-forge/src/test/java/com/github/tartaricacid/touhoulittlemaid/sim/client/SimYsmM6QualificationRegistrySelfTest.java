package com.github.tartaricacid.touhoulittlemaid.sim.client;

/** Standalone JDK-only regression for controlled E2 qualification gating. */
public final class SimYsmM6QualificationRegistrySelfTest {
    public static void main(String[] args) {
        SimYsmM6QualificationRegistry.clear();
        String id = "map|root.vars|variable.wuqi";

        require(!SimYsmM6QualificationRegistry.isQualified("run-a|level-a", "u", "wuqi", id),
                "candidate must start unqualified");
        require(SimYsmM6QualificationRegistry.qualify("run-a|level-a", "u", "v.wuqi", id),
                "valid candidate should qualify");
        require(SimYsmM6QualificationRegistry.isQualified("run-a|level-a", "u", "wuqi", id),
                "normalized variable should match qualification");
        require(!SimYsmM6QualificationRegistry.isQualified("run-a|level-b", "u", "wuqi", id),
                "qualification must not cross runtime scope identity");
        require(!SimYsmM6QualificationRegistry.isQualified("run-a|level-a", "other", "wuqi", id),
                "qualification must not cross entity identity");
        require(!SimYsmM6QualificationRegistry.isQualified(
                        "run-a|level-a", "u", "wuqi", "field|root.other.wuqi"),
                "qualification must not cross stable candidate identity");
        require(!SimYsmM6QualificationRegistry.qualify("", "u", "wuqi", id),
                "blank runtime scope must fail closed");

        SimYsmM6QualificationRegistry.clear();
        require(SimYsmM6QualificationRegistry.size() == 0, "clear must remove qualifications");

        System.out.println("SimYsmM6QualificationRegistrySelfTest OK");
    }

    private static void require(boolean ok, String message) {
        if (!ok) throw new AssertionError(message);
    }
}
