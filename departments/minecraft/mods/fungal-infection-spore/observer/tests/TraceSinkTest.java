import org.kneekura.sporeobserver.core.TraceSink;
import java.nio.file.*;
import java.util.Map;
public final class TraceSinkTest {
    public static void main(String[] args) throws Exception {
        Path dir=Files.createTempDirectory("spore-owned-trace-");
        Path target=dir.resolve("run.jsonl");
        try {
            var meta=Map.<String,Object>ofEntries(
                Map.entry("ch","spore_meta"),Map.entry("schema","kneekura.spore.observation.v1"),
                Map.entry("run_id","portable-1"),Map.entry("scenario","G13"),
                Map.entry("world_id","test_world"),Map.entry("dimension","minecraft:overworld"),
                Map.entry("jar_sha256","d20c4be6606f9752ecfd964eba625363eb76a28e327d67fe6dda4be748401489"),
                Map.entry("minecraft","1.20.1"),Map.entry("loader","Forge"),Map.entry("seed",42),
                Map.entry("world_disposable",true),Map.entry("origin","synthetic_fixture"),
                Map.entry("physical_side","DEDICATED_SERVER"),Map.entry("observer_identity","portable_self_test"));
            try (var writer=new TraceSink(target,meta)) {
                writer.event(100,"minecraft:overworld","server_tick_sample",Map.of("proto_count",1,"signal_count",0,"infected_count",10,"tick_ms",4.1));
                writer.event(101,"minecraft:overworld","server_tick_sample",Map.of("proto_count",1,"signal_count",0,"infected_count",10,"tick_ms",5.2));
                if (writer.eventCount()!=2)throw new AssertionError("counter");
                writer.finish("completed");
            }
            if (Files.readAllLines(target).size()!=4)throw new AssertionError("4 lines expected");
            try { new TraceSink(target,meta); throw new AssertionError("must not overwrite"); }
            catch (FileAlreadyExistsException expected) {}
            if (!TraceSink.mapToJson(Map.of("x","a\"\n\\\u0001")).contains("\\u0001"))throw new AssertionError("json escapes");
            System.out.println("PASS PORTABLE_CORE: "+target);
        } finally {
            // The test deletes only its own temporary data. Never deletes a Minecraft world.
            Files.deleteIfExists(target); Files.delete(dir);
        }
    }
}
