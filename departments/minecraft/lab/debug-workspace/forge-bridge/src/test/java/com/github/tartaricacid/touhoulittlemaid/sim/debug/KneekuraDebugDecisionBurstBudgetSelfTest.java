package com.github.tartaricacid.touhoulittlemaid.sim.debug;

public final class KneekuraDebugDecisionBurstBudgetSelfTest {
    public static void main(String[] args) {
        var context = new KneekuraDebugDecisionBurstBudget.Context("session", "run", "snapshot", 1, 0, 7,
                "11111111-2222-3333-4444-555555555555", "minecraft:overworld");
        var budget = new KneekuraDebugDecisionBurstBudget(context, 100, 5, 3, 100);
        require(budget.claim(context,100,20), "first original invocation");
        require(budget.claim(context,104,30), "last allowed tick");
        require(!budget.claim(context,105,20), "duration is finite/exclusive");
        require(budget.reason().equals("WINDOW_ENDED"), "window outcome");
        require(!budget.claim(context,104,10), "closed burst cannot replay");
        budget = new KneekuraDebugDecisionBurstBudget(context,100,5,2,100);
        require(budget.claim(context,100,20) && budget.claim(context,100,20), "same-tick invocations preserve count");
        require(!budget.claim(context,100,20) && budget.reason().equals("EVENT_BUDGET"), "bounded events");
        budget = new KneekuraDebugDecisionBurstBudget(context,100,5,3,100);
        require(budget.claim(context,100,100), "exact byte budget fits");
        require(!budget.claim(context,101,1) && budget.reason().equals("BYTE_BUDGET"), "bounded retained bytes");
        for (var other : new KneekuraDebugDecisionBurstBudget.Context[] {
                new KneekuraDebugDecisionBurstBudget.Context("other","run","snapshot",1,0,7,context.subjectUuid(),context.dimension()),
                new KneekuraDebugDecisionBurstBudget.Context("session","other","snapshot",1,0,7,context.subjectUuid(),context.dimension()),
                new KneekuraDebugDecisionBurstBudget.Context("session","run","other",1,0,7,context.subjectUuid(),context.dimension()),
                new KneekuraDebugDecisionBurstBudget.Context("session","run","snapshot",2,0,7,context.subjectUuid(),context.dimension()),
                new KneekuraDebugDecisionBurstBudget.Context("session","run","snapshot",1,1,7,context.subjectUuid(),context.dimension()),
                new KneekuraDebugDecisionBurstBudget.Context("session","run","snapshot",1,0,8,context.subjectUuid(),context.dimension()),
                new KneekuraDebugDecisionBurstBudget.Context("session","run","snapshot",1,0,7,"other",context.dimension()),
                new KneekuraDebugDecisionBurstBudget.Context("session","run","snapshot",1,0,7,context.subjectUuid(),"other")}) {
            budget = new KneekuraDebugDecisionBurstBudget(context,100,5,3,100);
            require(!budget.claim(other,100,10) && budget.reason().equals("CONTEXT_CHANGED"), "every generation boundary closes capture");
            require(!budget.claim(context,100,10), "cannot return to earlier generation");
        }
        budget = new KneekuraDebugDecisionBurstBudget(context,100,5,3,100);
        require(budget.claim(context,103,10), "monotonic sample");
        require(!budget.claim(context,102,10) && budget.reason().equals("CLOCK_CHANGED"), "time reversal closes capture");
        for (int[] limits : new int[][]{{0,3,100},{201,3,100},{5,0,100},{5,257,100},{5,3,0},{5,3,524289}}) {
            try {
                new KneekuraDebugDecisionBurstBudget(context,100,limits[0],limits[1],limits[2]);
                throw new AssertionError("invalid budget accepted");
            } catch (IllegalArgumentException expected) { }
        }
        System.out.println("Decision burst budgets: finite ticks/events/bytes, eight identity fences, no replay");
    }
    private static void require(boolean condition, String message) { if(!condition)throw new AssertionError(message); }
}
