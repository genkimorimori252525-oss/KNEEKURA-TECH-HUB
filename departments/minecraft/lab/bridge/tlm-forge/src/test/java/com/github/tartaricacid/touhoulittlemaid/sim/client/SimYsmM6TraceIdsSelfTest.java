package com.github.tartaricacid.touhoulittlemaid.sim.client;

import java.util.List;

/** Standalone regression for fail-closed handler trace identity parsing. */
public final class SimYsmM6TraceIdsSelfTest {
    public static void main(String[] args) {
        require(SimYsmM6TraceIds.parse("1").equals(List.of(1L)), "single ID");
        require(SimYsmM6TraceIds.parse("1,2,3").equals(List.of(1L,2L,3L)), "merged IDs");
        require(SimYsmM6TraceIds.parse(" 4 , 5 ").equals(List.of(4L,5L)), "whitespace");

        require(SimYsmM6TraceIds.parse("").isEmpty(), "empty rejected");
        require(SimYsmM6TraceIds.parse("0").isEmpty(), "zero rejected");
        require(SimYsmM6TraceIds.parse("-1").isEmpty(), "negative rejected");
        require(SimYsmM6TraceIds.parse("1,1").isEmpty(), "duplicate rejected");
        require(SimYsmM6TraceIds.parse("1,,2").isEmpty(), "empty member rejected");
        require(SimYsmM6TraceIds.parse("abc").isEmpty(), "non numeric rejected");

        StringBuilder tooMany = new StringBuilder();
        for (int i = 1; i <= 33; i++) {
            if (i > 1) tooMany.append(',');
            tooMany.append(i);
        }
        require(SimYsmM6TraceIds.parse(tooMany.toString()).isEmpty(), "budget rejected");

        require(Long.valueOf(7L).equals(SimYsmM6TraceIds.positiveLong(7L)), "long accepted");
        require(Long.valueOf(8L).equals(SimYsmM6TraceIds.positiveLong(8.0d)), "integral double accepted");
        require(SimYsmM6TraceIds.positiveLong(8.5d) == null, "fraction rejected");
        require(SimYsmM6TraceIds.positiveLong(0) == null, "non-positive number rejected");

        require("1,2,3".equals(SimYsmM6TraceIds.canonical(List.of(1L,2L,3L))),
                "canonical order");
        require(SimYsmM6TraceIds.canonical(List.of(1L,1L)).isEmpty(),
                "canonical duplicates rejected");

        System.out.println("SimYsmM6TraceIdsSelfTest OK");
    }

    private static void require(boolean ok, String message) {
        if (!ok) throw new AssertionError(message);
    }
}
