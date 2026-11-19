package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import com.google.gson.JsonParser;

public final class KneekuraDebugTerrainQueryRequestSelfTest {
    public static void main(String[] args) {
        String valid="{\"radius\":0,\"maxCells\":49,\"maxMillis\":10}";
        if(KneekuraDebugTerrainQueryRequest.parse(null)!=null)throw new AssertionError("default off");
        var request=KneekuraDebugTerrainQueryRequest.parse(JsonParser.parseString(valid));
        if(request.radius()!=0||request.maxCells()!=49||request.maxMillis()!=10)throw new AssertionError("bounded request");
        for(String invalid:new String[]{valid.replace("0,","4,"),valid.replace("0,","-1,"),
                valid.replace("49","50"),valid.replace("49","0"),valid.replace("10","51"),valid.replace("10","0"),
                valid.replace("10","10.1"),valid.replace("10","\"10\""),valid.replace("10","1e100"),
                valid.replace("{","{\"worldLoad\":true,"),"{}","[]","true"}) {
            try{KneekuraDebugTerrainQueryRequest.parse(JsonParser.parseString(invalid));throw new AssertionError("accepted "+invalid);}
            catch(IllegalArgumentException expected){ }
        }
        System.out.println("Terrain query request: default OFF, exact numeric limits and no extra action fields");
    }
}
