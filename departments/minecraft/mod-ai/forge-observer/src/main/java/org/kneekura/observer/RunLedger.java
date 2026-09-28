package org.kneekura.observer;

import java.util.*;

/** Run-local GameTest events. A duplicate result is ambiguous, not a retry win. */
public final class RunLedger {
    private final Map<String,Boolean> detected=new TreeMap<>();
    private final Map<String,Map<String,Object>> outcomes=new TreeMap<>();
    private final List<String> errors=new ArrayList<>();
    private boolean finished=false;
    public synchronized void detect(String id, boolean required) {
        if (detected.size()>=20000) throw new IllegalStateException("Too many tests");
        if (detected.putIfAbsent(id,required)!=null) errors.add("Duplicate test declaration: "+id);
    }
    public synchronized void record(String id, boolean required, boolean passed, String error) {
        if (!detected.containsKey(id) || detected.get(id)!=required) errors.add("Undetected test or required-flag drift: "+id);
        if (outcomes.containsKey(id)) { errors.add("Ambiguous retry: "+id); return; }
        Map<String,Object> row=new LinkedHashMap<>(); row.put("id",id); row.put("required",required);
        row.put("status",passed?"PASS":"FAIL");
        row.put("error",error==null?"":error.substring(0,Math.min(error.length(),2000))); outcomes.put(id,row);
    }
    public synchronized void complete() { finished=true; }
    public synchronized Map<String,Object> snapshot(Map<String,Object> identity) {
        Map<String,Object> out=new LinkedHashMap<>(); out.put("identity",identity); out.put("kind","gametest");
        out.put("completed",finished && errors.isEmpty()); out.put("exit_code",0);
        out.put("detected_test_ids",new ArrayList<>(detected.keySet())); out.put("detected_count",detected.size());
        out.put("executed_test_ids",new ArrayList<>(outcomes.keySet())); out.put("executed_count",outcomes.size());
        out.put("tests",new ArrayList<>(outcomes.values())); out.put("producer_errors",new ArrayList<>(errors));
        out.put("completion_semantics","Reporter finish, not OS process exit; runner supplies actual exit code");
        return out;
    }
}
