package org.kneekura.observer;

import com.google.gson.*;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.effect.MobEffects;

/** Same bounded reads on either logical side; never writes gameplay state. */
final class StaffStateCapture {
    private StaffStateCapture() {}
    static JsonObject capture(Entity entity,String side) {
        JsonObject out=new JsonObject(); out.addProperty("schema_version",1); out.addProperty("observation_side",side);
        if(!(entity instanceof Player player)) {out.addProperty("applicable",false);out.addProperty("unavailable_reason","Selected entity is not a player");return out;}
        out.addProperty("applicable",true); var stack=player.getMainHandItem(); JsonObject hand=new JsonObject();
        hand.addProperty("item",BuiltInRegistries.ITEM.getKey(stack.getItem()).toString());hand.addProperty("count",stack.getCount());hand.addProperty("damage",stack.getDamageValue());out.add("main_hand",hand);
        var effect=player.getEffect(MobEffects.GLOWING);
        if(effect==null)out.add("glowing",JsonNull.INSTANCE);
        else {JsonObject glowing=new JsonObject();glowing.addProperty("duration_ticks",effect.getDuration());glowing.addProperty("amplifier",effect.getAmplifier());out.add("glowing",glowing);}
        ResourceLocation id=new ResourceLocation("kneekura","celestial_staff");JsonObject cooldown=new JsonObject();cooldown.addProperty("item",id.toString());
        boolean registered=BuiltInRegistries.ITEM.containsKey(id);cooldown.addProperty("registered",registered);
        if(registered){var item=BuiltInRegistries.ITEM.get(id);cooldown.addProperty("active",player.getCooldowns().isOnCooldown(item));cooldown.addProperty("fraction",player.getCooldowns().getCooldownPercent(item,0.0F));}
        else {cooldown.add("active",JsonNull.INSTANCE);cooldown.add("fraction",JsonNull.INSTANCE);cooldown.addProperty("unavailable_reason","Celestial Staff item is not registered in this run");}
        out.add("staff_cooldown",cooldown);return out;
    }
}
