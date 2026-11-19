package com.example.kirby_mod.entity;

import com.example.kirby_mod.KirbyMod;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvent;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

public final class ModSounds {

    public static final DeferredRegister<SoundEvent> SOUND_EVENTS =
            DeferredRegister.create(ForgeRegistries.SOUND_EVENTS, KirbyMod.MODID);

    // --- 配線済み ---
    public static final RegistryObject<SoundEvent> KIRBY_BACUME_1   = reg("kirby_bacume_1");
    public static final RegistryObject<SoundEvent> KIRBY_BACUME_2   = reg("kirby_bacume_2");
    public static final RegistryObject<SoundEvent> KIRBY_SUICOMIED  = reg("kirby_suicomied");
    public static final RegistryObject<SoundEvent> KIRBY_REVERSE_1  = reg("kirby_reverse_1");
    public static final RegistryObject<SoundEvent> KIRBY_REVERSE_2A = reg("kirby_reverse_2a");
    public static final RegistryObject<SoundEvent> KIRBY_REVERSE_2B = reg("kirby_reverse_2b");
    public static final RegistryObject<SoundEvent> KIRBY_REVERSE_3  = reg("kirby_reverse_3");
    public static final RegistryObject<SoundEvent> KIRBY_NOMIKOMI_1 = reg("kirby_nomikomi_1");
    public static final RegistryObject<SoundEvent> KIRBY_NOMIKOMI_2 = reg("kirby_nomikomi_2");
    public static final RegistryObject<SoundEvent> KIRBY_FLY_LOOP   = reg("kirby_fly_loop");
    public static final RegistryObject<SoundEvent> KIRBY_FLY_FINISH = reg("kirby_fly_finish");
    public static final RegistryObject<SoundEvent> KIRBY_JAMP       = reg("kirby_jamp");
    public static final RegistryObject<SoundEvent> KIRBY_LAND       = reg("kirby_land");
    public static final RegistryObject<SoundEvent> KIRBY_WALK_1     = reg("kirby_walk_1");
    public static final RegistryObject<SoundEvent> KIRBY_WALK_2     = reg("kirby_walk_2");
    public static final RegistryObject<SoundEvent> KIRBY_WALK_3     = reg("kirby_walk_3");

    // --- 登録のみ(将来用) ---
    public static final RegistryObject<SoundEvent> ATTACK_1 = reg("attack_1");
    public static final RegistryObject<SoundEvent> ATTACK_3 = reg("attack_3");
    public static final RegistryObject<SoundEvent> ATTACK_4 = reg("attack_4");
    public static final RegistryObject<SoundEvent> ATTACK_5 = reg("attack_5");
    public static final RegistryObject<SoundEvent> CARRY    = reg("carry");
    public static final RegistryObject<SoundEvent> DEATH    = reg("death");
    public static final RegistryObject<SoundEvent> HAI      = reg("hai");
    public static final RegistryObject<SoundEvent> HIT_DAMAGE_1 = reg("hit_damage_1");
    public static final RegistryObject<SoundEvent> HIT_DAMAGE_2 = reg("hit_damage_2");
    public static final RegistryObject<SoundEvent> HIT_DAMAGE_3 = reg("hit_damage_3");
    public static final RegistryObject<SoundEvent> HIT_DAMAGE_4 = reg("hit_damage_4");
    public static final RegistryObject<SoundEvent> OTTO     = reg("otto");
    public static final RegistryObject<SoundEvent> SAD      = reg("sad");
    public static final RegistryObject<SoundEvent> SLEEP    = reg("sleep");
    public static final RegistryObject<SoundEvent> UO       = reg("uo");
    public static final RegistryObject<SoundEvent> KIRBY_COPY_REVERSE = reg("kirby_copy_reverse");
    public static final RegistryObject<SoundEvent> KIRBY_COPY_SOUND   = reg("kirby_copy_sound");
    public static final RegistryObject<SoundEvent> KIRBY_HIT_COPY_REVERSE = reg("kirby_hit_copy_reverse");
    public static final RegistryObject<SoundEvent> COPY_ABILITY_GET = reg("copy_ability_get");
    public static final RegistryObject<SoundEvent> PUNCH    = reg("punch");

    private static RegistryObject<SoundEvent> reg(String name) {
        return SOUND_EVENTS.register(name,
                () -> SoundEvent.createVariableRangeEvent(new ResourceLocation(KirbyMod.MODID, name)));
    }

    private ModSounds() {}
}
