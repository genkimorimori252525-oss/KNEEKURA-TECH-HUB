package com.example.kirby_mod.debug;

import java.util.ArrayList;
import java.util.List;

public final class KirbyDebugInfoProviders {

    public static List<KirbyDebugInfoProvider> add(
            List<KirbyDebugInfoProvider> providers,
            KirbyDebugInfoProvider provider) {
        List<KirbyDebugInfoProvider> out = providers == null ? new ArrayList<>() : providers;
        if (!out.contains(provider)) {
            out.add(provider);
        }
        return out;
    }

    public static void append(List<KirbyDebugInfoProvider> providers, List<String> lines) {
        if (providers == null) return;
        for (KirbyDebugInfoProvider provider : providers) {
            provider.appendDebugInfo(lines);
        }
    }

    private KirbyDebugInfoProviders() {}
}
