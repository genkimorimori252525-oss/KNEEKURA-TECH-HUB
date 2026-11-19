package dev.kneekura.fivedifficulties.forge.spellcard;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Supplier;

/**
 * Port of X1 {@code SpellCardRegistry}: spell card ID ↔ registered name ↔ card factory.
 * X1 instantiates the card class per use; here a {@link Supplier} does the same.
 */
public final class X1SpellCardRegistry {
    public record Entry(int id, String domain, String name, Supplier<X1SpellCard> factory) {
        public X1SpellCard create() {
            return factory.get();
        }

        /** Item / texture key: the X1 registered name, lower-cased with punctuation removed. */
        public String key() {
            return name.toLowerCase().replace("'", "").replace("-", "_");
        }
    }

    private static final Map<Integer, Entry> BY_ID = new LinkedHashMap<>();

    private X1SpellCardRegistry() {}

    /** registerSpellCard: false if the ID is already taken. */
    public static boolean register(Supplier<X1SpellCard> factory, String domain, String name, int id) {
        if (BY_ID.containsKey(id)) return false;
        BY_ID.put(id, new Entry(id, domain, name, factory));
        return true;
    }

    public static Entry get(int id) {
        return BY_ID.get(id);
    }

    public static List<Entry> all() {
        return List.copyOf(BY_ID.values());
    }

    /** sortSpellCard: ordered by the card's original user (ties by ID; X1 used HashMap order). */
    public static List<Entry> sorted() {
        List<Entry> list = new ArrayList<>(BY_ID.values());
        list.sort(Comparator.comparingInt((Entry e) -> e.create().getOriginalUserName()).thenComparingInt(Entry::id));
        return list;
    }

    public static int size() {
        return BY_ID.size();
    }
}
