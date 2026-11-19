import org.kneekura.sporeobserver.core.GoalSnapshotSelection;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/** Unit test of owned Goal snapshot prioritization, no Forge or Spore runtime. */
public final class GoalSnapshotSelectionTest {
    private static Map<String,Object> row(int id, String type, int priority, boolean running) {
        return Map.of("goal_instance_id", id, "selector", "goal",
                "goal_class", type, "priority", priority,
                "flags", List.of("MOVE"), "running", running);
    }
    public static void main(String[] args) {
        List<Map<String,Object>> rows = new ArrayList<>();
        for(int i=1; i<=16; i++) {
            rows.add(row(i,"synthetic.GenericHighPriorityGoal"+i,0,false));
        }
        rows.add(row(101,"com.Harbinger.Spore.Sentities.BasicInfected.InfectedWitch$3",4,false));
        rows.add(row(102,"com.Harbinger.Spore.Sentities.BasicInfected.InfectedWitch$4",4,false));
        rows.add(row(103,"com.Harbinger.Spore.Sentities.BasicInfected.InfectedWitch$5",4,false));
        rows.add(row(104,"com.Harbinger.Spore.Sentities.AI.LocHiv.SearchAreaGoal",4,false));
        rows.add(row(105,"synthetic.GenericRunningGoal",8,true));
        List<Map<String,Object>> got = GoalSnapshotSelection.select(rows);
        if(got.size()!=12)throw new AssertionError("capture must be bounded");
        for(int id=101; id<=104; id++){
            final int find=id;
            if(got.stream().noneMatch(e->(int)e.get("goal_instance_id")==find))
                throw new AssertionError("lost watched Witch/Move goal id="+id);
        }
        if(got.stream().noneMatch(e->(int)e.get("goal_instance_id")==105))
            throw new AssertionError("lost running goal");
        if(GoalSnapshotSelection.rank(rows.get(0))!=2)
            throw new AssertionError("generic goal rank");
        if(GoalSnapshotSelection.rank(rows.get(16))!=0)
            throw new AssertionError("watched goal rank");
        if(GoalSnapshotSelection.rank(rows.get(20))!=1)
            throw new AssertionError("running goal rank");
        if(rows.size()!=21)throw new AssertionError("test should not change source registry");
        System.out.println("PASS GOAL_SNAPSHOT_SELECTION: retained Witch priority-4 support and running goals under 12-item cap");
    }
}
