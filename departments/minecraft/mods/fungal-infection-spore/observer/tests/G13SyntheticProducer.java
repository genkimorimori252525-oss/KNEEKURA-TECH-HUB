import org.kneekura.sporeobserver.core.TraceSink;
import java.nio.file.Path;
import java.util.Map;

/** Synthetic, owned data. Never claims a Forge server observation. */
public final class G13SyntheticProducer {
    public static void main(String[] args) throws Exception {
        if (args.length != 1) throw new IllegalArgumentException("expected output path");
        var meta = Map.<String,Object>ofEntries(
            Map.entry("ch","spore_meta"),Map.entry("schema","kneekura.spore.observation.v1"),
            Map.entry("run_id","synthetic-g13-cross-language"),Map.entry("scenario","G13"),
            Map.entry("world_id","test_world"),Map.entry("dimension","minecraft:overworld"),
            Map.entry("jar_sha256","d20c4be6606f9752ecfd964eba625363eb76a28e327d67fe6dda4be748401489"),
            Map.entry("minecraft","1.20.1"),Map.entry("loader","Forge"),Map.entry("seed",20261011),
            Map.entry("world_disposable",true),Map.entry("origin","synthetic_fixture"),
            Map.entry("physical_side","DEDICATED_SERVER"),Map.entry("observer_identity","synthetic_java_writer_not_attested"));
        long tick=100;
        try (var writer=new TraceSink(Path.of(args[0]),meta)) {
            for(int proto : new int[]{1,4,16}) {
                for(int i=0;i<200;i++) {
                    double ms = 3.0+0.1*proto+(i%7)*0.05;
                    writer.event(tick++,"minecraft:overworld","server_tick_sample",Map.of(
                        "proto_count",proto,"infected_count",0,"signal_count",0,
                        "tick_ms",ms,"measurement_scope","SYNTHETIC_EXERCISE_ONLY"));
                }
            }
            writer.finish("completed");
        }
        System.out.println("G13_SYNTHETIC_ROWS=600");
    }
}
