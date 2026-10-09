package com.example.kirby_mod.client;

import com.example.kirby_mod.entity.KirbyEntity;
import net.minecraft.client.resources.sounds.AbstractTickableSoundInstance;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;

public class KirbyInhaleSoundInstance extends AbstractTickableSoundInstance {

    private final KirbyEntity kirby;

    public KirbyInhaleSoundInstance(KirbyEntity kirby, SoundEvent event) {
        super(event, SoundSource.NEUTRAL, RandomSource.create());
        this.kirby = kirby;
        this.looping = true;
        this.attenuation = Attenuation.LINEAR;
        this.relative = false;
        this.volume = 1.0F;
        this.pitch = 1.0F;
        this.x = kirby.getX();
        this.y = kirby.getY() + kirby.getBbHeight() * 0.5D;
        this.z = kirby.getZ();
    }

    @Override
    public void tick() {
        if (!kirby.isAlive() || !kirby.getCombatState().isInhaling()) {
            this.stop();
            return;
        }
        this.x = kirby.getX();
        this.y = kirby.getY() + kirby.getBbHeight() * 0.5D;
        this.z = kirby.getZ();
    }
}
