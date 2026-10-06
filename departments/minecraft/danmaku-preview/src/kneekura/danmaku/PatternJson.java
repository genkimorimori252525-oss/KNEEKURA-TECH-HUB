package kneekura.danmaku;

import java.util.HashMap;
import java.util.Locale;
import java.util.Set;
import java.util.regex.Pattern;

/** A deliberately limited, flat JSON v1 schema; no general-purpose JSON parser. */
public final class PatternJson {
    private static final Set<String> KEYS = Set.of("schemaVersion", "tickRate", "pattern", "bullets",
        "speed", "intervalTicks", "fanAngleDeg", "rotationDegPerSecond", "elevationDeg",
        "lifetimeTicks", "durationTicks");
    private static final Set<String> INTEGER_KEYS = Set.of("schemaVersion", "tickRate", "bullets",
        "intervalTicks", "lifetimeTicks", "durationTicks");
    private static final Pattern VALUE = Pattern.compile(
        "\\s*\"([A-Za-z]+)\"\\s*:\\s*(?:\"([A-Z_]+)\"|(-?(?:0|[1-9][0-9]*)(?:\\.[0-9]+)?(?:[eE][+-]?[0-9]+)?))\\s*");

    public static String write(kneekura.danmaku.Pattern.Config c) {
        return String.format(Locale.ROOT, """
            {
              "schemaVersion": 1,
              "tickRate": 20,
              "pattern": "%s",
              "bullets": %d,
              "speed": %s,
              "intervalTicks": %d,
              "fanAngleDeg": %s,
              "rotationDegPerSecond": %s,
              "elevationDeg": %s,
              "lifetimeTicks": %d,
              "durationTicks": %d
            }
            """, c.pattern(), c.bullets(), Double.toString(c.speed()), c.intervalTicks(),
            Double.toString(c.fanAngleDeg()), Double.toString(c.rotationDegPerSecond()),
            Double.toString(c.elevationDeg()), c.lifetimeTicks(), c.durationTicks());
    }

    public static kneekura.danmaku.Pattern.Config read(String json) {
        if (json == null || json.length() > 16384) throw new IllegalArgumentException("JSON size limit: 16KiB");
        String text = json.strip();
        if (!text.startsWith("{") || !text.endsWith("}")) throw new IllegalArgumentException("JSON object required");
        var numbers = new HashMap<String, Double>();
        var strings = new HashMap<String, String>();
        int position = 1, end = text.length() - 1;
        while (position < end) {
            var matcher = VALUE.matcher(text).region(position, end);
            if (!matcher.lookingAt()) throw new IllegalArgumentException("Invalid JSON field at " + position);
            String key = matcher.group(1);
            if (!KEYS.contains(key) || numbers.containsKey(key) || strings.containsKey(key))
                throw new IllegalArgumentException("Unknown or duplicate field: " + key);
            if (matcher.group(2) != null) strings.put(key, matcher.group(2));
            else {
                if (INTEGER_KEYS.contains(key)) {
                    try { new java.math.BigDecimal(matcher.group(3)).intValueExact(); }
                    catch (ArithmeticException ex) { throw new IllegalArgumentException("Integer required: " + key, ex); }
                }
                double value = Double.parseDouble(matcher.group(3));
                if (!Double.isFinite(value)) throw new IllegalArgumentException("Finite number required: " + key);
                numbers.put(key, value);
            }
            position = matcher.end();
            if (position == end) break;
            if (text.charAt(position++) != ',' || text.substring(position, end).isBlank())
                throw new IllegalArgumentException("Invalid JSON separator");
        }
        if (numbers.size() != 10 || strings.size() != 1 || !strings.containsKey("pattern"))
            throw new IllegalArgumentException("All v1 fields with the correct types are required");
        if (integer(numbers, "schemaVersion") != 1 || integer(numbers, "tickRate") != 20)
            throw new IllegalArgumentException("Only schemaVersion=1 and tickRate=20 are supported");
        return new kneekura.danmaku.Pattern.Config(kneekura.danmaku.Pattern.Kind.valueOf(strings.get("pattern")),
            integer(numbers, "bullets"), numbers.get("speed"), integer(numbers, "intervalTicks"),
            numbers.get("fanAngleDeg"), numbers.get("rotationDegPerSecond"), numbers.get("elevationDeg"),
            integer(numbers, "lifetimeTicks"), integer(numbers, "durationTicks"));
    }

    private static int integer(HashMap<String, Double> values, String name) {
        double value = values.get(name);
        if (value != Math.rint(value) || value < Integer.MIN_VALUE || value > Integer.MAX_VALUE)
            throw new IllegalArgumentException("Integer required: " + name);
        return (int) value;
    }
}