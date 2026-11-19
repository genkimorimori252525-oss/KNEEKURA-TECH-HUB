package com.github.tartaricacid.touhoulittlemaid.sim.client;

import com.github.tartaricacid.touhoulittlemaid.entity.passive.EntityMaid;
import com.github.tartaricacid.touhoulittlemaid.geckolib3.geo.IGeoEntity;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.api.distmarker.OnlyIn;

import java.util.Map;
import java.util.WeakHashMap;
import java.util.concurrent.atomic.AtomicLong;

/**
 * {@code EntityMaidRenderer.geoRender} 直後の YSM palette を Viewer へライブ転送する入口。
 *
 * <p>録画用 {@link SimPaletteTrace} とは独立しており、Path/Files/record codec を使わない。
 * Viewer の受信 socket が無ければ transport は loopback 接続を再試行し、UUID ごとの最新
 * frame だけをメモリに保持する。{@code -Dtlm.sim.palette.live=0} で完全に停止できる。
 */
@OnlyIn(Dist.CLIENT)
public final class SimPaletteLive {
    public static final String PROP_ENABLE = "tlm.sim.palette.live";
    public static final String PROP_PORT = "tlm.sim.palette.live.port";

    private static final AtomicLong SEQUENCE = new AtomicLong();
    private static final SimPaletteLiveTransport TRANSPORT = new SimPaletteLiveTransport(port());

    /** geo root はモデル差し替えで使い回され得るので、1秒ごとに object graph を引き直す。 */
    private static final Map<Object, Map<String, CachedPalette>> FOUND_CACHE = new WeakHashMap<>();

    private record CachedPalette(SimBonePalette.Found found, String[] names, long refreshedAt) {}

    private SimPaletteLive() {}

    public static boolean enabled() {
        return !"0".equals(System.getProperty(PROP_ENABLE));
    }

    private static int port() {
        int value = Integer.getInteger(PROP_PORT, SimPaletteLiveTransport.DEFAULT_PORT);
        return value >= 1 && value <= 65535 ? value : SimPaletteLiveTransport.DEFAULT_PORT;
    }

    /** post-geoRender の本体描画からだけ呼ぶ。反射メソッドは呼ばず SimBonePalette の field 探索を使う。 */
    public static void afterRender(EntityMaid maid, IGeoEntity geoEntity, float partialTick) {
        if (!enabled() || maid == null || geoEntity == null || !maid.isYsmModel()) {
            return;
        }
        Object root = geoEntity.getGeoModel();
        if (root == null) {
            return;
        }

        String modelId = maid.getYsmModelId();
        String modelTexture = maid.getYsmModelTexture();
        String modelKey = modelId + '\u0000' + modelTexture;
        long gameTime = maid.level().getGameTime();
        CachedPalette cached = find(root, modelKey, gameTime);
        if (cached == null) {
            return;
        }
        SimBonePalette.Found found = cached.found();
        int bones = found.bones().size();
        if (bones < 1 || bones > SimPaletteLiveProtocol.MAX_BONES
                || found.palette().length != bones * SimPaletteLiveProtocol.PALETTE_STRIDE) {
            return;
        }

        String geometryType = found.ownerClass() + "#" + found.path();
        SimPaletteLiveProtocol.Frame frame = new SimPaletteLiveProtocol.Frame(
                SEQUENCE.incrementAndGet(), gameTime, partialTick, maid.getId(), maid.getUUID(),
                String.valueOf(BuiltInRegistries.ENTITY_TYPE.getKey(maid.getType())),
                modelId, modelTexture, geometryType, cached.names(), found.palette());
        TRANSPORT.offer(frame);
    }

    private static CachedPalette find(Object root, String modelKey, long gameTime) {
        synchronized (FOUND_CACHE) {
            Map<String, CachedPalette> byModel = FOUND_CACHE.computeIfAbsent(root,
                    ignored -> new java.util.HashMap<>());
            CachedPalette cached = byModel.get(modelKey);
            if (cached != null && gameTime >= cached.refreshedAt()
                    && gameTime - cached.refreshedAt() < 20L) {
                return cached;
            }
            SimBonePalette.Found found = SimBonePalette.find(root);
            if (found == null) {
                byModel.remove(modelKey);
                return null;
            }
            String[] names = null;
            if (cached != null && cached.found().palette() == found.palette()
                    && cached.found().bones().size() == found.bones().size()) {
                names = cached.names();
            } else {
                SimBonePalette.SlotResult slots = SimBonePalette.slotNames(found);
                if (!slots.ok()) {
                    byModel.remove(modelKey);
                    return null;
                }
                names = slots.names().clone();
            }
            CachedPalette refreshed = new CachedPalette(found, names, gameTime);
            byModel.put(modelKey, refreshed);
            return refreshed;
        }
    }
}
