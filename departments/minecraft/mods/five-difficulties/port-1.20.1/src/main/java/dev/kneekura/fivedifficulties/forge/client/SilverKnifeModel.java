package dev.kneekura.fivedifficulties.forge.client;

import dev.kneekura.fivedifficulties.forge.FiveDifficultiesPort;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.resources.ResourceLocation;

/** Box-for-box port of X1 {@code ModelSilverKnife} (64x32 texture, three boxes rotated 90 degrees on X). */
public final class SilverKnifeModel {
    public static final ModelLayerLocation LAYER_LOCATION = new ModelLayerLocation(
            new ResourceLocation(FiveDifficultiesPort.MOD_ID, "silver_knife"), "main");

    private SilverKnifeModel() {}

    public static LayerDefinition createBodyLayer() {
        MeshDefinition mesh = new MeshDefinition();
        PartDefinition root = mesh.getRoot();
        PartPose rotated = PartPose.rotation((float) Math.PI / 2F, 0F, 0F);
        root.addOrReplaceChild("knife0", CubeListBuilder.create().texOffs(0, 0).addBox(-4, -5, -1, 7, 1, 3), rotated);
        root.addOrReplaceChild("knife1", CubeListBuilder.create().texOffs(0, 16).addBox(-2, -9, 0, 3, 14, 1), rotated);
        root.addOrReplaceChild("knife2", CubeListBuilder.create().texOffs(32, 16).addBox(-1, 5, 0, 1, 1, 1), rotated);
        return LayerDefinition.create(mesh, 64, 32);
    }

    public static ModelPart bake(net.minecraft.client.model.geom.EntityModelSet models) {
        return models.bakeLayer(LAYER_LOCATION);
    }
}
