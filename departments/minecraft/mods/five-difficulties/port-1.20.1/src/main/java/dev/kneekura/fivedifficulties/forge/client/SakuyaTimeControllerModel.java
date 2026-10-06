package dev.kneekura.fivedifficulties.forge.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import dev.kneekura.fivedifficulties.forge.FiveDifficultiesPort;
import dev.kneekura.fivedifficulties.forge.entity.SakuyaTimeControllerEntity;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.resources.ResourceLocation;

public final class SakuyaTimeControllerModel extends EntityModel<SakuyaTimeControllerEntity> {
    public static final ModelLayerLocation LAYER_LOCATION = new ModelLayerLocation(
            new ResourceLocation(FiveDifficultiesPort.MOD_ID, "sakuya_time_controller"),
            "main"
    );

    private final ModelPart root;

    public SakuyaTimeControllerModel(ModelPart root) {
        this.root = root;
    }

    public static LayerDefinition createBodyLayer() {
        MeshDefinition mesh = new MeshDefinition();
        PartDefinition root = mesh.getRoot();

        root.addOrReplaceChild(
                "watch_base",
                CubeListBuilder.create()
                        .texOffs(0, 0)
                        .addBox(-6.0F, -6.0F, -2.0F, 12.0F, 12.0F, 4.0F),
                PartPose.ZERO
        );

        root.addOrReplaceChild(
                "watch_center",
                CubeListBuilder.create()
                        .texOffs(28, 14)
                        .addBox(-8.0F, -8.0F, -1.0F, 16.0F, 16.0F, 2.0F),
                PartPose.ZERO
        );

        root.addOrReplaceChild(
                "watch_handle",
                CubeListBuilder.create()
                        .texOffs(32, 0)
                        .addBox(-4.0F, 8.0F, 0.0F, 8.0F, 6.0F, 0.0F),
                PartPose.ZERO
        );

        root.addOrReplaceChild(
                "watch_cover",
                CubeListBuilder.create()
                        .texOffs(48, 16)
                        .addBox(-8.0F, -8.0F, 0.0F, 16.0F, 16.0F, 0.0F),
                PartPose.offsetAndRotation(0.0F, -16.0F, -4.0F, (float)Math.PI / 6.0F, 0.0F, 0.0F)
        );

        return LayerDefinition.create(mesh, 64, 32);
    }

    @Override
    public void setupAnim(
            SakuyaTimeControllerEntity entity,
            float limbSwing,
            float limbSwingAmount,
            float ageInTicks,
            float netHeadYaw,
            float headPitch
    ) {
        // X1 ModelPrivateSquare has no per-part animation.
    }

    @Override
    public void renderToBuffer(
            PoseStack poseStack,
            VertexConsumer consumer,
            int packedLight,
            int packedOverlay,
            float red,
            float green,
            float blue,
            float alpha
    ) {
        root.render(poseStack, consumer, packedLight, packedOverlay, red, green, blue, alpha);
    }
}
