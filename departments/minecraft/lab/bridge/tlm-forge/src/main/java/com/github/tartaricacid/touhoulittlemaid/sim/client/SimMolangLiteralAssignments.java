package com.github.tartaricacid.touhoulittlemaid.sim.client;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.ArrayList;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Fail-closed extractor for simple numeric Molang assignments.
 *
 * <p>Only direct assignments to one-segment variables such as {@code v.wuqi = 1} or
 * {@code variable.wuqi = 0.0} are accepted. Dotted variables, expressions on the right-hand side,
 * comparisons, function calls and other Molang syntax are intentionally ignored.
 */
public final class SimMolangLiteralAssignments {
    private static final int MAX_ASSIGNMENTS = 32;
    private static final Pattern ASSIGNMENT = Pattern.compile(
            "(?i)(?<![A-Za-z0-9_.])(?:v|variable)\\.([A-Za-z_][A-Za-z0-9_]*)(?!\\.)"
                    + "\\s*=\\s*(?!=)"
                    + "([-+]?(?:(?:\\d+(?:\\.\\d*)?)|(?:\\.\\d+))(?:[eE][-+]?\\d+)?)"
                    + "(?=\\s*(?:[;)]|$))");

    private SimMolangLiteralAssignments() {}

    public record Assignment(String variable, double value, String literal, int offset) {}

    public static List<Assignment> parse(String expression) {
        if (expression == null || expression.isBlank()) {
            return List.of();
        }
        List<Assignment> out = new ArrayList<>();
        Matcher matcher = ASSIGNMENT.matcher(expression);
        while (matcher.find() && out.size() < MAX_ASSIGNMENTS) {
            try {
                double value = Double.parseDouble(matcher.group(2));
                if (!Double.isFinite(value)) {
                    continue;
                }
                out.add(new Assignment(matcher.group(1), value, matcher.group(2), matcher.start()));
            } catch (NumberFormatException ignored) {
                // Fail closed: malformed numeric literal is not evidence.
            }
        }
        return List.copyOf(out);
    }

    /**
     * Match one complete handler expression inside a possibly merged M5 expression.
     * Whitespace is ignored, but semicolon boundaries are required.
     */
    static boolean containsWholeExpression(String combinedExpression, String handlerExpression) {
        String combined = normalizeExpression(combinedExpression);
        String handler = normalizeExpression(handlerExpression);
        if (combined.isEmpty() || handler.isEmpty()) {
            return false;
        }
        if (combined.equals(handler)) {
            return true;
        }
        return combined.startsWith(handler + ";")
                || combined.endsWith(";" + handler)
                || combined.contains(";" + handler + ";");
    }

    private static String normalizeExpression(String expression) {
        return expression == null ? "" : expression.replaceAll("\\s+", "");
    }

    /**
     * Final assignment per variable in execution order. If one command writes v.wuqi twice,
     * only the last literal is the expected post-command state.
     */
    public static Map<String, Assignment> lastByVariable(String expression) {
        Map<String, Assignment> out = new LinkedHashMap<>();
        for (Assignment assignment : parse(expression)) {
            out.put(assignment.variable(), assignment);
        }
        return out;
    }
}
