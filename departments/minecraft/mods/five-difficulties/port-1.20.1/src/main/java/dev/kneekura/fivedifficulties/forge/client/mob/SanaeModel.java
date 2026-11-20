package dev.kneekura.fivedifficulties.forge.client.mob;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import dev.kneekura.fivedifficulties.forge.entity.mob.SanaeEntity;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeDeformation;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.util.Mth;

/** Port of X1 {@code ModelSanae}: boxes generated from the X1 constructor; animation ported by hand. */
public class SanaeModel extends EntityModel<SanaeEntity> {
    // ---- generated from ModelSanae.java ----
    private final ModelPart bipedBody;
    private final ModelPart bipedRightArm;
    private final ModelPart rightHand;
    private final ModelPart bipedLeftArm;
    private final ModelPart leftHand;
    private final ModelPart bipedRightLeg;
    private final ModelPart bipedLeftLeg;
    private final ModelPart skirtTop;
    private final ModelPart skirtBottom;
    private final ModelPart bipedHead;
    private final ModelPart longHair;
    private final ModelPart leftBraid;
    private final ModelPart rightBraid;
    private final ModelPart leftBraid2;
    private final ModelPart kaeruBase;
    private final ModelPart kaeruEyeRight;
    private final ModelPart kaeruEyeLeft;

    public SanaeModel(ModelPart root) {
        this.bipedBody = root.getChild("bipedbody");
        this.bipedRightArm = root.getChild("bipedrightarm");
        this.rightHand = root.getChild("bipedrightarm").getChild("righthand");
        this.bipedLeftArm = root.getChild("bipedleftarm");
        this.leftHand = root.getChild("bipedleftarm").getChild("lefthand");
        this.bipedRightLeg = root.getChild("bipedrightleg");
        this.bipedLeftLeg = root.getChild("bipedleftleg");
        this.skirtTop = root.getChild("bipedbody").getChild("skirttop");
        this.skirtBottom = root.getChild("bipedbody").getChild("skirttop").getChild("skirtbottom");
        this.bipedHead = root.getChild("bipedhead");
        this.longHair = root.getChild("bipedhead").getChild("longhair");
        this.leftBraid = root.getChild("bipedhead").getChild("leftbraid");
        this.rightBraid = root.getChild("bipedhead").getChild("rightbraid");
        this.leftBraid2 = root.getChild("bipedhead").getChild("leftbraid2");
        this.kaeruBase = root.getChild("bipedhead").getChild("kaerubase");
        this.kaeruEyeRight = root.getChild("bipedhead").getChild("kaerueyeright");
        this.kaeruEyeLeft = root.getChild("bipedhead").getChild("kaerueyeleft");
    }

    public static LayerDefinition createBodyLayer() {
        MeshDefinition mesh = new MeshDefinition();
        PartDefinition root = mesh.getRoot();
        PartDefinition d_bipedBody = root.addOrReplaceChild("bipedbody", CubeListBuilder.create().texOffs(32, 8).addBox(-3F, 0F, -2F, 6F, 9F, 4F),
                PartPose.offsetAndRotation(0F, 2F, 0F, 0F, 0F, 0F));
        PartDefinition d_skirtTop = d_bipedBody.addOrReplaceChild("skirttop", CubeListBuilder.create().texOffs(0, 16).addBox(-4F, -2F, -4F, 8F, 4F, 8F),
                PartPose.offsetAndRotation(0F, 8F, 0F, 0F, 0F, 0F));
        PartDefinition d_skirtBottom = d_skirtTop.addOrReplaceChild("skirtbottom", CubeListBuilder.create().texOffs(16, 32).addBox(-5F, -2F, -5F, 10F, 8F, 10F),
                PartPose.offsetAndRotation(0F, 4F, 0F, 0F, 0F, 0F));
        PartDefinition d_bipedRightArm = root.addOrReplaceChild("bipedrightarm", CubeListBuilder.create().texOffs(48, 0).addBox(0F, 0F, -1F, 4F, 7F, 2F),
                PartPose.offsetAndRotation(-3F, 2F, 0F, 0F, 0F, 0F));
        PartDefinition d_rightHand = d_bipedRightArm.addOrReplaceChild("righthand", CubeListBuilder.create().texOffs(52, 9).addBox(0F, 1F, -1F, 2F, 1F, 2F),
                PartPose.offsetAndRotation(-0F, 6F, 0F, 0F, 0F, 0F));
        PartDefinition d_bipedLeftArm = root.addOrReplaceChild("bipedleftarm", CubeListBuilder.create().texOffs(48, 0).addBox(-4F, 0F, -1F, 4F, 7F, 2F),
                PartPose.offsetAndRotation(3F, 2F, 0F, 0F, 0F, 0F));
        PartDefinition d_leftHand = d_bipedLeftArm.addOrReplaceChild("lefthand", CubeListBuilder.create().texOffs(52, 9).addBox(-2F, 1F, -1F, 2F, 1F, 2F),
                PartPose.offsetAndRotation(0F, 6F, 0F, 0F, 0F, 0F));
        PartDefinition d_bipedRightLeg = root.addOrReplaceChild("bipedrightleg", CubeListBuilder.create().texOffs(50, 18).addBox(-1F, 0F, -2F, 3F, 13F, 4F),
                PartPose.offsetAndRotation(-2F, 11F, 0F, 0F, 0F, 0F));
        PartDefinition d_bipedLeftLeg = root.addOrReplaceChild("bipedleftleg", CubeListBuilder.create().texOffs(50, 18).addBox(-2F, 0F, -2F, 3F, 13F, 4F),
                PartPose.offsetAndRotation(2F, 11F, 0F, 0F, 0F, 0F));
        PartDefinition d_bipedHead = root.addOrReplaceChild("bipedhead", CubeListBuilder.create().texOffs(0, 0).addBox(-4F, -6F, -4F, 8F, 8F, 8F),
                PartPose.offsetAndRotation(0F, 2F, 0F, 0F, 0F, 0F));
        PartDefinition d_longHair = d_bipedHead.addOrReplaceChild("longhair", CubeListBuilder.create().texOffs(0, 50).addBox(-4F, 1F, -3F, 8F, 9F, 3F),
                PartPose.offsetAndRotation(0F, -1F, 4F, 0.2094395F, 0F, 0F));
        PartDefinition d_leftBraid = d_bipedHead.addOrReplaceChild("leftbraid", CubeListBuilder.create().texOffs(4, 32).addBox(0F, 1F, -1F, 1F, 5F, 1F),
                PartPose.offsetAndRotation(3F, -3F, -3F, -0.2443461F, 0F, 0F));
        PartDefinition d_rightBraid = d_bipedHead.addOrReplaceChild("rightbraid", CubeListBuilder.create().texOffs(0, 32).addBox(-1F, 1F, -1F, 1F, 5F, 1F),
                PartPose.offsetAndRotation(-3F, -3F, -3F, -0.2443461F, 0F, 0F));
        PartDefinition d_leftBraid2 = d_bipedHead.addOrReplaceChild("leftbraid2", CubeListBuilder.create().texOffs(8, 31).addBox(-1F, 2F, -1F, 2F, 5F, 2F),
                PartPose.offsetAndRotation(3F, 0F, -4F, -0.2443461F, 0F, 0F));
        PartDefinition d_kaeruBase = d_bipedHead.addOrReplaceChild("kaerubase", CubeListBuilder.create().texOffs(0, 38).addBox(-2F, 1F, -1F, 3F, 2F, 1F),
                PartPose.offsetAndRotation(3F, -7F, -4F, 0F, 0F, 0.3839724F));
        PartDefinition d_kaeruEyeRight = d_bipedHead.addOrReplaceChild("kaerueyeright", CubeListBuilder.create().texOffs(8, 38).addBox(-1F, 2F, -1F, 1F, 1F, 1F),
                PartPose.offsetAndRotation(2.7F, -9F, -4F, 0F, 0F, 0.3839724F));
        PartDefinition d_kaeruEyeLeft = d_bipedHead.addOrReplaceChild("kaerueyeleft", CubeListBuilder.create().texOffs(8, 38).addBox(0F, 2F, -1F, 1F, 1F, 1F),
                PartPose.offsetAndRotation(3.7F, -8.7F, -4F, 0F, 0F, 0.3839724F));
        return LayerDefinition.create(mesh, 64, 64);
    }

    /** The parts X1's render() draws, in its order. */
    private ModelPart[] drawn() {
        return new ModelPart[] {bipedBody, bipedRightArm, bipedLeftArm, bipedRightLeg, bipedLeftLeg, bipedHead};
    }

    @Override
    public void setupAnim(SanaeEntity e, float movement, float far, float tick, float yaw, float pitch) {
        this.skirtTop.xRot = 0.0F;
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
        bipedRightArm.yRot = -10F / 180F * (float) Math.PI;
        bipedRightArm.zRot = 30F / 180F * (float) Math.PI;
        bipedLeftArm.yRot = -bipedRightArm.yRot;
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
            this.skirtTop.xRot += -((float) Math.PI / 5F);
        }
        this.bipedRightArm.zRot += Mth.cos(tick * 0.09F) * 0.05F + 0.05F;
        this.bipedLeftArm.zRot -= Mth.cos(tick * 0.09F) * 0.05F + 0.05F;
        this.bipedRightArm.xRot += Mth.sin(tick * 0.067F) * 0.05F;
        this.bipedLeftArm.xRot -= Mth.sin(tick * 0.067F) * 0.05F;
        // X1 sets the arms again after drawing (card pose); the next setRotationAngles overwrites them first, so
        // it never shows.

    }

    @Override
    public void renderToBuffer(PoseStack pose, VertexConsumer consumer, int light, int overlay, float r, float g, float b, float a) {
        for (ModelPart p : drawn()) p.render(pose, consumer, light, overlay, r, g, b, a);
    }
}
