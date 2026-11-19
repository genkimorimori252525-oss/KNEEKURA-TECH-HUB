package com.github.tartaricacid.touhoulittlemaid.sim;

import com.github.tartaricacid.touhoulittlemaid.TouhouLittleMaid;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.event.PlayLevelSoundEvent;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.living.LivingDamageEvent;
import net.minecraftforge.event.server.ServerStartedEvent;
import net.minecraftforge.event.server.ServerStoppingEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/**
 * SimLab を Forge のライフサイクルへ繋ぐだけの層。
 *
 * <p>{@code tlm.sim.scenario} が指定されていない JVM では {@link SimLab#begin} が即 return し、
 * 以降のフックも {@code ENABLED=false} で全部素通りする。
 * つまり<b>通常の {@code runServer} / 実機ビルドには実質的な影響がない</b>。
 */
@Mod.EventBusSubscriber(modid = TouhouLittleMaid.MOD_ID)
public final class SimEvents {

    private SimEvents() {}

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        SimLab.begin(event.getServer());
    }

    @SubscribeEvent
    public static void onServerTick(TickEvent.ServerTickEvent event) {
        if (event.phase == TickEvent.Phase.END) {
            SimLab.tick();
        }
    }

    @SubscribeEvent
    public static void onServerStopping(ServerStoppingEvent event) {
        SimLab.shutdown("server-stopping");
    }

    /**
     * 実ダメージ (防具/吸収適用後) を {@code ch:dmg} へ。
     * {@code LivingHurtEvent} ではなく {@code LivingDamageEvent} を採るのは、
     * バランス測定で欲しいのが「実際に減った HP」だから。
     */
    @SubscribeEvent
    public static void onLivingDamage(LivingDamageEvent event) {
        SimLab.onDamage(event.getEntity(), event.getSource(), event.getAmount());
    }

    /**
     * エンティティ位置で鳴った音 ({@code owner.playSound(...)} 系) を {@code ch:sound} へ。
     * volume/pitch は他 mod の listener による変更後の値 ({@code getNew*}) を採る ——
     * 記録したいのは「呼ばれた値」ではなく「実際に鳴った値」だから。
     */
    @SubscribeEvent
    public static void onLevelSoundAtEntity(PlayLevelSoundEvent.AtEntity event) {
        if (!SimLab.ENABLED || event.getEntity() == null || event.getLevel().isClientSide()) {
            return;
        }
        SimLab.onSound(event.getSound(), event.getSource(),
                event.getEntity().getX(), event.getEntity().getY(), event.getEntity().getZ(),
                event.getNewVolume(), event.getNewPitch());
    }

    /** 座標指定で鳴った音 ({@code level.playSound(...)} 系) を {@code ch:sound} へ。 */
    @SubscribeEvent
    public static void onLevelSoundAtPosition(PlayLevelSoundEvent.AtPosition event) {
        if (!SimLab.ENABLED || event.getLevel().isClientSide()) {
            return;
        }
        Vec3 p = event.getPosition();
        SimLab.onSound(event.getSound(), event.getSource(), p.x, p.y, p.z,
                event.getNewVolume(), event.getNewPitch());
    }
}
