package kneekura.manual;

import java.util.function.Consumer;

/** A diagnostic-write failure cannot suppress an already validated shutdown. */
public final class ManualShutdown {
    private ManualShutdown() { }
    @FunctionalInterface public interface Receipt { void write() throws Exception; }
    public static void request(Receipt receipt, Runnable shutdown, Consumer<Exception> onError) {
        try { receipt.write(); }
        catch (Exception failure) { onError.accept(failure); }
        finally { shutdown.run(); }
    }
}
