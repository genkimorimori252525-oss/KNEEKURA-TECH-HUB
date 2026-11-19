package org.kneekura.techhub.warfarewings.physics;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

/** Synthetic negative-provenance fixtures only; no GameTest evidence here. */
public final class RealPhysicsTwinReplaySelfTest {
    private static int checks;
    private RealPhysicsTwinReplaySelfTest() {}

    private static void expectFailure(Path file, String aircraft, String message) throws Exception {
        checks++;
        boolean rejected=false;
        try {RealPhysicsTwinReplayMain.loadReal(file, aircraft);}
        catch (IllegalArgumentException | java.io.IOException expected) {
            rejected=true;
        }
        if (!rejected) throw new AssertionError("Synthetic tamper escaped: " + message);
    }

    private static String synthetic(int tick, long time, String scenario, String aircraft,
                                    double z, double power) {
        return TraceCsv.row(new TraceCsv.Frame("minecraft_runtime", scenario, aircraft, tick, time,
                0,200,z, 0,0,.7,0,0,0, 1,power,1, 0,0,0, 0,0,0));
    }

    public static void main(String[] args) throws Exception {
        Path folder=Files.createTempDirectory("ww-source-only-twin-fixtures");
        Path file=folder.resolve("synthetic-not-forge.csv");
        String id="warfare_wings:a6m",scenario="a6m-throttle-step-v1";
        String good=TraceCsv.HEADER+"\n"
                +synthetic(0,100,scenario,id,0,0)+"\n"
                +synthetic(1,101,scenario,id,.7,.01)+"\n"
                +synthetic(2,102,scenario,id,1.4,.02)+"\n"
                +synthetic(3,103,scenario,id,2.1,.03)+"\n";
        try {
            Files.writeString(file,good,StandardCharsets.UTF_8);
            var rows=RealPhysicsTwinReplayMain.loadReal(file,id);
            if(rows.size()!=4 || rows.get(3).gameTime()!=103) throw new AssertionError("Good synthetic parser fixture");
            checks++;
            expectFailure(file,"warfare_wings:b17","wrong aircraft must never be accepted");
            Files.writeString(file,good.replace("minecraft_runtime","microkernel"),StandardCharsets.UTF_8);
            expectFailure(file,id,"source substitute masquerading as actual game");
            Files.writeString(file,good.replace("a6m-throttle-step-v1","a6m-renamed-scenario"),StandardCharsets.UTF_8);
            expectFailure(file,id,"wrong scenario identity");
            Files.writeString(file,good.replace(",102,",",105,"),StandardCharsets.UTF_8);
            expectFailure(file,id,"nonconsecutive actual Minecraft game ticks");
            Files.writeString(file,good.replace(",2,102,",",5,102,"),StandardCharsets.UTF_8);
            expectFailure(file,id,"duplicate/missing entity ticks");
            Files.writeString(file,good.replace(",14.000000000000,14.000000000000,",",13.000000000000,13.000000000000,"),StandardCharsets.UTF_8);
            expectFailure(file,id,"unphysical reported speed field");
            Files.writeString(file,TraceCsv.HEADER+"\n"
                    +synthetic(0,100,scenario,id,0,0)+"\n"
                    +synthetic(1,101,scenario,id,.7,.01)+"\n"
                    +synthetic(2,102,scenario,id,.7,.01)+"\n"
                    +synthetic(3,103,scenario,id,.7,.01)+"\n"
                    +synthetic(4,104,scenario,id,.7,.01)+"\n",StandardCharsets.UTF_8);
            expectFailure(file,id,"three frozen entity states despite advancing game clock");
            Files.writeString(file,good,StandardCharsets.UTF_8);
            Path result=folder.resolve("source-only-diagnostic.csv");
            // Source test verifies machine-readable raw replay contract but
            // never labels the synthetic fixture as actual physical success.
            if(args.length != 1) throw new IllegalArgumentException("Source anchor required");
            RealPhysicsTwinReplayMain.replay(Path.of(args[0]),id,file,result);
            var series=Files.readAllLines(result,StandardCharsets.UTF_8);
            if(series.size()!=4 || !series.get(0).equals(RealPhysicsTwinReplayMain.HEADER))
                throw new AssertionError("Deterministic source diagnostic CSV schema");
            checks++;
            System.out.println("RealPhysicsTwinReplaySelfTest passed " + checks
                    + " SYNTHETIC parser/replay fixture checks; actual Minecraft NOT_RUN");
        } finally {
            Files.deleteIfExists(file);
            Files.deleteIfExists(folder.resolve("source-only-diagnostic.csv"));
            Files.deleteIfExists(folder);
        }
    }
}
