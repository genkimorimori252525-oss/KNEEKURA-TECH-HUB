package com.example.kirby_mod.entity.ai.target;

import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Items;

/** Shared rules for player-held items that attract Kirby's attention. */
public final class KirbyInterestRules {

    private KirbyInterestRules() {}

    public static boolean isTempting(Player player) {
        return player.getMainHandItem().is(Items.APPLE) || player.getMainHandItem().is(Items.CAKE)
                || player.getOffhandItem().is(Items.APPLE) || player.getOffhandItem().is(Items.CAKE);
    }
}
