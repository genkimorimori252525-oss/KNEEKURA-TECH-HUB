package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.JsonParser;

public final class KneekuraDebugDecisionBurstRequestSelfTest {
    public static void main(String[] args) {
        String valid="{\"ticks\":20,\"maxEvents\":64,\"maxBytes\":32768,\"maxNodes\":8,\"channels\":[\"goal\"]}";
        var request=KneekuraDebugDecisionBurstRequest.parse(JsonParser.parseString(valid));
        if(request.ticks()!=20||!request.channels().equals(java.util.Set.of("goal")))throw new AssertionError("valid finite request");
        if(KneekuraDebugDecisionBurstRequest.parse(null)!=null)throw new AssertionError("default off");
        var mod=KneekuraDebugDecisionBurstRequest.parse(JsonParser.parseString(valid.replace("goal","mod")));
        if(!mod.channels().equals(java.util.Set.of("mod")))throw new AssertionError("explicit MOD channel");
        if(request.channels().contains("mod"))throw new AssertionError("ordinary request cannot arm MOD");
        var projectile=KneekuraDebugDecisionBurstRequest.parse(JsonParser.parseString(valid.replace("goal","projectile")));
        if(!projectile.channels().equals(java.util.Set.of("projectile")))throw new AssertionError("explicit projectile-only channel");
        var activity=KneekuraDebugDecisionBurstRequest.parse(JsonParser.parseString(valid.replace("goal","brain_activity")));
        if(!activity.channels().equals(java.util.Set.of("brain_activity"))||request.channels().contains("brain_activity"))
            throw new AssertionError("activity requires dedicated explicit channel");
        var navigation=KneekuraDebugDecisionBurstRequest.parse(JsonParser.parseString(valid.replace("goal","navigation_result")));
        if(!navigation.channels().equals(java.util.Set.of("navigation_result"))||request.channels().contains("navigation_result"))
            throw new AssertionError("Navigation result requires explicit channel");
        var all=KneekuraDebugDecisionBurstRequest.parse(JsonParser.parseString(valid.replace("[\"goal\"]","[\"goal\",\"brain\",\"path\",\"control\",\"malus\",\"sensor\",\"mod\",\"projectile\"]")));
        if(all.channels().size()!=8)throw new AssertionError("eight unique known channels remain finite");
        for(String invalid:new String[]{valid.replace("20","20.1"),valid.replace("20","201"),
                valid.replace("20","\"20\""),valid.replace("20","1e100"),valid.replace("20","0"),
                valid.replace("[\"goal\"]","[]"),valid.replace("[\"goal\"]","[\"goal\",\"goal\"]"),
                valid.replace("goal","unknown"),valid.replace("\"ticks\":20,",""),valid.replace("{","{\"authority\":true,")}) {
            try{KneekuraDebugDecisionBurstRequest.parse(JsonParser.parseString(invalid));throw new AssertionError("accepted "+invalid);}
            catch(IllegalArgumentException expected){ }
        }
        System.out.println("Decision burst request: default OFF, exact numeric bounds, known unique channels, no extra authority fields");
    }
}
