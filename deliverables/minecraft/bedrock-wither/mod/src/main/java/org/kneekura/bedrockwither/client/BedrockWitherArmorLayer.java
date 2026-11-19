package org.kneekura.bedrockwither.client;

import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.EntityModelSet;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.layers.EnergySwirlLayer;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import org.kneekura.bedrockwither.entity.BedrockWitherEntity;

/**
 * Bedrock powered-shield geometry/visibility with a Java-runtime texture substitute.
 *
 * Current Mojang Bedrock armor geometry is the boss geometry inflated by 2 pixels.
 * Its white armor controller uses:
 *   x = cos(life_time * 22.92deg) * 3
 *   y = life_time * 0.2
 * With 20 ticks/sec this maps exactly to x=cos(ticks*0.02)*3 and y=ticks*0.01,
 * which is the EnergySwirlLayer coordinate convention used here.
 *
 * Texture bytes are NOT copied from Bedrock. Java's bundled Wither armor texture
 * is a temporary product asset substitute; visual parity remains a Tank task.
 */
public final class BedrockWitherArmorLayer
        extends EnergySwirlLayer<BedrockWitherEntity, BedrockWitherModel> {

    private static final ResourceLocation JAVA_WITHER_ARMOR_TEXTURE =
            new ResourceLocation("minecraft", "textures/entity/wither/wither_armor.png");

    private final BedrockWitherModel model;

    public BedrockWitherArmorLayer(
            RenderLayerParent<BedrockWitherEntity, BedrockWitherModel> parent,
            EntityModelSet modelSet
    ) {
        super(parent);
        this.model = new BedrockWitherModel(
                modelSet.bakeLayer(BedrockWitherModel.ARMOR_LAYER_LOCATION)
        );
    }

    @Override
    protected float xOffset(float ticks) {
        return Mth.cos(ticks * 0.02F) * 3.0F;
    }

    @Override
    protected ResourceLocation getTextureLocation() {
        return JAVA_WITHER_ARMOR_TEXTURE;
    }

    @Override
    protected EntityModel<BedrockWitherEntity> model() {
        return model;
    }
}
