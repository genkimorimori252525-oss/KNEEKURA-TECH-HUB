package com.example.kirby_mod.client;

import com.example.kirby_mod.KirbyMod;
import com.example.kirby_mod.entity.KirbyEntity;
import com.example.kirby_mod.entity.KirbyEntity.FlightState;
import com.example.kirby_mod.entity.KirbyEntity.HurtFace;
import com.example.kirby_mod.entity.KirbySize;
import net.minecraft.resources.ResourceLocation;
import software.bernie.geckolib.model.GeoModel;

public class KirbyModel extends GeoModel<KirbyEntity> {

    private static final ResourceLocation MODEL =
            new ResourceLocation(KirbyMod.MODID, "geo/kirby.geo.json");
    private static final ResourceLocation ANIMATION =
            new ResourceLocation(KirbyMod.MODID, "animations/kirby.animation.json");

    private static final ResourceLocation TEX_DEFAULT      = tex("Kirby_texture.png");
    private static final ResourceLocation TEX_BACUME       = tex("Kirby_texture.Bacume.png");
    private static final ResourceLocation TEX_FLY          = tex("Kirby_texture.fly.png");
    private static final ResourceLocation TEX_KEEP_SMALL_MIDDLE = tex("Kirby_small.middle.texture.png");
    private static final ResourceLocation TEX_KEEP_BIG          = tex("Kirby_texture.big.png");
    private static final ResourceLocation TEX_HURT_1       = tex("Kirby_texture.HitbyDamage.png");
    private static final ResourceLocation TEX_HURT_2       = tex("Kirby_texture.HitbyDamage2.png");
    private static final ResourceLocation TEX_HURT_3       = tex("Kirby_texture.HitbyDamage3.png");

    private static ResourceLocation tex(String name) {
        return new ResourceLocation(KirbyMod.MODID, "texture/" + name);
    }

    @Override
    public ResourceLocation getModelResource(KirbyEntity entity) {
        return MODEL;
    }

    @Override
    public ResourceLocation getTextureResource(KirbyEntity entity) {
        // 被弾は他の状態より優先
        HurtFace hurt = entity.getHurtFace();
        switch (hurt) {
            case HURT_1: return TEX_HURT_1;
            case HURT_2: return TEX_HURT_2;
            case HURT_3: return TEX_HURT_3;
            case NONE:
            default:     break;
        }

        if (entity.getCombatState().isInhaling()) {
            return TEX_BACUME;
        }
        if (entity.getCombatState().isHolding()) {
            return entity.getKirbySize() == KirbySize.BIG ? TEX_KEEP_BIG : TEX_KEEP_SMALL_MIDDLE;
        }
        if (entity.isInWater()) {
            return TEX_DEFAULT;
        }
        if (entity.getFlightState() != FlightState.GROUND) {
            return TEX_FLY;
        }
        return TEX_DEFAULT;
    }

    @Override
    public ResourceLocation getAnimationResource(KirbyEntity entity) {
        return ANIMATION;
    }
}
