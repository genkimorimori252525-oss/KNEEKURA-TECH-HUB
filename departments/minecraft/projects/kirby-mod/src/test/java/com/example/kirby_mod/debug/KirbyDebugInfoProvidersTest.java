package com.example.kirby_mod.debug;

import java.util.ArrayList;
import java.util.List;

public final class KirbyDebugInfoProvidersTest {

    public static void main(String[] args) {
        addingToNullProviderListCreatesList();
        addingSameProviderTwiceDoesNotDuplicate();
        appendingFromNullProviderListDoesNothing();
    }

    private static void addingToNullProviderListCreatesList() {
        KirbyDebugInfoProvider provider = lines -> lines.add("thought=test");

        List<KirbyDebugInfoProvider> providers = KirbyDebugInfoProviders.add(null, provider);

        assertEquals(1, providers.size(), "provider count");
        assertSame(provider, providers.get(0), "stored provider");
    }

    private static void addingSameProviderTwiceDoesNotDuplicate() {
        KirbyDebugInfoProvider provider = lines -> lines.add("thought=test");
        List<KirbyDebugInfoProvider> providers = KirbyDebugInfoProviders.add(null, provider);

        providers = KirbyDebugInfoProviders.add(providers, provider);

        assertEquals(1, providers.size(), "provider count after duplicate add");
    }

    private static void appendingFromNullProviderListDoesNothing() {
        List<String> lines = new ArrayList<>();

        KirbyDebugInfoProviders.append(null, lines);

        assertEquals(0, lines.size(), "debug lines");
    }

    private static void assertEquals(int expected, int actual, String label) {
        if (expected != actual) {
            throw new AssertionError(label + ": expected <" + expected + "> but was <" + actual + ">");
        }
    }

    private static void assertSame(Object expected, Object actual, String label) {
        if (expected != actual) {
            throw new AssertionError(label + ": expected same instance");
        }
    }

    private KirbyDebugInfoProvidersTest() {}
}
