package dev.kneekura.fivedifficulties.forge.client.mob;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import dev.kneekura.fivedifficulties.forge.entity.mob.SunFlowerFairyEntity;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeDeformation;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.util.Mth;

/** Port of X1 {@code ModelSunFlowerFairy} (128 × 64): boxes generated from the X1 constructor; animation ported by hand. */
public class SunFlowerFairyModel extends EntityModel<SunFlowerFairyEntity> {
    // ---- generated from ModelSunFlowerFairy.java ----
    private final ModelPart bipedBody;
    private final ModelPart bipedRightArm;
    private final ModelPart bipedLeftArm;
    private final ModelPart bipedRightLeg;
    private final ModelPart bipedLeftLeg;
    private final ModelPart skirtTop;
    private final ModelPart skirtBottom;
    private final ModelPart leftWing;
    private final ModelPart rightWing;
    private final ModelPart himawari1;
    private final ModelPart himawari2;
    private final ModelPart bipedHead;
    private final ModelPart longHair;
    private final ModelPart rightRibbon;
    private final ModelPart rightTail;
    private final ModelPart leftRibbon;
    private final ModelPart leftTail;

    public SunFlowerFairyModel(ModelPart root) {
        this.bipedBody = root.getChild("bipedbody");
        this.bipedRightArm = root.getChild("bipedrightarm");
        this.bipedLeftArm = root.getChild("bipedleftarm");
        this.bipedRightLeg = root.getChild("bipedrightleg");
        this.bipedLeftLeg = root.getChild("bipedleftleg");
        this.skirtTop = root.getChild("bipedbody").getChild("skirttop");
        this.skirtBottom = root.getChild("bipedbody").getChild("skirttop").getChild("skirtbottom");
        this.leftWing = root.getChild("bipedbody").getChild("leftwing");
        this.rightWing = root.getChild("bipedbody").getChild("rightwing");
        this.himawari1 = root.getChild("bipedleftarm").getChild("himawari1");
        this.himawari2 = root.getChild("bipedleftarm").getChild("himawari2");
        this.bipedHead = root.getChild("bipedhead");
        this.longHair = root.getChild("bipedhead").getChild("longhair");
        this.rightRibbon = root.getChild("bipedhead").getChild("rightribbon");
        this.rightTail = root.getChild("bipedhead").getChild("righttail");
        this.leftRibbon = root.getChild("bipedhead").getChild("leftribbon");
        this.leftTail = root.getChild("bipedhead").getChild("lefttail");
    }

    public static LayerDefinition createBodyLayer() {
        MeshDefinition mesh = new MeshDefinition();
        PartDefinition root = mesh.getRoot();
        PartDefinition d_bipedBody = root.addOrReplaceChild("bipedbody", CubeListBuilder.create().texOffs(32, 8).addBox(-3F, 0F, -2F, 6F, 7F, 4F),
                PartPose.offsetAndRotation(0F, 5F, 0F, 0F, 0F, 0F));
        PartDefinition d_skirtTop = d_bipedBody.addOrReplaceChild("skirttop", CubeListBuilder.create().texOffs(0, 16).addBox(-4F, 5F, -4F, 8F, 4F, 8F),
                PartPose.offsetAndRotation(0F, 0F, 0F, 0F, 0F, 0F));
        PartDefinition d_skirtBottom = d_skirtTop.addOrReplaceChild("skirtbottom", CubeListBuilder.create().texOffs(32, 32).addBox(-5F, 0F, -5F, 10F, 6F, 10F),
                PartPose.offsetAndRotation(0F, 9F, 0F, 0F, 0F, 0F));
        PartDefinition d_leftWing = d_bipedBody.addOrReplaceChild("leftwing", CubeListBuilder.create().texOffs(64, 0).addBox(-1F, -16F, 0F, 20F, 26F, 1F),
                PartPose.offsetAndRotation(2F, 3F, 2F, 0F, -0.4886922F, 0.0167304F));
        PartDefinition d_rightWing = d_bipedBody.addOrReplaceChild("rightwing", CubeListBuilder.create().texOffs(72, 32).addBox(-1F, -16F, 0F, 20F, 26F, 1F),
                PartPose.offsetAndRotation(-2F, 3F, 2F, 0F, -2.6529F, 0.0167304F));
        PartDefinition d_bipedRightArm = root.addOrReplaceChild("bipedrightarm", CubeListBuilder.create().texOffs(48, 0).addBox(-1F, -1F, -1F, 2F, 8F, 2F),
                PartPose.offsetAndRotation(-4F, 6F, 0F, -0.7679449F, 0F, -0.6457718F));
        PartDefinition d_bipedLeftArm = root.addOrReplaceChild("bipedleftarm", CubeListBuilder.create().texOffs(56, 0).addBox(-1F, -1F, -1F, 2F, 8F, 2F),
                PartPose.offsetAndRotation(4F, 6F, 0F, -0.7679449F, 0F, 0.6457718F));
        PartDefinition d_himawari1 = d_bipedLeftArm.addOrReplaceChild("himawari1", CubeListBuilder.create().texOffs(0, 32).addBox(-7F, -20F, 0F, 12F, 31F, 1F),
                PartPose.offsetAndRotation(0F, 6F, -2F, 0.4089647F, -0.7435722F, 0.3666439F));
        PartDefinition d_himawari2 = d_bipedLeftArm.addOrReplaceChild("himawari2", CubeListBuilder.create().texOffs(0, 32).addBox(-7F, -20F, 0F, 12F, 31F, 1F),
                PartPose.offsetAndRotation(-1F, 6F, -2F, 0.2230717F, -0.669215F, 0.2551081F));
        PartDefinition d_bipedRightLeg = root.addOrReplaceChild("bipedrightleg", CubeListBuilder.create().texOffs(50, 16).addBox(-1F, 0F, -2F, 3F, 11F, 4F),
                PartPose.offsetAndRotation(-2F, 12F, 0F, 0F, 0F, 0F));
        PartDefinition d_bipedLeftLeg = root.addOrReplaceChild("bipedleftleg", CubeListBuilder.create().texOffs(50, 16).addBox(-2F, 0F, -2F, 3F, 11F, 4F),
                PartPose.offsetAndRotation(2F, 12F, 0F, 0F, 0F, 0F));
        PartDefinition d_bipedHead = root.addOrReplaceChild("bipedhead", CubeListBuilder.create().texOffs(0, 0).addBox(-4F, -8F, -4F, 8F, 8F, 8F),
                PartPose.offsetAndRotation(0F, 5F, 0F, 0F, 0F, 0F));
        PartDefinition d_longHair = d_bipedHead.addOrReplaceChild("longhair", CubeListBuilder.create().texOffs(24, 0).addBox(-4F, 4F, -3F, 8F, 5F, 3F),
                PartPose.offsetAndRotation(0F, -5F, 4F, 0F, 0F, 0F));
        PartDefinition d_rightRibbon = d_bipedHead.addOrReplaceChild("rightribbon", CubeListBuilder.create().texOffs(32, 19).addBox(-3F, -2F, -1F, 5F, 4F, 1F),
                PartPose.offsetAndRotation(-4F, -7F, 0F, -0.4712389F, 1.570796F, 0F));
        PartDefinition d_rightTail = d_bipedHead.addOrReplaceChild("righttail", CubeListBuilder.create().texOffs(32, 24).addBox(-2F, -1F, -2F, 3F, 8F, 2F),
                PartPose.offsetAndRotation(-5F, -7F, 0F, -0.2617994F, 1.570796F, 0F));
        PartDefinition d_leftRibbon = d_bipedHead.addOrReplaceChild("leftribbon", CubeListBuilder.create().texOffs(32, 19).addBox(-3F, -2F, 0F, 5F, 4F, 1F),
                PartPose.offsetAndRotation(4F, -7F, 0F, 0.4712389F, 1.570796F, 0F));
        PartDefinition d_leftTail = d_bipedHead.addOrReplaceChild("lefttail", CubeListBuilder.create().texOffs(32, 24).addBox(-2F, -1F, 0F, 3F, 8F, 2F),
                PartPose.offsetAndRotation(5F, -7F, 0F, 0.2617994F, 1.570796F, 0F));
        return LayerDefinition.create(mesh, 128, 64);
    }

    /** The parts X1's render() draws, in its order. */
    private ModelPart[] drawn() {
        return new ModelPart[] {bipedBody, bipedRightArm, bipedLeftArm, bipedRightLeg, bipedLeftLeg, bipedHead};
    }

    @Override
    public void setupAnim(SunFlowerFairyEntity fairy, float movement, float far, float tick, float yaw, float pitch) {
        this.bipedHead.yRot = yaw / (180F / (float) Math.PI);
        this.bipedHead.xRot = pitch / (180F / (float) Math.PI);
        this.bipedBody.yRot = Mth.sin(Mth.sqrt(this.attackTime) * (float) Math.PI * 2.0F) * 0.2F;
        this.skirtTop.xRot = 0F;
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
        } else if (fairy.getFlyingHeight() == 0) {
            bipedRightLeg.xRot = Mth.cos(movement) * 0.7F * far;
            bipedLeftLeg.xRot = Mth.cos(movement + (float) Math.PI) * 0.7F * far;
            bipedRightLeg.zRot = 0F;
            bipedLeftLeg.zRot = 0F;
            if (movement > 0F) {
                this.bipedRightArm.xRot = Mth.cos(movement + (float) Math.PI) * 2.0F * far * 0.5F;
                this.bipedLeftArm.xRot = Mth.cos(movement) * 2.0F * far * 0.5F;
                bipedRightArm.yRot = -10F / 180F * (float) Math.PI;
                bipedRightArm.zRot = 20F / 180F * (float) Math.PI;
                bipedLeftArm.yRot = -bipedRightArm.yRot;
                bipedLeftArm.zRot = -bipedRightArm.zRot;
            } else {
                restingArms(tick);
            }
        } else {
            bipedRightLeg.zRot = Math.abs(Mth.sin(tick / 10F) * 0.1F);
            bipedLeftLeg.zRot = -bipedRightLeg.zRot;
            bipedRightLeg.xRot = Math.abs(Mth.sin(tick / 10F) * 0.2F);
            bipedLeftLeg.xRot = bipedRightLeg.zRot;
            restingArms(tick);
        }
        if (fairy.getHealth() > 0F) {
            this.bipedBody.xRot = 0F;
            if (fairy.getFlyingHeight() > 0) {
                this.rightWing.yRot = Mth.cos(tick * 1.3F) * (float) Math.PI * 0.25F - (float) Math.PI;
                this.leftWing.yRot = -Mth.cos(tick * 1.3F) * (float) Math.PI * 0.25F;
            } else {
                this.rightWing.yRot = Mth.cos(tick * 0.5F) * (float) Math.PI * 0.1F - (float) Math.PI;
                this.leftWing.yRot = -Mth.cos(tick * 0.5F) * (float) Math.PI * 0.1F;
            }
        } else {
            this.bipedHead.xRot = 70F;
            this.bipedHead.yRot = 0F;
            this.bipedHead.zRot = 0F;
            this.rightWing.yRot = -25F;
            this.leftWing.yRot = 25F;
        }
    }

    private void restingArms(float tick) {
        bipedRightArm.xRot = -0.7F - Mth.sin(tick / 10F) * 0.1F;
        bipedRightArm.yRot = 0.0F;
        bipedRightArm.zRot = -0.6457718F;
        bipedLeftArm.xRot = bipedRightArm.xRot;
        bipedLeftArm.yRot = 0.0F;
        bipedLeftArm.zRot = 0.6457718F;
    }

    @Override
    public void renderToBuffer(PoseStack pose, VertexConsumer consumer, int light, int overlay, float r, float g, float b, float a) {
        for (ModelPart p : drawn()) p.render(pose, consumer, light, overlay, r, g, b, a);
    }
}
