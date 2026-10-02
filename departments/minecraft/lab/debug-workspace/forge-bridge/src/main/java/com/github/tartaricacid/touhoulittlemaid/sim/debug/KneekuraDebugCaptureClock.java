package com.github.tartaricacid.touhoulittlemaid.sim.debug;

import java.lang.reflect.Field;
import java.lang.reflect.Modifier;
import java.util.Objects;
import java.util.function.BooleanSupplier;

/** Owned paused-render interpolation, never a replacement for observed frame metadata. */
final class KneekuraDebugCaptureClock {
    interface Access { float read(); void write(float value); }
    private final Access[] accesses;
    private final BooleanSupplier paused;
    private boolean acquired;
    private boolean restored;
    private boolean restorationExact;
    private final float[] originals;

    KneekuraDebugCaptureClock(Access access, BooleanSupplier paused) {
        this(paused, access);
    }
    KneekuraDebugCaptureClock(BooleanSupplier paused, Access... accesses) {
        if (accesses.length == 0) throw new IllegalArgumentException("CAPTURE_CLOCK_EMPTY");
        this.accesses = accesses.clone();
        for (Access access : this.accesses) Objects.requireNonNull(access);
        this.originals = new float[accesses.length];
        this.paused = Objects.requireNonNull(paused);
    }
    void acquire() {
        if (acquired || restored || !paused.getAsBoolean()) throw new IllegalStateException("CAPTURE_CLOCK_NOT_PAUSED");
        for (int i = 0; i < accesses.length; i++) {
            originals[i] = accesses[i].read();
            if (!Float.isFinite(originals[i]) || originals[i] < 0 || originals[i] > 1)
                throw new IllegalStateException("CAPTURE_CLOCK_INVALID");
        }
        acquired = true; // A failed/partial write must still be restored by the owner.
        for (Access access : accesses) access.write(0);
        if (!frozen()) throw new IllegalStateException("CAPTURE_CLOCK_WRITE_NOT_ESTABLISHED");
    }
    boolean frozen() {
        if (!acquired || restored || !paused.getAsBoolean()) return false;
        for (Access access : accesses) if (Float.compare(access.read(), 0) != 0) return false;
        return true;
    }
    boolean restore() {
        if (restored) return restorationExact;
        restored = true;
        if (!acquired) return restorationExact = true;
        boolean exact = true;
        for (int i = 0; i < accesses.length; i++) {
            try {
                accesses[i].write(originals[i]);
                exact &= Float.floatToRawIntBits(accesses[i].read()) == Float.floatToRawIntBits(originals[i]);
            } catch (RuntimeException denied) { exact = false; }
        }
        return restorationExact = exact;
    }
    static Access field(Object target, Class<?> type) {
        return namedField(target, type, "pausePartialTick", "f_91013_");
    }
    static Access eventField(Object target, Class<?> type) {
        // Forge-added field: dispatchRenderStage reads Minecraft.getPartialTick(),
        // which returns this cache computed before RenderTick.START.
        return namedField(target, type, "realPartialTick");
    }
    private static Access namedField(Object target, Class<?> type, String... names) {
        if (!type.isInstance(target)) throw new IllegalArgumentException("CAPTURE_CLOCK_TARGET");
        Field selected = null;
        // Official-mapped development name and verified Forge1.20.1 SRG field.
        for (String name : names) {
            try { selected = type.getDeclaredField(name); break; }
            catch (NoSuchFieldException absent) { /* Only the exact known aliases are eligible. */ }
        }
        if (selected == null || selected.getType() != float.class ||
                Modifier.isStatic(selected.getModifiers()) || Modifier.isFinal(selected.getModifiers()) || !selected.trySetAccessible())
            throw new IllegalStateException("CAPTURE_CLOCK_ACCESS_UNAVAILABLE");
        final Field field = selected;
        return new Access() {
            public float read() {
                try { return field.getFloat(target); }
                catch (IllegalAccessException denied) { throw new IllegalStateException("CAPTURE_CLOCK_READ_FAILED", denied); }
            }
            public void write(float value) {
                try { field.setFloat(target, value); }
                catch (IllegalAccessException denied) { throw new IllegalStateException("CAPTURE_CLOCK_WRITE_FAILED", denied); }
            }
        };
    }
}
