package dev.kneekura.fivedifficulties.forge.client.mob;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import dev.kneekura.fivedifficulties.forge.entity.mob.RinnosukeEntity;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeDeformation;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.util.Mth;

/** Port of X1 {@code ModelRinnosuke}: boxes generated from the X1 constructor; animation ported by hand. */
public class RinnosukeModel extends EntityModel<RinnosukeEntity> {
    // ---- generated from ModelRinnosuke.java ----
    private final ModelPart bipedBody;
    private final ModelPart bipedRightArm;
    private final ModelPart bipedLeftArm;
    private final ModelPart bipedRightLeg;
    private final ModelPart bipedLeftLeg;
    private final ModelPart box;
    private final ModelPart bottom;
    private final ModelPart bipedHead;
    private final ModelPart longHair;
    private final ModelPart Grass;

    public RinnosukeModel(ModelPart root) {
        this.bipedBody = root.getChild("bipedbody");
        this.bipedRightArm = root.getChild("bipedrightarm");
        this.bipedLeftArm = root.getChild("bipedleftarm");
        this.bipedRightLeg = root.getChild("bipedrightleg");
        this.bipedLeftLeg = root.getChild("bipedleftleg");
        this.box = root.getChild("bipedbody").getChild("box");
        this.bottom = root.getChild("bipedbody").getChild("bottom");
        this.bipedHead = root.getChild("bipedhead");
        this.longHair = root.getChild("bipedhead").getChild("longhair");
        this.Grass = root.getChild("bipedhead").getChild("grass");
    }

    public static LayerDefinition createBodyLayer() {
        MeshDefinition mesh = new MeshDefinition();
        PartDefinition root = mesh.getRoot();
        PartDefinition d_bipedBody = root.addOrReplaceChild("bipedbody", CubeListBuilder.create().texOffs(0, 16).addBox(-4F, 0F, -2F, 8F, 10F, 4F),
                PartPose.offsetAndRotation(0F, 0F, 0F, 0F, 0F, 0F));
        PartDefinition d_box = d_bipedBody.addOrReplaceChild("box", CubeListBuilder.create().texOffs(32, 10).addBox(-3F, -2F, 0F, 6F, 4F, 2F),
                PartPose.offsetAndRotation(0F, 8F, -4F, 0F, 0F, 0F));
        PartDefinition d_bottom = d_bipedBody.addOrReplaceChild("bottom", CubeListBuilder.create().texOffs(0, 46).addBox(-4.5F, 0F, -2.5F, 9F, 13F, 5F),
                PartPose.offsetAndRotation(0F, 8F, 0F, 0F, 0F, 0F));
        PartDefinition d_bipedRightArm = root.addOrReplaceChild("bipedrightarm", CubeListBuilder.create().texOffs(0, 32).addBox(-2F, -1F, -1.5F, 3F, 10F, 3F),
                PartPose.offsetAndRotation(-5F, 1F, 0F, 0F, 0F, 0F));
        PartDefinition d_bipedLeftArm = root.addOrReplaceChild("bipedleftarm", CubeListBuilder.create().texOffs(12, 32).addBox(-1F, -1F, -1.5F, 3F, 10F, 3F),
                PartPose.offsetAndRotation(5F, 1F, 0F, 0F, 0F, 0F));
        PartDefinition d_bipedRightLeg = root.addOrReplaceChild("bipedrightleg", CubeListBuilder.create().texOffs(48, 16).addBox(-1F, 0F, -2F, 4F, 14F, 4F),
                PartPose.offsetAndRotation(-3F, 10F, 0F, 0F, 0F, 0F));
        PartDefinition d_bipedLeftLeg = root.addOrReplaceChild("bipedleftleg", CubeListBuilder.create().texOffs(32, 16).addBox(-2F, 0F, -2F, 4F, 14F, 4F),
                PartPose.offsetAndRotation(2F, 10F, 0F, 0F, 0F, 0F));
        PartDefinition d_bipedHead = root.addOrReplaceChild("bipedhead", CubeListBuilder.create().texOffs(0, 0).addBox(-4F, -8F, -4F, 8F, 8F, 8F),
                PartPose.offsetAndRotation(0F, 0F, 0F, 0F, 0F, 0F));
        PartDefinition d_longHair = d_bipedHead.addOrReplaceChild("longhair", CubeListBuilder.create().texOffs(24, 0).addBox(-4F, 0F, -3F, 8F, 2F, 3F),
                PartPose.offsetAndRotation(0F, 0F, 4F, 0F, 0F, 0F));
        PartDefinition d_Grass = d_bipedHead.addOrReplaceChild("grass", CubeListBuilder.create().texOffs(48, 0).addBox(-4F, 0F, 0F, 8F, 2F, 1F),
                PartPose.offsetAndRotation(0F, -3F, -4.2F, 0F, 0F, 0F));
        return LayerDefinition.create(mesh, 64, 64);
    }

    /** The parts X1's render() draws, in its order. */
    private ModelPart[] drawn() {
        return new ModelPart[] {bipedBody, bipedRightArm, bipedLeftArm, bipedRightLeg, bipedLeftLeg, bipedHead};
    }

    @Override
    public void setupAnim(RinnosukeEntity e, float movement, float far, float tick, float yaw, float pitch) {
        this.bipedHead.yRot = yaw / (180F / (float) Math.PI);
        this.bipedHead.xRot = pitch / (180F / (float) Math.PI);
        this.bipedBody.yRot = Mth.sin(Mth.sqrt(this.attackTime) * (float) Math.PI * 2.0F) * 0.2F;
        bipedRightLeg.xRot = Mth.cos(movement * 0.6662F) * 0.7F * far;
        bipedLeftLeg.xRot = Mth.cos(movement * 0.6662F + (float) Math.PI) * 0.7F * far;
        this.bipedRightLeg.yRot = 0.0F;
        this.bipedLeftLeg.yRot = 0.0F;
        this.bipedRightLeg.zRot = 0.0F;
        this.bipedLeftLeg.zRot = 0.0F;
        this.bipedRightArm.xRot = Mth.cos(movement * 0.6662F + (float) Math.PI) * 2.0F * far * 0.5F;
        this.bipedLeftArm.xRot = Mth.cos(movement * 0.6662F) * 2.0F * far * 0.5F;
        bipedRightArm.zRot = 10F / 180F * (float) Math.PI;
        bipedLeftArm.zRot = -bipedRightArm.zRot;
        if (this.riding) {
            this.bipedRightArm.xRot = -((float) Math.PI / 5F);
            this.bipedLeftArm.xRot = -((float) Math.PI / 5F);
            this.bipedRightLeg.xRot = -((float) Math.PI * 2F / 5F);
            this.bipedLeftLeg.xRot = -((float) Math.PI * 2F / 5F);
            this.bipedRightLeg.yRot = ((float) Math.PI / 14F);
            this.bipedLeftLeg.yRot = -((float) Math.PI / 14F);
            this.bipedRightLeg.zRot = ((float) Math.PI / 14F);
            this.bipedLeftLeg.zRot = -((float) Math.PI / 14F);
        }
        this.bipedRightArm.zRot += Mth.cos(tick * 0.09F) * 0.05F + 0.05F;
        this.bipedLeftArm.zRot -= Mth.cos(tick * 0.09F) * 0.05F + 0.05F;
        this.bipedRightArm.xRot += Mth.sin(tick * 0.067F) * 0.05F;
        this.bipedLeftArm.xRot -= Mth.sin(tick * 0.067F) * 0.05F;

    }

    @Override
    public void renderToBuffer(PoseStack pose, VertexConsumer consumer, int light, int overlay, float r, float g, float b, float a) {
        for (ModelPart p : drawn()) p.render(pose, consumer, light, overlay, r, g, b, a);
    }
}
