package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.*;
import java.io.IOException;
import java.nio.file.*;
import java.util.*;

public final class KneekuraDebugTankPreflightSelfTest {
    static void check(boolean value,String reason) { if(!value)throw new AssertionError(reason); }
    public static void main(String[] args)throws Exception {
        long[] now={0L};String hash="a".repeat(64);
        var identity=new KneekuraDebugArenaController.Identity("s","r","snap",1,"n".repeat(32),"experiment");
        var arena=new KneekuraDebugArenaController.Arena("tank",0,0,hash,new KneekuraDebugArenaController.Bounds(0,64,0,16,72,16));
        var lease=new KneekuraDebugArenaController.Lease("lease",identity,0L,120_000_000_000L,1,Set.of("wait_ticks"));
        var backend=new KneekuraDebugArenaController.Backend() {
            public void requireOwnerThread(){} public void guard(){} public void preflight(JsonObject action){}
            public JsonObject apply(JsonObject action){throw new AssertionError("preflight never applies");}
            public String stateHash(){return hash;}public void restoreBaseline(){throw new AssertionError("no reset");}
            public String observe(long epoch,long tick,String kind,JsonObject payload){throw new AssertionError("no observation fabrication");}
        };
        var controller=new KneekuraDebugArenaController(identity,arena,lease,Map.of(),backend,
                new KneekuraDebugActionJournal(Files.createTempDirectory("tank-preflight-test")),()->now[0]);
        var original=controller.snapshot();
        JsonObject marker=new JsonObject();marker.addProperty("minRemainingMs",45000);
        long required=KneekuraDebugOwnerDispatch.requiredRemainingMs(marker);
        now[0]=75_000_000_000L;controller.requireLeaseRemaining(original,required);
        now[0]++;try{controller.requireLeaseRemaining(original,required);throw new AssertionError("one ns delayed dispatch must reject");}
        catch(IOException expected){check(expected.getMessage().contains("INSUFFICIENT"),"exact budget guard");}
        check(controller.snapshot().equals(original)&&lease.deadlineNanos()==120_000_000_000L,"no extension or state change");
        for(long invalid:new long[]{-1,120001}) {
            marker.addProperty("minRemainingMs",invalid);
            try{KneekuraDebugOwnerDispatch.requiredRemainingMs(marker);throw new AssertionError("invalid budget accepted");}catch(IOException expected){}
        }
        check(KneekuraDebugOwnerDispatch.requiredRemainingMs(new JsonObject())==0,"old dispatch format preserved");
        var view=KneekuraDebugTankPresentationRecipe.fromRegisteredResource(Files.readAllBytes(Path.of(args[0])));
        check(view!=null&&!view.bright()&&view.geometry().width()==16,"Node ZIP parsed and hash-verified by actual native consumer");
        System.out.println("Tank preflight: original-lease boundary/delay, old dispatch and Node ZIP interop passed");
    }
}
