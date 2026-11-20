package dev.kneekura.fivedifficulties.forge.crafting;

import com.google.gson.JsonObject;
import dev.kneekura.fivedifficulties.forge.FiveDifficultiesPort;
import dev.kneekura.fivedifficulties.forge.X1Config;
import net.minecraft.resources.ResourceLocation;
import net.minecraftforge.common.crafting.conditions.ICondition;
import net.minecraftforge.common.crafting.conditions.IConditionSerializer;

/**
 * X1 {@code THKaguyaConfig.recipelessItemsRecipe} ("Add Recipeless Items Recipe", default false): the recipes in
 * {@code THKaguyaRecipe.setRecipelessItemsRecipe} only exist when it is on. Read when recipes (re)load.
 */
public final class RecipelessItemsCondition implements ICondition {
    public static final ResourceLocation ID = new ResourceLocation(FiveDifficultiesPort.MOD_ID, "recipeless_items_recipe");
    public static final RecipelessItemsCondition INSTANCE = new RecipelessItemsCondition();

    private RecipelessItemsCondition() {}

    @Override
    public ResourceLocation getID() { return ID; }

    @Override
    public boolean test(IContext context) { return X1Config.recipelessItemsRecipe(); }

    public static final IConditionSerializer<RecipelessItemsCondition> SERIALIZER = new IConditionSerializer<>() {
        @Override
        public void write(JsonObject json, RecipelessItemsCondition value) {}

        @Override
        public RecipelessItemsCondition read(JsonObject json) { return INSTANCE; }

        @Override
        public ResourceLocation getID() { return ID; }
    };
}
