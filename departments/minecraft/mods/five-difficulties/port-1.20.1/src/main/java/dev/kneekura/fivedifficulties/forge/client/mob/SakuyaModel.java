package dev.kneekura.fivedifficulties.forge.client.mob;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import dev.kneekura.fivedifficulties.forge.entity.mob.SakuyaEntity;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeDeformation;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.util.Mth;

/** Port of X1 {@code ModelSakuya}: boxes generated from the X1 constructor; animation ported by hand. */
public class SakuyaModel extends EntityModel<SakuyaEntity> {
    // ---- generated from ModelSakuya.java ----
    private final ModelPart bipedBody;
    private final ModelPart bipedRightArm;
    private final ModelPart bipedLeftArm;
    private final ModelPart bipedRightLeg;
    private final ModelPart bipedLeftLeg;
    private final ModelPart skirtTop;
    private final ModelPart skirtBottom;
    private final ModelPart leftRibbon;
    private final ModelPart rightRibbon;
    private final ModelPart bipedHead;
    private final ModelPart longHair;
    private final ModelPart leftBraid;
    private final ModelPart rightBraid;
    private final ModelPart leftKatyusha;
    private final ModelPart rightKatyusha;

    public SakuyaModel(ModelPart root) {
        this.bipedBody = root.getChild("bipedbody");
        this.bipedRightArm = root.getChild("bipedbody").getChild("bipedrightarm");
        this.bipedLeftArm = root.getChild("bipedbody").getChild("bipedleftarm");
        this.bipedRightLeg = root.getChild("bipedbody").getChild("bipedrightleg");
        this.bipedLeftLeg = root.getChild("bipedbody").getChild("bipedleftleg");
        this.skirtTop = root.getChild("bipedbody").getChild("skirttop");
        this.skirtBottom = root.getChild("bipedbody").getChild("skirttop").getChild("skirtbottom");
        this.leftRibbon = root.getChild("bipedbody").getChild("leftribbon");
        this.rightRibbon = root.getChild("bipedbody").getChild("rightribbon");
        this.bipedHead = root.getChild("bipedbody").getChild("bipedhead");
        this.longHair = root.getChild("bipedbody").getChild("bipedhead").getChild("longhair");
        this.leftBraid = root.getChild("bipedbody").getChild("bipedhead").getChild("leftbraid");
        this.rightBraid = root.getChild("bipedbody").getChild("bipedhead").getChild("rightbraid");
        this.leftKatyusha = root.getChild("bipedbody").getChild("bipedhead").getChild("leftkatyusha");
        this.rightKatyusha = root.getChild("bipedbody").getChild("bipedhead").getChild("rightkatyusha");
    }

    public static LayerDefinition createBodyLayer() {
        MeshDefinition mesh = new MeshDefinition();
        PartDefinition root = mesh.getRoot();
        PartDefinition d_bipedBody = root.addOrReplaceChild("bipedbody", CubeListBuilder.create().texOffs(32, 8).addBox(-3F, 0F, -2F, 6F, 9F, 4F),
                PartPose.offsetAndRotation(0F, 1F, 0F, 0F, 0F, 0F));
        PartDefinition d_bipedRightArm = d_bipedBody.addOrReplaceChild("bipedrightarm", CubeListBuilder.create().texOffs(48, 0).addBox(-1F, -1F, -1F, 2F, 8F, 2F),
                PartPose.offsetAndRotation(-4F, 2F, 0F, -0.7679449F, 0F, -0.6457718F));
        PartDefinition d_bipedLeftArm = d_bipedBody.addOrReplaceChild("bipedleftarm", CubeListBuilder.create().texOffs(56, 0).addBox(-1F, -1F, -1F, 2F, 8F, 2F),
                PartPose.offsetAndRotation(4F, 2F, 0F, -0.7679449F, 0F, 0.6457718F));
        PartDefinition d_bipedRightLeg = d_bipedBody.addOrReplaceChild("bipedrightleg", CubeListBuilder.create().texOffs(50, 18).addBox(-1F, 0F, -2F, 3F, 14F, 4F),
                PartPose.offsetAndRotation(-2F, 10F, 0F, 0F, 0F, 0F));
        PartDefinition d_bipedLeftLeg = d_bipedBody.addOrReplaceChild("bipedleftleg", CubeListBuilder.create().texOffs(50, 18).addBox(-2F, 0F, -2F, 3F, 14F, 4F),
                PartPose.offsetAndRotation(2F, 10F, 0F, 0F, 0F, 0F));
        PartDefinition d_skirtTop = d_bipedBody.addOrReplaceChild("skirttop", CubeListBuilder.create().texOffs(0, 16).addBox(-4F, 0F, -4F, 8F, 4F, 8F),
                PartPose.offsetAndRotation(0F, 6F, 0F, 0F, 0F, 0F));
        PartDefinition d_skirtBottom = d_skirtTop.addOrReplaceChild("skirtbottom", CubeListBuilder.create().texOffs(16, 32).addBox(-5F, 0F, -5F, 10F, 5F, 10F),
                PartPose.offsetAndRotation(0F, 4F, 0F, 0F, 0F, 0F));
        PartDefinition d_leftRibbon = d_bipedBody.addOrReplaceChild("leftribbon", CubeListBuilder.create().texOffs(0, 38).addBox(0F, 0F, 0F, 5F, 4F, 1F),
                PartPose.offsetAndRotation(0F, 5F, 3F, 0.4886922F, -0.3F, -0.296706F));
        PartDefinition d_rightRibbon = d_bipedBody.addOrReplaceChild("rightribbon", CubeListBuilder.create().texOffs(0, 38).addBox(0F, 0F, -1F, 5F, 4F, 1F),
                PartPose.offsetAndRotation(0F, 5F, 3F, -0.4886922F, -(float)Math.PI + 0.3F, 0.296706F));
        PartDefinition d_bipedHead = d_bipedBody.addOrReplaceChild("bipedhead", CubeListBuilder.create().texOffs(0, 0).addBox(-4F, -8F, -4F, 8F, 8F, 8F),
                PartPose.offsetAndRotation(0F, 1F, 0F, 0F, 0F, 0F));
        PartDefinition d_longHair = d_bipedHead.addOrReplaceChild("longhair", CubeListBuilder.create().texOffs(24, 0).addBox(-4F, -2F, -4F, 8F, 5F, 3F),
                PartPose.offsetAndRotation(0F, 0F, 4F, 0.2094395F, 0F, 0F));
        PartDefinition d_leftBraid = d_bipedHead.addOrReplaceChild("leftbraid", CubeListBuilder.create().texOffs(0, 32).addBox(0F, -1F, -1F, 1F, 5F, 1F),
                PartPose.offsetAndRotation(3F, -1F, -3F, -0.2443461F, 0F, 0F));
        PartDefinition d_rightBraid = d_bipedHead.addOrReplaceChild("rightbraid", CubeListBuilder.create().texOffs(0, 32).addBox(-1F, -1F, -1F, 1F, 5F, 1F),
                PartPose.offsetAndRotation(-3F, -1F, -3F, -0.2443461F, 0F, 0F));
        PartDefinition d_leftKatyusha = d_bipedHead.addOrReplaceChild("leftkatyusha", CubeListBuilder.create().texOffs(4, 32).addBox(0F, -1F, 0F, 4F, 1F, 1F),
                PartPose.offsetAndRotation(0F, -8F, -5F, 0F, -0.1745329F, 0.2268928F));
        PartDefinition d_rightKatyusha = d_bipedHead.addOrReplaceChild("rightkatyusha", CubeListBuilder.create().texOffs(4, 32).addBox(-4F, -1F, 0F, 4F, 1F, 1F),
                PartPose.offsetAndRotation(0F, -8F, -5F, 0F, 0.1745329F, -0.2268928F));
        return LayerDefinition.create(mesh, 64, 64);
    }

    /** The parts X1's render() draws, in its order. */
    private ModelPart[] drawn() {
        return new ModelPart[] {bipedBody};
    }

    @Override
    public void setupAnim(SakuyaEntity e, float movement, float far, float tick, float yaw, float pitch) {
        // setDefaultPause (bodyHeight 9)
        bipedHead.setPos(0.0F, 0.0F, 0.0F);
        bipedBody.setPos(0.0F, 1.0F, 0.0F);
        bipedRightArm.setPos(-3.0F, 1.0F, 0.0F);
        bipedLeftArm.setPos(3.0F, 1.0F, 0.0F);
        bipedRightLeg.setPos(-2.0F, 9F, 0.0F);
        bipedLeftLeg.setPos(2.0F, 9F, 0.0F);
        bipedRightLeg.x = -2.0F;
        bipedLeftLeg.x = 2.0F;
        bipedHead.yRot = yaw / 57.29578F;
        bipedHead.xRot = pitch / 57.29578F;
        bipedRightArm.xRot = Mth.cos(movement * 0.6662F + 3.141593F) * 2.0F * far * 0.5F;
        bipedLeftArm.xRot = Mth.cos(movement * 0.6662F) * 2.0F * far * 0.5F;
        bipedRightArm.zRot = 30F / 180F * 3.141593F;
        bipedLeftArm.zRot = -30F / 180F * 3.141593F;
        this.skirtTop.xRot = 0.0F;
        this.skirtBottom.z = 0.0F;
        this.skirtBottom.xRot = 0.0F;
        // X1 quirk kept: the body / skirt Y turn is only ever written while sneaking (and then sticks).
        if (e.isShiftKeyDown()) {
            bipedBody.yRot = Mth.cos(movement * 0.6662F + (float) Math.PI) * 2.4F * far;
            skirtTop.yRot = Mth.cos(movement * 0.6662F + (float) Math.PI) * 2.4F * far;
            bipedRightArm.xRot = Mth.cos(movement * 0.6662F + (float) Math.PI) * 1.4F * far;
            bipedLeftArm.xRot = Mth.cos(movement * 0.6662F) * 1.4F * far;
        }
        bipedRightLeg.xRot = Mth.cos(movement * 0.6662F) * 0.5F * far;
        bipedLeftLeg.xRot = Mth.cos(movement * 0.6662F + (float) Math.PI) * 0.5F * far;
        bipedRightLeg.yRot = bipedLeftLeg.yRot = bipedRightLeg.zRot = bipedLeftLeg.zRot = 0.0F;
        if (e.isPassenger()) {
            this.bipedBody.y = -1F;
            this.bipedRightLeg.y = 5.0F;
            this.bipedLeftLeg.y = 5.0F;
            this.bipedRightArm.xRot += -((float) Math.PI / 5F);
            this.bipedLeftArm.xRot += -((float) Math.PI / 5F);
            this.bipedRightLeg.xRot = -((float) Math.PI * 2F / 5F);
            this.bipedLeftLeg.xRot = -((float) Math.PI * 2F / 5F);
            this.bipedRightLeg.yRot = ((float) Math.PI / 14F);
            this.bipedLeftLeg.yRot = -((float) Math.PI / 14F);
            this.bipedRightLeg.zRot = ((float) Math.PI / 14F);
            this.bipedLeftLeg.zRot = -((float) Math.PI / 14F);
            skirtTop.y = 5F;
            skirtTop.z = 0F;
            this.skirtTop.xRot = -((float) Math.PI / 5F);
            skirtBottom.z = 0.0F;
            skirtBottom.y = 4F;
            this.skirtBottom.xRot = -((float) Math.PI / 4F);
        } else {
            skirtTop.y = 5F;
            skirtTop.z = 0F;
            skirtBottom.z = 0.0F;
            skirtBottom.y = 4.0F;
            this.bipedRightLeg.y = 9F;
            this.bipedLeftLeg.y = 9F;
        }
        bipedRightArm.yRot = bipedLeftArm.yRot = 0.0F;
        bipedRightLeg.z = bipedLeftLeg.z = bipedBody.xRot = bipedBody.zRot = 0.0F;
        if (e.isShiftKeyDown()) bipedHead.xRot -= 0.5F;

    }

    @Override
    public void renderToBuffer(PoseStack pose, VertexConsumer consumer, int light, int overlay, float r, float g, float b, float a) {
        for (ModelPart p : drawn()) p.render(pose, consumer, light, overlay, r, g, b, a);
    }
}
