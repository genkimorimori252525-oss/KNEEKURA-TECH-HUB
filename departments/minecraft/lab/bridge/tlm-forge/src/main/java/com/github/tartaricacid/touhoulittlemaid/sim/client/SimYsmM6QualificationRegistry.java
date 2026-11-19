package com.github.tartaricacid.touhoulittlemaid.sim.client;

import java.util.LinkedHashSet;
import java.util.Set;

/**
 * In-process registry of candidates that already passed controlled E2 qualification.
 *
 * <p>The registry is keyed by runtime scope + entity + variable + stable runtime identity. It is only an
 * authorization gate for later actual-chain M6 evidence; it does not itself emit evidence.
 */
public final class SimYsmM6QualificationRegistry {
    private static final int MAX_ENTRIES = 256;
    private static final Set<Key> QUALIFIED = new LinkedHashSet<>();

    private SimYsmM6QualificationRegistry() {}

    private record Key(
            String scopeKey,
            String entityUuid,
            String variable,
            String stableIdentity
    ) {}

    public static synchronized boolean qualify(
            String scopeKey, String entityUuid, String variable, String stableIdentity) {
        Key key = key(scopeKey, entityUuid, variable, stableIdentity);
        if (key == null) {
            return false;
        }
        while (QUALIFIED.size() >= MAX_ENTRIES) {
            var it = QUALIFIED.iterator();
            if (!it.hasNext()) {
                break;
            }
            it.next();
            it.remove();
        }
        QUALIFIED.add(key);
        return true;
    }

    public static synchronized boolean isQualified(
            String scopeKey, String entityUuid, String variable, String stableIdentity) {
        Key key = key(scopeKey, entityUuid, variable, stableIdentity);
        return key != null && QUALIFIED.contains(key);
    }

    public static synchronized int size() {
        return QUALIFIED.size();
    }

    public static synchronized void clear() {
        QUALIFIED.clear();
    }

    private static Key key(
            String scopeKey, String entityUuid, String variable, String stableIdentity) {
        if (blank(scopeKey) || blank(entityUuid) || blank(variable) || blank(stableIdentity)) {
            return null;
        }
        String bare = SimYsmToggleAnalyzer.normalizeVariable(variable);
        if (bare == null) {
            return null;
        }
        return new Key(scopeKey.trim(), entityUuid.trim(), bare, stableIdentity);
    }

    private static boolean blank(String value) {
        return value == null || value.isBlank();
    }
}
