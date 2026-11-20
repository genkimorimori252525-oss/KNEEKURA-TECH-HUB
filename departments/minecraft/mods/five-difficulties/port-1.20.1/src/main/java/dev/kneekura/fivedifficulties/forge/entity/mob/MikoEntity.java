package dev.kneekura.fivedifficulties.forge.entity.mob;

import dev.kneekura.fivedifficulties.forge.X1Config;
import net.minecraft.network.chat.Component;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;

/**
 * Port of X1 {@code EntityMiko} (豊聡耳神子): Reimu's code with a new name (saint, flying height 0) that starts
 * in {@code NOT_ATTACK}, so she is invulnerable and never fights (her card would be Reimu's 0). Right-click on
 * an odd tick cycles the danmaku level EASY → NORMAL → HARD → LUNATIC → EASY in memory (as X1 assigns
 * THKaguyaConfig, not the file) and tells the player the new level; even ticks do nothing.
 */
public class MikoEntity extends ReimuEntity {
    private static final int EASY = 1, NORMAL = 2, HARD = 3, LUNATIC = 4;

    public MikoEntity(EntityType<? extends MikoEntity> type, Level level) {
        super(type, level);
        this.setDanmakuMobName("Toyosatomimi no Miko");
        this.setSpecies(SPECIES_HUMAN_SAINT);
        this.setDanmakuPattern(NOT_ATTACK);
        this.setFlyingHeight(0);
    }

    @Override
    protected InteractionResult mobInteract(Player player, InteractionHand hand) {
        if (this.tickCount % 2 == 0) return InteractionResult.PASS;
        if (this.level().isClientSide) return InteractionResult.SUCCESS;
        cycleDanmakuLevel(player);
        return InteractionResult.SUCCESS;
    }

    /** X1 interact body; public for the scenario. */
    public static String cycleDanmakuLevel(Player player) {
        int level = X1Config.danmakuLevel();
        String str;
        if (level == EASY) { level = NORMAL; str = "NORMAL"; }
        else if (level == NORMAL) { level = HARD; str = "HARD"; }
        else if (level == HARD) { level = LUNATIC; str = "LUNATIC"; }
        else { level = EASY; str = "EASY"; }
        X1Config.setDanmakuLevelInMemory(level);
        if (player != null) player.sendSystemMessage(Component.literal(str));
        return str;
    }
}
