import org.kneekura.sporeobserver.core.GoalRunningStateDiff;
import java.util.List;
import java.util.Map;
import java.util.Set;

/** Owned Java 17 tests; NO Minecraft/Spore required. */
public final class GoalRunningStateDiffTest {
    private static Map<String,Object> goal(int id, boolean running) {
        return Map.of("goal_instance_id",id,"running",running,"priority",4,
                "selector","goal","goal_class","synthetic.WitchBuffGoal");
    }
    private static Map<String,Object> snapshot(String uuid, boolean truncated, Map<String,Object>... goals) {
        return Map.of("entity_uuid",uuid,"truncated",truncated,"goals",List.of(goals));
    }
    private static int count(Map<String,Object> delta) {
        return ((Number)delta.get("observed_state_changes")).intValue();
    }
    public static void main(String[] args) {
        var diff=new GoalRunningStateDiff();
        if (count(diff.observe(snapshot("witch-a",false,goal(7,false)))) != 0)throw new AssertionError("first is baseline");
        var change=diff.observe(snapshot("witch-a",false,goal(7,true)));
        if (count(change)!=1)throw new AssertionError("missed observed running change");
        if (!Boolean.TRUE.equals(((List<Map<String,Object>>)change.get("changes")).get(0).get("current_running")))
            throw new AssertionError("incorrect running state");
        if (count(diff.observe(snapshot("witch-a",false,goal(7,true))))!=0)
            throw new AssertionError("unchanged goal counted");
        // Truncation: omission of a goal cannot imply it stopped.
        if (count(diff.observe(snapshot("witch-a",true,goal(8,false))))!=0)
            throw new AssertionError("omission fabricated stop");
        if (count(diff.observe(snapshot("witch-a",false,goal(7,false))))!=0)
            throw new AssertionError("reappearing goal should be a new baseline");
        // No state changes inferred over a gap in observed Mobs.
        diff.retainOnly(Set.of());
        if (count(diff.observe(snapshot("witch-a",false,goal(7,true))))!=0)
            throw new AssertionError("gap was misinterpreted as a transition");
        boolean duplicatedRejected=false;
        try {diff.observe(snapshot("witch-b",false,goal(1,false),goal(1,true)));}
        catch (IllegalArgumentException expected) {duplicatedRejected=true;}
        if (!duplicatedRejected)throw new AssertionError("duplicate ID should reject snapshot");
        diff.clear();
        System.out.println("PASS GOAL_RUNNING_STATE_DIFF: baseline, transition, truncation, gap and duplicate");
    }
}
