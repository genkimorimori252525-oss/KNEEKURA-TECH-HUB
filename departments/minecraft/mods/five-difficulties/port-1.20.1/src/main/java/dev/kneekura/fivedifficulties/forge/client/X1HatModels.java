package dev.kneekura.fivedifficulties.forge.client;

import dev.kneekura.fivedifficulties.forge.FiveDifficultiesPort;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeDeformation;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.LivingEntity;

/**
 * Ports of X1 {@code ModelMarisaHat} and {@code ModelSuwakoHat}: a ModelBiped whose head (the plain 8³ head
 * cube, UV 0,0, as X1's inherited {@code bipedHead}) carries the hat boxes, inflated 0.4, mirrored, on a 64×32
 * texture. Only the head is drawn (X1 renders {@code bipedHead} alone, no headwear).
 */
public final class X1HatModels {
    private X1HatModels() {}

    public static final ModelLayerLocation MARISA_HAT =
            new ModelLayerLocation(new ResourceLocation(FiveDifficultiesPort.MOD_ID, "marisa_hat"), "main");
    public static final ModelLayerLocation SUWAKO_HAT =
            new ModelLayerLocation(new ResourceLocation(FiveDifficultiesPort.MOD_ID, "suwako_hat"), "main");

    private static final CubeDeformation S = new CubeDeformation(0.4F);

    private static PartDefinition base(MeshDefinition mesh) {
        PartDefinition root = mesh.getRoot();
        PartDefinition head = root.addOrReplaceChild("head",
                CubeListBuilder.create().texOffs(0, 0).addBox(-4F, -8F, -4F, 8, 8, 8), PartPose.ZERO);
        root.addOrReplaceChild("hat", CubeListBuilder.create(), PartPose.ZERO);
        return head;
    }

    private static CubeListBuilder box(int u, int v, float x, float y, float z, int w, int h, int d) {
        return CubeListBuilder.create().texOffs(u, v).mirror().addBox(x, y, z, w, h, d, S);
    }

    public static LayerDefinition createMarisaHat() {
        MeshDefinition mesh = HumanoidModel.createMesh(CubeDeformation.NONE, 0.0F);
        PartDefinition hatBase = base(mesh).addOrReplaceChild("hat_base", box(0, 0, -4F, -8F, -4F, 8, 4, 8), PartPose.ZERO);
        hatBase.addOrReplaceChild("hat_base2", box(32, 2, -3F, -3F, -3F, 6, 3, 6),
                PartPose.offsetAndRotation(0F, -7F, 0F, -0.2792527F, 0F, 0F));
        hatBase.addOrReplaceChild("hat_base3", box(48, 16, -2F, -3F, -2F, 4, 3, 4),
                PartPose.offsetAndRotation(0F, -9F, 0F, -0.5410521F, 0F, 0F));
        hatBase.addOrReplaceChild("hat_base4", box(48, 24, -1F, -3F, -1F, 2, 3, 2),
                PartPose.offsetAndRotation(0F, -11F, 1F, -0.8203047F, 0F, 0F));
        hatBase.addOrReplaceChild("brim", box(0, 16, -6F, 0F, -6F, 12, 1, 12), PartPose.offset(0F, -6F, 0F));
        hatBase.addOrReplaceChild("ribbon_right", box(44, 12, 0F, -2F, -1F, 4, 3, 1),
                PartPose.offsetAndRotation(0.5F, -6F, -4F, 0F, 0F, -0.3490659F));
        hatBase.addOrReplaceChild("ribbon_left", box(32, 12, -4F, -2F, -1F, 4, 3, 1),
                PartPose.offsetAndRotation(-0.5F, -6F, -4F, 0F, 0F, 0.3490659F));
        return LayerDefinition.create(mesh, 64, 32);
    }

    public static LayerDefinition createSuwakoHat() {
        MeshDefinition mesh = HumanoidModel.createMesh(CubeDeformation.NONE, 0.0F);
        PartDefinition hatBase = base(mesh).addOrReplaceChild("hat_base", box(0, 0, -4F, -9F, -4F, 8, 4, 8), PartPose.ZERO);
        hatBase.addOrReplaceChild("eye_right", box(0, 0, -1F, -2F, -1F, 2, 2, 2), PartPose.offset(-4F, -9F, -4F));
        hatBase.addOrReplaceChild("eye_left", box(24, 0, -1F, -2F, -1F, 2, 2, 2), PartPose.offset(4F, -9F, -4F));
        hatBase.addOrReplaceChild("brim", box(0, 16, -6F, -1F, -6F, 12, 1, 12), PartPose.offset(0F, -5F, 0F));
        return LayerDefinition.create(mesh, 64, 32);
    }

    private static HumanoidModel<LivingEntity> marisa, suwako;

    public static HumanoidModel<LivingEntity> marisa() {
        if (marisa == null) marisa = new HumanoidModel<>(Minecraft.getInstance().getEntityModels().bakeLayer(MARISA_HAT));
        return marisa;
    }

    public static HumanoidModel<LivingEntity> suwako() {
        if (suwako == null) suwako = new HumanoidModel<>(Minecraft.getInstance().getEntityModels().bakeLayer(SUWAKO_HAT));
        return suwako;
    }
}
