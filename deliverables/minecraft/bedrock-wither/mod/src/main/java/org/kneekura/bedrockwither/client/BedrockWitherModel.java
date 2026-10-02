package org.kneekura.bedrockwither.client;

import net.minecraft.client.model.HierarchicalModel;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeDeformation;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import org.kneekura.bedrockwither.BedrockWitherMod;
import org.kneekura.bedrockwither.entity.BedrockWitherEntity;
import org.kneekura.bedrockwither.entity.BedrockWitherHeadRuntime;

public final class BedrockWitherModel extends HierarchicalModel<BedrockWitherEntity> {
    public static final ModelLayerLocation LAYER_LOCATION =
            new ModelLayerLocation(new ResourceLocation(BedrockWitherMod.MOD_ID, "bedrock_wither"), "main");
    public static final ModelLayerLocation ARMOR_LAYER_LOCATION =
            new ModelLayerLocation(new ResourceLocation(BedrockWitherMod.MOD_ID, "bedrock_wither"), "armor");

    private final ModelPart root;
    private final ModelPart ribcage;
    private final ModelPart tail;
    private final ModelPart centerHead;
    private final ModelPart rightHead;
    private final ModelPart leftHead;

    public BedrockWitherModel(ModelPart root) {
        this.root = root;
        this.ribcage = root.getChild("upper_body_part_2");
        this.tail = root.getChild("upper_body_part_3");
        this.centerHead = root.getChild("head_1");
        this.rightHead = root.getChild("head_2");
        this.leftHead = root.getChild("head_3");
    }

    /**
     * Converted directly from Mojang Bedrock geometry.witherBoss.
     * Bedrock Y-up cube origins are converted into Java model-space Y-down coordinates.
     */
    public static LayerDefinition createBodyLayer(CubeDeformation deformation) {
        MeshDefinition mesh = new MeshDefinition();
        PartDefinition root = mesh.getRoot();

        root.addOrReplaceChild(
                "upper_body_part_1",
                CubeListBuilder.create()
                        .texOffs(0, 16)
                        .addBox(-10.0F, 3.9F, -0.5F, 20.0F, 3.0F, 3.0F, deformation),
                PartPose.ZERO
        );

        root.addOrReplaceChild(
                "upper_body_part_2",
                CubeListBuilder.create()
                        .texOffs(0, 22)
                        .addBox(0.0F, 0.0F, 0.0F, 3.0F, 10.0F, 3.0F, deformation)
                        .texOffs(24, 22)
                        .addBox(-4.0F, 1.5F, 0.5F, 11.0F, 2.0F, 2.0F, deformation)
                        .texOffs(24, 22)
                        .addBox(-4.0F, 4.0F, 0.5F, 11.0F, 2.0F, 2.0F, deformation)
                        .texOffs(24, 22)
                        .addBox(-4.0F, 6.5F, 0.5F, 11.0F, 2.0F, 2.0F, deformation),
                PartPose.offset(-2.0F, 6.9F, -0.5F)
        );

        root.addOrReplaceChild(
                "upper_body_part_3",
                CubeListBuilder.create()
                        .texOffs(12, 22)
                        .addBox(0.0F, 0.0F, 0.0F, 3.0F, 6.0F, 3.0F, deformation),
                PartPose.offset(-2.0F, 16.9F, -0.5F)
        );

        root.addOrReplaceChild(
                "head_1",
                CubeListBuilder.create()
                        .texOffs(0, 0)
                        .addBox(-4.0F, -8.0F, -4.0F, 8.0F, 8.0F, 8.0F, deformation),
                PartPose.offset(0.0F, 4.0F, 0.0F)
        );

        root.addOrReplaceChild(
                "head_2",
                CubeListBuilder.create()
                        .texOffs(32, 0)
                        .addBox(-3.0F, -6.0F, -3.0F, 6.0F, 6.0F, 6.0F, deformation),
                PartPose.offset(-9.0F, 6.0F, -1.0F)
        );

        root.addOrReplaceChild(
                "head_3",
                CubeListBuilder.create()
                        .texOffs(32, 0)
                        .addBox(-3.0F, -6.0F, -3.0F, 6.0F, 6.0F, 6.0F, deformation),
                PartPose.offset(9.0F, 6.0F, -1.0F)
        );

        return LayerDefinition.create(mesh, 64, 64);
    }

    @Override
    public ModelPart root() {
        return root;
    }

    @Override
    public void setupAnim(
            BedrockWitherEntity entity,
            float limbSwing,
            float limbSwingAmount,
            float ageInTicks,
            float netHeadYaw,
            float headPitch
    ) {
        // Bedrock: body_base_rotation = cos(life_time * 114.6 degrees).
        // 114.6 deg/sec ~= 2 rad/sec; at 20 ticks/sec this is 0.1 rad/tick.
        float bodyBase = Mth.cos(ageInTicks * 0.1F);

        // Bedrock upperBodyPart2:
        // (0.065 + 0.05 * body_base_rotation) * 180 + target_x_rotation.
        ribcage.xRot = (0.065F + 0.05F * bodyBase) * Mth.PI + headPitch * ((float) Math.PI / 180.0F);

        // upperBodyPart3 is parented to upperBodyPart2 in the Bedrock geometry.
        // This Java ModelPart is flattened to the root, so preserve the parent
        // transform explicitly in both its pivot position and global X rotation.
        tail.setPos(
                -2.0F,
                6.9F + Mth.cos(ribcage.xRot) * 10.0F,
                -0.5F + Mth.sin(ribcage.xRot) * 10.0F
        );
        tail.xRot = ribcage.xRot + (0.2F + 0.1F * bodyBase) * Mth.PI;

        // Current Mojang Bedrock animation:
        // head1 X=query.head_x_rotation(0)
        // head2 X=query.head_x_rotation(1)
        // head3 X=query.head_x_rotation(2)
        // all three Y=query.target_y_rotation.
        float targetYaw = netHeadYaw * ((float) Math.PI / 180.0F);
        centerHead.xRot = entity.runtimeState().head(0).pitch() * ((float) Math.PI / 180.0F);
        rightHead.xRot = entity.runtimeState().head(1).pitch() * ((float) Math.PI / 180.0F);
        leftHead.xRot = entity.runtimeState().head(2).pitch() * ((float) Math.PI / 180.0F);

        centerHead.yRot = targetYaw;
        rightHead.yRot = targetYaw;
        leftHead.yRot = targetYaw;
    }
}
