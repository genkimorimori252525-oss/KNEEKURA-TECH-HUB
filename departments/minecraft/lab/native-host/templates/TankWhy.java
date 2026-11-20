// Tank "why" template. Copy this file into your MOD (add your own package line) and own it: rename, extend, adapt.
// No dependency on the Tank. Outside the Tank every call is a single static boolean check (no allocation, no logging).
// Inside the Tank (KNEEKURA_TANK_AI=1) the AI lens finds a public no-arg `tankWhy()` on your entity or on a running
// Goal and shows the notes above the mob (purple "? key=value") and in ai.jsonl ("why": {...}, change-only).
//
// Use:
//   final TankWhy why = new TankWhy();                         // one per entity (or per Goal)
//   public java.util.Map<String, Object> tankWhy() { return why.snapshot(); }
//   ... at each decision point, record the deciding reason, not a narration:
//   if (cooldown > 0) { why.note("attack", "skip: cooldown " + cooldown); return false; }   // inside canUse()
//   why.note("attack", "fire: dist " + (int) dist);                                         // when it fires
//   why.note("phase", "-> ENRAGED: hp " + (int) getHealth() + " < 50%");                   // state transition
//
// Rules: notes must be side-effect free and cheap; keep values short (the lens clips at 60 chars, 8 notes per mob).
// String concatenation still runs outside the Tank, so guard costly values with `if (TankWhy.ON)`.
// Prefer one stable key per decision ("attack", "target", "phase") so a changed value means a changed decision.
public final class TankWhy {
    public static final boolean ON = "1".equals(System.getenv("KNEEKURA_TANK_AI"));
    private final java.util.LinkedHashMap<String, Object> notes = ON ? new java.util.LinkedHashMap<>() : null;

    /** Remember the latest reason for one decision; the newest value per key wins. */
    public void note(String key, Object value) {
        if (ON) synchronized (notes) { notes.put(key, value); }
    }

    /** Drop a reason that no longer applies (for example when a goal stops). */
    public void forget(String key) {
        if (ON) synchronized (notes) { notes.remove(key); }
    }

    /** Return this from {@code public Map<String, Object> tankWhy()}. Empty outside the Tank. */
    public java.util.Map<String, Object> snapshot() {
        if (!ON) return java.util.Map.of();
        synchronized (notes) { return new java.util.LinkedHashMap<>(notes); }
    }
}
