package dev.kneekura.fivedifficulties.forge.client.mob;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import dev.kneekura.fivedifficulties.forge.entity.mob.ReimuEntity;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeDeformation;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.util.Mth;

/** Port of X1 {@code ModelReimu}: boxes generated from the X1 constructor; animation ported by hand. */
public class ReimuModel extends EntityModel<ReimuEntity> {
    // ---- generated from ModelReimu.java ----
    private final ModelPart bipedBody;
    private final ModelPart bipedRightArm;
    private final ModelPart handRight;
    private final ModelPart bipedLeftArm;
    private final ModelPart handLeft;
    private final ModelPart bipedRightLeg;
    private final ModelPart bipedLeftLeg;
    private final ModelPart skirtTop;
    private final ModelPart skirtBottom;
    private final ModelPart bipedHead;
    private final ModelPart longHair;
    private final ModelPart braidLeft;
    private final ModelPart braidRight;
    private final ModelPart leftRibbon;
    private final ModelPart rightRibbon;
    private final ModelPart rightRibbon2;
    private final ModelPart leftRibbon2;

    public ReimuModel(ModelPart root) {
        this.bipedBody = root.getChild("bipedbody");
        this.bipedRightArm = root.getChild("bipedbody").getChild("bipedrightarm");
        this.handRight = root.getChild("bipedbody").getChild("bipedrightarm").getChild("handright");
        this.bipedLeftArm = root.getChild("bipedbody").getChild("bipedleftarm");
        this.handLeft = root.getChild("bipedbody").getChild("bipedleftarm").getChild("handleft");
        this.bipedRightLeg = root.getChild("bipedbody").getChild("bipedrightleg");
        this.bipedLeftLeg = root.getChild("bipedbody").getChild("bipedleftleg");
        this.skirtTop = root.getChild("bipedbody").getChild("skirttop");
        this.skirtBottom = root.getChild("bipedbody").getChild("skirttop").getChild("skirtbottom");
        this.bipedHead = root.getChild("bipedbody").getChild("bipedhead");
        this.longHair = root.getChild("bipedbody").getChild("bipedhead").getChild("longhair");
        this.braidLeft = root.getChild("bipedbody").getChild("bipedhead").getChild("braidleft");
        this.braidRight = root.getChild("bipedbody").getChild("bipedhead").getChild("braidright");
        this.leftRibbon = root.getChild("bipedbody").getChild("bipedhead").getChild("leftribbon");
        this.rightRibbon = root.getChild("bipedbody").getChild("bipedhead").getChild("rightribbon");
        this.rightRibbon2 = root.getChild("bipedbody").getChild("bipedhead").getChild("rightribbon2");
        this.leftRibbon2 = root.getChild("bipedbody").getChild("bipedhead").getChild("leftribbon2");
    }

    public static LayerDefinition createBodyLayer() {
        MeshDefinition mesh = new MeshDefinition();
        PartDefinition root = mesh.getRoot();
        PartDefinition d_bipedBody = root.addOrReplaceChild("bipedbody", CubeListBuilder.create().texOffs(32, 8).addBox(-3F, -1F, -2F, 6F, 9F, 4F),
                PartPose.offsetAndRotation(0F, 3F, 0F, 0F, 0F, 0F));
        PartDefinition d_bipedRightArm = d_bipedBody.addOrReplaceChild("bipedrightarm", CubeListBuilder.create().texOffs(48, 0).addBox(-1F, 0F, -1F, 4F, 7F, 2F),
                PartPose.offsetAndRotation(-3F, 3F, 0F, 0F, 0F, 0F));
        PartDefinition d_handRight = d_bipedRightArm.addOrReplaceChild("handright", CubeListBuilder.create().texOffs(52, 9).addBox(-1F, 1F, -1F, 2F, 1F, 2F),
                PartPose.offsetAndRotation(-0F, 6F, 0F, 0F, 0F, 0F));
        PartDefinition d_bipedLeftArm = d_bipedBody.addOrReplaceChild("bipedleftarm", CubeListBuilder.create().texOffs(48, 0).addBox(-3F, 0F, -1F, 4F, 7F, 2F),
                PartPose.offsetAndRotation(3F, 3F, 0F, 0F, 0F, 0F));
        PartDefinition d_handLeft = d_bipedLeftArm.addOrReplaceChild("handleft", CubeListBuilder.create().texOffs(52, 9).addBox(-1F, 1F, -1F, 2F, 1F, 2F),
                PartPose.offsetAndRotation(0F, 6F, 0F, 0F, 0F, 0F));
        PartDefinition d_bipedRightLeg = d_bipedBody.addOrReplaceChild("bipedrightleg", CubeListBuilder.create().texOffs(50, 18).addBox(-1F, 0F, -2F, 3F, 12F, 4F),
                PartPose.offsetAndRotation(-2F, 12F, 0F, 0F, 0F, 0F));
        PartDefinition d_bipedLeftLeg = d_bipedBody.addOrReplaceChild("bipedleftleg", CubeListBuilder.create().texOffs(50, 18).addBox(-2F, 0F, -2F, 3F, 12F, 4F),
                PartPose.offsetAndRotation(2F, 12F, 0F, 0F, 0F, 0F));
        PartDefinition d_skirtTop = d_bipedBody.addOrReplaceChild("skirttop", CubeListBuilder.create().texOffs(0, 16).addBox(-4F, 0F, -4F, 8F, 4F, 8F),
                PartPose.offsetAndRotation(0F, 9F, 0F, 0F, 0F, 0F));
        PartDefinition d_skirtBottom = d_skirtTop.addOrReplaceChild("skirtbottom", CubeListBuilder.create().texOffs(16, 33).addBox(-5F, 0F, -5F, 10F, 7F, 10F),
                PartPose.offsetAndRotation(0F, 13F, 0F, 0F, 0F, 0F));
        PartDefinition d_bipedHead = d_bipedBody.addOrReplaceChild("bipedhead", CubeListBuilder.create().texOffs(0, 0).addBox(-4F, -8F, -4F, 8F, 8F, 8F),
                PartPose.offsetAndRotation(0F, 3F, 0F, 0F, 0F, 0F));
        PartDefinition d_longHair = d_bipedHead.addOrReplaceChild("longhair", CubeListBuilder.create().texOffs(0, 50).addBox(-4F, -2F, -3F, 8F, 9F, 3F),
                PartPose.offsetAndRotation(0F, 0F, 4F, 0.2094395F, 0F, 0F));
        PartDefinition d_braidLeft = d_bipedHead.addOrReplaceChild("braidleft", CubeListBuilder.create().texOffs(0, 32).addBox(0F, -3F, -2F, 1F, 6F, 1F),
                PartPose.offsetAndRotation(3F, 0F, -3F, -0.2443461F, 0F, 0F));
        PartDefinition d_braidRight = d_bipedHead.addOrReplaceChild("braidright", CubeListBuilder.create().texOffs(0, 32).addBox(-1F, -3F, -2F, 1F, 6F, 1F),
                PartPose.offsetAndRotation(-3F, 0F, -3F, -0.2443461F, 0F, 0F));
        PartDefinition d_leftRibbon = d_bipedHead.addOrReplaceChild("leftribbon", CubeListBuilder.create().texOffs(32, 56).addBox(1F, -6F, 1F, 8F, 7F, 1F),
                PartPose.offsetAndRotation(0F, -3F, 4F, 0.4461433F, 0F, -0.4089647F));
        PartDefinition d_rightRibbon = d_bipedHead.addOrReplaceChild("rightribbon", CubeListBuilder.create().texOffs(32, 56).addBox(1F, -6F, -2F, 8F, 7F, 1F),
                PartPose.offsetAndRotation(0F, -3F, 4F, -0.4461411F, 3.141593F, -0.4089647F + (float)Math.PI / 4.0F));
        PartDefinition d_rightRibbon2 = d_bipedHead.addOrReplaceChild("rightribbon2", CubeListBuilder.create().texOffs(32, 56).addBox(-1F, -5F, -1F, 8F, 3F, 1F),
                PartPose.offsetAndRotation(0F, -3F, 5F, -0.260248F, 3.141593F, -0.7063936F));
        PartDefinition d_leftRibbon2 = d_bipedHead.addOrReplaceChild("leftribbon2", CubeListBuilder.create().texOffs(32, 56).addBox(-1F, -5F, 0F, 8F, 3F, 1F),
                PartPose.offsetAndRotation(0F, -3F, 5F, 0.260246F, 0F, 0.7063936F));
        return LayerDefinition.create(mesh, 64, 64);
    }

    /** The parts X1's render() draws, in its order. */
    private ModelPart[] drawn() {
        return new ModelPart[] {bipedBody};
    }

    @Override
    public void setupAnim(ReimuEntity e, float movement, float far, float tick, float yaw, float pitch) {
        // setDefaultPause (bodyHeight 9)
        bipedHead.setPos(0.0F, 5.0F, 0.0F);
        bipedBody.setPos(0.0F, -5.0F, 0.0F);
        bipedRightArm.setPos(-3.0F, 6.0F, 0.0F);
        bipedLeftArm.setPos(3.0F, 6.0F, 0.0F);
        bipedRightLeg.setPos(-2.0F, 9F + 5F, 0.0F);
        bipedLeftLeg.setPos(2.0F, 9F + 5F, 0.0F);
        bipedBody.y = 5F;
        bipedRightLeg.x = -2.0F;
        bipedLeftLeg.x = 2.0F;
        bipedHead.y = -1.0F;
        bipedHead.yRot = yaw / 57.29578F;
        bipedHead.xRot = pitch / 57.29578F;
        bipedRightArm.xRot = Mth.cos(movement * 0.6662F + 3.141593F) * 2.0F * far * 0.5F;
        bipedLeftArm.xRot = Mth.cos(movement * 0.6662F) * 2.0F * far * 0.5F;
        bipedRightArm.zRot = 30F / 180F * 3.141593F;
        bipedLeftArm.zRot = -30F / 180F * 3.141593F;
        this.skirtTop.xRot = 0.0F;
        this.skirtBottom.z = 0.0F;
        this.skirtBottom.xRot = 0.0F;
        this.bipedLeftArm.y = -1F;
        this.bipedRightArm.y = -1F;
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
            this.bipedRightLeg.y = 7.0F;
            this.bipedLeftLeg.y = 7.0F;
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
