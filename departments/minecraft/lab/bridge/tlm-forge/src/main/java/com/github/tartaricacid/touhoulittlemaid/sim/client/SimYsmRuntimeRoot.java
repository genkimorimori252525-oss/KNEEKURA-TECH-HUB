package com.github.tartaricacid.touhoulittlemaid.sim.client;

import com.github.tartaricacid.touhoulittlemaid.capability.GeckoMaidEntityCapabilityProvider;
import com.github.tartaricacid.touhoulittlemaid.client.renderer.entity.EntityMaidRenderer;
import com.github.tartaricacid.touhoulittlemaid.entity.passive.EntityMaid;
import com.github.tartaricacid.touhoulittlemaid.geckolib3.geo.IGeoEntity;
import com.github.tartaricacid.touhoulittlemaid.geckolib3.geo.IGeoEntityRenderer;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.world.entity.Entity;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.api.distmarker.OnlyIn;

import javax.annotation.Nullable;
import java.lang.reflect.Field;
import java.lang.reflect.Method;

/**
 * Resolves the YSM runtime object-graph root for the nearest Reimu maid.
 *
 * <p>The renderer route is authoritative because it is the route proven to hold the live YSM model.
 * The older Gecko capability route remains a fallback for non-YSM/alternate render paths.
 *
 * <p>This class does not inspect unknown YSM internals. It only reaches the already-established
 * {@link IGeoEntity#getGeoModel()} boundary; downstream probes remain field-only.
 */
@OnlyIn(Dist.CLIENT)
final class SimYsmRuntimeRoot {
    private SimYsmRuntimeRoot() {}

    record Result(
            boolean ok,
            String message,
            @Nullable EntityMaid maid,
            @Nullable IGeoEntity geoEntity,
            @Nullable Object root,
            String route,
            String routeNote
    ) {}

    static Result findNearestReimu() {
        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null || mc.player == null) {
            return fail("ワールドに入ってから実行すること", "none", "client world/player unavailable");
        }

        EntityMaid reimu = nearestReimu(mc);
        if (reimu == null) {
            return fail("近くに霊夢が居ない", "none", "no Reimu maid in renderable entities");
        }
        return findForMaid(reimu);
    }

    /**
     * Resolve the runtime root for one already-selected maid. Controlled probes use this overload
     * so the command target and every scalar snapshot are guaranteed to refer to the same entity.
     */
    static Result findForMaid(@Nullable EntityMaid reimu) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null || mc.player == null) {
            return fail("ワールドに入ってから実行すること", "none", "client world/player unavailable");
        }
        if (reimu == null || !reimu.isAlive()) {
            return fail("対象の霊夢が居なくなった", "none", "selected Reimu maid unavailable");
        }

        IGeoEntity geoEntity = null;
        String route = "none";
        String rendererNote;

        EntityRenderer<? super EntityMaid> renderer = mc.getEntityRenderDispatcher().getRenderer(reimu);
        if (renderer instanceof EntityMaidRenderer maidRenderer) {
            RendererGeoResult rendererGeo = rendererGeoEntity(maidRenderer, reimu);
            geoEntity = rendererGeo.geoEntity();
            rendererNote = rendererGeo.note();
            if (geoEntity != null) {
                route = "renderer";
            }
        } else {
            rendererNote = "霊夢のrendererがEntityMaidRendererではない ("
                    + (renderer == null ? "null" : renderer.getClass().getName()) + ")";
        }

        if (geoEntity == null) {
            geoEntity = reimu.getCapability(GeckoMaidEntityCapabilityProvider.CAP)
                    .map(e -> (IGeoEntity) e)
                    .orElse(null);
            if (geoEntity != null) {
                route = "capability";
            }
        }

        if (geoEntity == null) {
            return new Result(
                    false,
                    "IGeoEntity に到達できない — " + rendererNote + "、capability 経路も空",
                    reimu,
                    null,
                    null,
                    "none",
                    rendererNote);
        }

        Object root = geoEntity.getGeoModel();
        String routeNote = "renderer".equals(route)
                ? rendererNote
                : "capability fallback; renderer observation: " + rendererNote;
        if (root == null) {
            return new Result(
                    false,
                    "getGeoModel() が null (経路: " + route + ")",
                    reimu,
                    geoEntity,
                    null,
                    route,
                    routeNote);
        }

        return new Result(true, "ok", reimu, geoEntity, root, route, routeNote);
    }

    private record RendererGeoResult(@Nullable IGeoEntity geoEntity, String note) {}

    /**
     * Reach the same known TLM renderer boundary used by actual YSM rendering without making
     * getYsmGeoEntity a compile-time API requirement.
     *
     * <p>Some TLM integration branches expose a dedicated getYsmGeoEntity(EntityMaid) helper.
     * reimu-mod main instead keeps the known TLM IGeoEntityRenderer in the private
     * ysmMaidRenderer field and calls IGeoEntityRenderer#getGeoEntity during render.
     *
     * <p>This helper may reflect only those named TLM integration members. It never invokes
     * methods on the returned obfuscated YSM object; downstream YSM traversal remains field-only.
     */
    @SuppressWarnings({"rawtypes", "unchecked"})
    private static RendererGeoResult rendererGeoEntity(
            EntityMaidRenderer maidRenderer, EntityMaid reimu) {
        try {
            Method helper = maidRenderer.getClass().getMethod("getYsmGeoEntity", EntityMaid.class);
            Object value = helper.invoke(maidRenderer, reimu);
            if (value instanceof IGeoEntity geo) {
                return new RendererGeoResult(geo, "EntityMaidRenderer#getYsmGeoEntity");
            }
        } catch (NoSuchMethodException ignored) {
            // Current reimu-mod main uses the renderer field route below.
        } catch (Throwable t) {
            return new RendererGeoResult(
                    null,
                    "EntityMaidRenderer#getYsmGeoEntity failed: " + t.getClass().getSimpleName());
        }

        try {
            Field field = EntityMaidRenderer.class.getDeclaredField("ysmMaidRenderer");
            field.setAccessible(true);
            Object value = field.get(maidRenderer);
            if (!(value instanceof IGeoEntityRenderer geoRenderer)) {
                return new RendererGeoResult(
                        null,
                        "EntityMaidRenderer.ysmMaidRenderer is null/unexpected");
            }
            Object geo = geoRenderer.getGeoEntity(reimu);
            if (geo instanceof IGeoEntity geoEntity) {
                return new RendererGeoResult(
                        geoEntity,
                        "EntityMaidRenderer.ysmMaidRenderer -> IGeoEntityRenderer#getGeoEntity");
            }
            return new RendererGeoResult(
                    null,
                    "IGeoEntityRenderer#getGeoEntity returned null/unexpected");
        } catch (Throwable t) {
            return new RendererGeoResult(
                    null,
                    "renderer YSM field route failed: " + t.getClass().getSimpleName());
        }
    }

    /**
     * Resolve the same entity selection shape used by the Reimu YSM debug selector:
     * nearest Reimu host to the supplied coordinates within the supplied radius.
     */
    @Nullable
    static EntityMaid findReimuNear(double x, double y, double z, double radius) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null || radius <= 0.0 || !Double.isFinite(radius)) {
            return null;
        }
        EntityMaid best = null;
        double bestDistance = radius * radius;
        boolean ambiguousBest = false;
        final double tieEpsilon = 1.0e-12;
        for (Entity entity : mc.level.entitiesForRendering()) {
            if (!(entity instanceof EntityMaid maid) || !maid.isAlive()) {
                continue;
            }
            if (!(maid.isReimuMaid() || maid.isNamedReimu())) {
                continue;
            }
            double dx = maid.getX() - x;
            double dy = maid.getY() - y;
            double dz = maid.getZ() - z;
            double distance = dx * dx + dy * dy + dz * dz;
            if (distance > radius * radius) {
                continue;
            }
            if (best == null || distance < bestDistance - tieEpsilon) {
                bestDistance = distance;
                best = maid;
                ambiguousBest = false;
            } else if (Math.abs(distance - bestDistance) <= tieEpsilon
                    && best.getId() != maid.getId()) {
                ambiguousBest = true;
            }
        }
        return ambiguousBest ? null : best;
    }

    private static Result fail(String message, String route, String routeNote) {
        return new Result(false, message, null, null, null, route, routeNote);
    }

    private static EntityMaid nearestReimu(Minecraft mc) {
        EntityMaid best = null;
        double bestDistance = Double.MAX_VALUE;
        for (Entity entity : mc.level.entitiesForRendering()) {
            if (!(entity instanceof EntityMaid maid)) {
                continue;
            }
            if (!(maid.isReimuMaid() || maid.isNamedReimu())) {
                continue;
            }
            double distance = mc.player.distanceToSqr(maid);
            if (distance < bestDistance) {
                bestDistance = distance;
                best = maid;
            }
        }
        return best;
    }
}
