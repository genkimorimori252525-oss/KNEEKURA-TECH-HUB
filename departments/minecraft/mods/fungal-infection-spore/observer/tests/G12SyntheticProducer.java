import org.kneekura.sporeobserver.core.TraceSink;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

/**
 * Source-owned synthetic G12 registration snapshots. This is not a recording
 * from Minecraft, GoalRuntimeSampler or Harbinger's mod.
 */
public final class G12SyntheticProducer {
    private static Map<String,Object> goal(String selector, String clazz,
                                            int priority, boolean running, String... flags) {
        return Map.of("selector", selector, "goal_class", clazz,
                "priority", priority, "running", running, "flags", List.of(flags));
    }
    public static void main(String[] args) throws Exception {
        if (args.length != 1)throw new IllegalArgumentException("Expected one output path");
        var metadata=Map.<String,Object>ofEntries(
                Map.entry("ch","spore_meta"),Map.entry("schema","kneekura.spore.observation.v1"),
                Map.entry("run_id","synthetic-g12-registration"),Map.entry("scenario","G12"),
                Map.entry("world_id","test_world"),Map.entry("dimension","minecraft:overworld"),
                Map.entry("jar_sha256","d20c4be6606f9752ecfd964eba625363eb76a28e327d67fe6dda4be748401489"),
                Map.entry("minecraft","1.20.1"),Map.entry("loader","Forge"),
                Map.entry("seed",20261011),Map.entry("world_disposable",true),
                Map.entry("origin","synthetic_fixture"),Map.entry("physical_side","DEDICATED_SERVER"),
                Map.entry("observer_identity","synthetic_java_registration_writer_not_attested"));
        try (TraceSink sink = new TraceSink(Path.of(args[0]),metadata)) {
            var witch=List.of(
                    goal("goal","com.Harbinger.Spore.Sentities.BasicInfected.InfectedWitch$3",4,true,"MOVE","LOOK"),
                    goal("goal","com.Harbinger.Spore.Sentities.BasicInfected.InfectedWitch$4",4,false,"MOVE","LOOK"),
                    goal("goal","com.Harbinger.Spore.Sentities.BasicInfected.InfectedWitch$5",4,false,"MOVE","LOOK"),
                    goal("goal","com.Harbinger.Spore.Sentities.AI.LocHiv.SearchAreaGoal",4,false,"MOVE"));
            sink.event(100,"minecraft:overworld","goal_registry_snapshot",
                    Map.of("entity_uuid","synthetic-witch","registered_goal_count",4,
                            "registered_running_count",1,"truncated",false,
                            "goals",witch,"capture_scope","SYNTHETIC_GOAL_REGISTRY_NO_GAME"));
            var brute=List.of(
                    goal("goal","com.Harbinger.Spore.Sentities.AI.TransportInfected",1,true,"TARGET"),
                    goal("goal","net.minecraft.world.entity.ai.goal.MeleeAttackGoal",3,false,"MOVE","LOOK"));
            sink.event(101,"minecraft:overworld","goal_registry_snapshot",
                    Map.of("entity_uuid","synthetic-brute","registered_goal_count",2,
                            "registered_running_count",1,"truncated",false,
                            "goals",brute,"capture_scope","SYNTHETIC_GOAL_REGISTRY_NO_GAME"));
            sink.finish("completed");
        }
        System.out.println("G12_SYNTHETIC_REGISTRATIONS=2");
    }
}
