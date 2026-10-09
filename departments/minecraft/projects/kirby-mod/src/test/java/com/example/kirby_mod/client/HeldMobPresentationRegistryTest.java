package com.example.kirby_mod.client;

import java.util.List;
import java.util.UUID;

public final class HeldMobPresentationRegistryTest {

    public static void main(String[] args) {
        replacementUpdatesTheReverseIndex();
        staleRevisionCannotRevealMob();
        sharedReferenceSurvivesOneOwnerRemoval();
        clearRemovesAllPresentationState();
    }

    private static void replacementUpdatesTheReverseIndex() {
        HeldMobPresentationRegistry.clear();
        UUID first = UUID.randomUUID();
        UUID second = UUID.randomUUID();
        HeldMobPresentationRegistry.apply(1, 1, List.of(first));
        assertEquals(true, HeldMobPresentationRegistry.shouldHide(first), "first hidden");
        HeldMobPresentationRegistry.apply(1, 2, List.of(second));
        assertEquals(false, HeldMobPresentationRegistry.shouldHide(first), "first released");
        assertEquals(true, HeldMobPresentationRegistry.shouldHide(second), "second hidden");
    }

    private static void staleRevisionCannotRevealMob() {
        HeldMobPresentationRegistry.clear();
        UUID mob = UUID.randomUUID();
        HeldMobPresentationRegistry.apply(2, 5, List.of(mob));
        HeldMobPresentationRegistry.apply(2, 4, List.of());
        assertEquals(true, HeldMobPresentationRegistry.shouldHide(mob), "stale release ignored");
    }

    private static void sharedReferenceSurvivesOneOwnerRemoval() {
        HeldMobPresentationRegistry.clear();
        UUID mob = UUID.randomUUID();
        HeldMobPresentationRegistry.apply(3, 1, List.of(mob));
        HeldMobPresentationRegistry.apply(4, 1, List.of(mob));
        HeldMobPresentationRegistry.removeKirby(3);
        assertEquals(true, HeldMobPresentationRegistry.shouldHide(mob), "remaining reference");
        HeldMobPresentationRegistry.removeKirby(4);
        assertEquals(false, HeldMobPresentationRegistry.shouldHide(mob), "all references removed");
    }

    private static void clearRemovesAllPresentationState() {
        UUID mob = UUID.randomUUID();
        HeldMobPresentationRegistry.apply(5, 1, List.of(mob));
        HeldMobPresentationRegistry.clear();
        assertEquals(false, HeldMobPresentationRegistry.shouldHide(mob), "clear");
        assertEquals(0, HeldMobPresentationRegistry.hiddenMobCountForDebug(), "hidden count");
    }

    private static void assertEquals(boolean expected, boolean actual, String label) {
        if (expected != actual) {
            throw new AssertionError(label + ": expected <" + expected + "> but was <" + actual + ">");
        }
    }

    private static void assertEquals(int expected, int actual, String label) {
        if (expected != actual) {
            throw new AssertionError(label + ": expected <" + expected + "> but was <" + actual + ">");
        }
    }

    private HeldMobPresentationRegistryTest() {}
}
