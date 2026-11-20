package dev.kneekura.fivedifficulties.forge.client.mob;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import dev.kneekura.fivedifficulties.forge.entity.mob.MikoEntity;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeDeformation;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.util.Mth;

/** Port of X1 {@code ModelMiko}: boxes generated from the X1 constructor; animation ported by hand. */
public class MikoModel extends EntityModel<MikoEntity> {
    // ---- generated from ModelMiko.java ----
    private final ModelPart bipedBody;
    private final ModelPart bipedRightArm;
    private final ModelPart bipedLeftArm;
    private final ModelPart bipedRightLeg;
    private final ModelPart bipedLeftLeg;
    private final ModelPart skirtTop;
    private final ModelPart skirtBottom;
    private final ModelPart cape;
    private final ModelPart Manto1;
    private final ModelPart Manto2;
    private final ModelPart Manto3;
    private final ModelPart Manto4;
    private final ModelPart bipedHead;
    private final ModelPart longHair;
    private final ModelPart leftBraid;
    private final ModelPart rightBraid;
    private final ModelPart MimiateRight;
    private final ModelPart MimiateLeft;
    private final ModelPart HearLeft1;
    private final ModelPart HearLeft2;
    private final ModelPart HearRight1;
    private final ModelPart HearRight2;

    public MikoModel(ModelPart root) {
        this.bipedBody = root.getChild("bipedbody");
        this.bipedRightArm = root.getChild("bipedbody").getChild("bipedrightarm");
        this.bipedLeftArm = root.getChild("bipedbody").getChild("bipedleftarm");
        this.bipedRightLeg = root.getChild("bipedbody").getChild("bipedrightleg");
        this.bipedLeftLeg = root.getChild("bipedbody").getChild("bipedleftleg");
        this.skirtTop = root.getChild("bipedbody").getChild("skirttop");
        this.skirtBottom = root.getChild("bipedbody").getChild("skirttop").getChild("skirtbottom");
        this.cape = root.getChild("bipedbody").getChild("cape");
        this.Manto1 = root.getChild("bipedbody").getChild("manto1");
        this.Manto2 = root.getChild("bipedbody").getChild("manto1").getChild("manto2");
        this.Manto3 = root.getChild("bipedbody").getChild("manto1").getChild("manto2").getChild("manto3");
        this.Manto4 = root.getChild("bipedbody").getChild("manto1").getChild("manto2").getChild("manto3").getChild("manto4");
        this.bipedHead = root.getChild("bipedbody").getChild("bipedhead");
        this.longHair = root.getChild("bipedbody").getChild("bipedhead").getChild("longhair");
        this.leftBraid = root.getChild("bipedbody").getChild("bipedhead").getChild("leftbraid");
        this.rightBraid = root.getChild("bipedbody").getChild("bipedhead").getChild("rightbraid");
        this.MimiateRight = root.getChild("bipedbody").getChild("bipedhead").getChild("mimiateright");
        this.MimiateLeft = root.getChild("bipedbody").getChild("bipedhead").getChild("mimiateleft");
        this.HearLeft1 = root.getChild("bipedbody").getChild("bipedhead").getChild("hearleft1");
        this.HearLeft2 = root.getChild("bipedbody").getChild("bipedhead").getChild("hearleft1").getChild("hearleft2");
        this.HearRight1 = root.getChild("bipedbody").getChild("bipedhead").getChild("hearright1");
        this.HearRight2 = root.getChild("bipedbody").getChild("bipedhead").getChild("hearright1").getChild("hearright2");
    }

    public static LayerDefinition createBodyLayer() {
        MeshDefinition mesh = new MeshDefinition();
        PartDefinition root = mesh.getRoot();
        PartDefinition d_bipedBody = root.addOrReplaceChild("bipedbody", CubeListBuilder.create().texOffs(32, 8).addBox(-3F, 0F, -2F, 6F, 9F, 4F),
                PartPose.offsetAndRotation(0F, 3F, 0F, 0F, 0F, 0F));
        PartDefinition d_bipedRightArm = d_bipedBody.addOrReplaceChild("bipedrightarm", CubeListBuilder.create().texOffs(56, 0).addBox(-0.8F, -1F, -1F, 2F, 8F, 2F),
                PartPose.offsetAndRotation(-4F, 4F, 0F, 0F, 0F, 0F));
        PartDefinition d_bipedLeftArm = d_bipedBody.addOrReplaceChild("bipedleftarm", CubeListBuilder.create().texOffs(56, 0).addBox(-1.2F, -1F, -1F, 2F, 8F, 2F),
                PartPose.offsetAndRotation(4F, 4F, 0F, 0F, 0F, 0F));
        PartDefinition d_bipedRightLeg = d_bipedBody.addOrReplaceChild("bipedrightleg", CubeListBuilder.create().texOffs(50, 18).addBox(-1F, 0F, -2F, 3F, 12F, 4F),
                PartPose.offsetAndRotation(-2F, 9F, 0F, 0F, 0F, 0F));
        PartDefinition d_bipedLeftLeg = d_bipedBody.addOrReplaceChild("bipedleftleg", CubeListBuilder.create().texOffs(50, 18).addBox(-2F, 0F, -2F, 3F, 12F, 4F),
                PartPose.offsetAndRotation(2F, 0F, 0F, 0F, 0F, 0F));
        PartDefinition d_skirtTop = d_bipedBody.addOrReplaceChild("skirttop", CubeListBuilder.create().texOffs(0, 16).addBox(-4F, 0F, -6F, 8F, 4F, 8F),
                PartPose.offsetAndRotation(0F, 6F, 2F, 0F, 0F, 0F));
        PartDefinition d_skirtBottom = d_skirtTop.addOrReplaceChild("skirtbottom", CubeListBuilder.create().texOffs(16, 31).addBox(-5F, 0F, -10F, 10F, 8F, 10F),
                PartPose.offsetAndRotation(0F, 4F, 3F, 0F, 0F, 0F));
        PartDefinition d_cape = d_bipedBody.addOrReplaceChild("cape", CubeListBuilder.create().texOffs(30, 54).addBox(-5F, -4F, -2.5F, 10F, 3F, 7F),
                PartPose.offsetAndRotation(0F, 2F, 0F, 0F, 0F, 0F));
        PartDefinition d_Manto1 = d_bipedBody.addOrReplaceChild("manto1", CubeListBuilder.create().texOffs(0, 49).addBox(-5.5F, 0F, -1F, 11F, 3F, 1F),
                PartPose.offsetAndRotation(0F, 0F, 3F, 0F, 0F, 0F));
        PartDefinition d_Manto2 = d_Manto1.addOrReplaceChild("manto2", CubeListBuilder.create().texOffs(0, 53).addBox(-6.0F, 0F, -1F, 12F, 4F, 1F),
                PartPose.offsetAndRotation(0F, 3F, 0F, 0F, 0F, 0F));
        PartDefinition d_Manto3 = d_Manto2.addOrReplaceChild("manto3", CubeListBuilder.create().texOffs(0, 58).addBox(-6.5F, 0F, -1F, 13F, 5F, 1F),
                PartPose.offsetAndRotation(0F, 4F, 0F, 0F, 0F, 0F));
        PartDefinition d_Manto4 = d_Manto3.addOrReplaceChild("manto4", CubeListBuilder.create().texOffs(0, 58).addBox(-6.5F, 0F, -1F, 13F, 5F, 1F),
                PartPose.offsetAndRotation(0F, 5F, 0F, 0F, 0F, 0F));
        PartDefinition d_bipedHead = d_bipedBody.addOrReplaceChild("bipedhead", CubeListBuilder.create().texOffs(0, 0).addBox(-4F, -8F, -4F, 8F, 8F, 8F),
                PartPose.offsetAndRotation(0F, 3F, 0F, 0F, 0F, 0F));
        PartDefinition d_longHair = d_bipedHead.addOrReplaceChild("longhair", CubeListBuilder.create().texOffs(0, 28).addBox(-4F, -2F, -3F, 8F, 3F, 3F),
                PartPose.offsetAndRotation(0F, 0F, 4F, 0.2094395F, 0F, 0F));
        PartDefinition d_leftBraid = d_bipedHead.addOrReplaceChild("leftbraid", CubeListBuilder.create().texOffs(0, 16).addBox(0F, -3F, -1F, 1F, 4F, 1F),
                PartPose.offsetAndRotation(3F, 0F, -3F, -0.2443461F, 0F, 0F));
        PartDefinition d_rightBraid = d_bipedHead.addOrReplaceChild("rightbraid", CubeListBuilder.create().texOffs(0, 16).addBox(-1F, -3F, -1F, 1F, 4F, 1F),
                PartPose.offsetAndRotation(-3F, 0F, -3F, -0.2443461F, 0F, 0F));
        PartDefinition d_MimiateRight = d_bipedHead.addOrReplaceChild("mimiateright", CubeListBuilder.create().texOffs(0, 41).addBox(-2F, -5F, -1F, 4F, 4F, 1F),
                PartPose.offsetAndRotation(-4F, -1F, 0F, 0F, 1.570796F, 0F));
        PartDefinition d_MimiateLeft = d_bipedHead.addOrReplaceChild("mimiateleft", CubeListBuilder.create().texOffs(0, 41).addBox(-2F, -5F, -1F, 4F, 4F, 1F),
                PartPose.offsetAndRotation(4F, -1F, 0F, 0F, -1.570796F, 0F));
        PartDefinition d_HearLeft1 = d_bipedHead.addOrReplaceChild("hearleft1", CubeListBuilder.create().texOffs(24, 0).addBox(0F, -5F, -2F, 4F, 2F, 4F),
                PartPose.offsetAndRotation(0F, -5F, 0F, 0F, 0F, 0.1745329F));
        PartDefinition d_HearLeft2 = d_HearLeft1.addOrReplaceChild("hearleft2", CubeListBuilder.create().texOffs(38, 1).addBox(0F, -1F, -1.5F, 3F, 3F, 3F),
                PartPose.offsetAndRotation(1F, -7F, 0F, 0F, 0F, 0.1745329F));
        PartDefinition d_HearRight1 = d_bipedHead.addOrReplaceChild("hearright1", CubeListBuilder.create().texOffs(24, 0).addBox(-4F, -5F, -2F, 4F, 2F, 4F),
                PartPose.offsetAndRotation(0F, -5F, 0F, 0F, 0F, -0.1745329F));
        PartDefinition d_HearRight2 = d_HearRight1.addOrReplaceChild("hearright2", CubeListBuilder.create().texOffs(38, 1).addBox(-3F, -1F, -1.5F, 3F, 3F, 3F),
                PartPose.offsetAndRotation(-1F, -7F, 0F, 0F, 0F, -0.1745329F));
        return LayerDefinition.create(mesh, 64, 64);
    }

    /** The parts X1's render() draws, in its order. */
    private ModelPart[] drawn() {
        return new ModelPart[] {bipedBody};
    }

    @Override
    public void setupAnim(MikoEntity e, float movement, float far, float tick, float yaw, float pitch) {
        // setDefaultPause (bodyHeight 9)
        bipedHead.setPos(0.0F, 0.0F, 0.0F);
        bipedBody.setPos(0.0F, 3.0F, 0.0F);
        bipedRightArm.setPos(-3.0F, 1.0F, 0.0F);
        bipedLeftArm.setPos(3.0F, 1.0F, 0.0F);
        bipedRightLeg.setPos(-2.0F, 9F, 0.0F);
        bipedLeftLeg.setPos(2.0F, 9F, 0.0F);
        this.bipedBody.xRot = 0.0F;
        this.bipedHead.yRot = yaw / 57.29578F;
        this.bipedHead.xRot = pitch / 57.29578F;
        this.bipedRightArm.xRot = Mth.cos(movement * 0.6662F + 3.141593F) * 2.0F * far * 0.5F;
        this.bipedRightArm.yRot = 90F / 180F * 3.141593F;
        this.bipedLeftArm.xRot = Mth.cos(movement * 0.6662F) * 2.0F * far * 0.5F;
        this.bipedLeftArm.yRot = 90F / 180F * 3.141593F;
        this.bipedRightArm.zRot = 20F / 180F * 3.141593F;
        this.bipedLeftArm.zRot = -20F / 180F * 3.141593F;
        this.bipedRightLeg.xRot = Mth.cos(movement * 0.6662F) * 0.5F * far;
        this.bipedLeftLeg.xRot = Mth.cos(movement * 0.6662F + (float) Math.PI) * 0.5F * far;
        this.bipedRightLeg.yRot = bipedLeftLeg.yRot = bipedRightLeg.zRot = bipedLeftLeg.zRot = 0.0F;
        this.skirtTop.xRot = 0.0F;
        this.skirtBottom.xRot = 0.0F;
        this.Manto1.xRot = (float) Math.sin((double) (movement + tick) / 10.0D) * 0.1F + 0.3F;
        this.Manto2.xRot = (float) Math.sin((double) (movement * 1.2F + tick) / 7.8D) * 0.25F + 0.25F;
        this.Manto3.xRot = (float) Math.sin((double) (movement * 1.5F + tick) / 5.3D) * 0.3F + 0.20F;
        this.Manto4.xRot = (float) Math.sin((double) (movement * 2.0F + tick) / 4.1D) * 0.34F + 0.0F;
        if (e.isPassenger()) {
            bipedBody.y = -1.0F;
            this.bipedRightArm.xRot += -((float) Math.PI / 5F);
            this.bipedLeftArm.xRot += -((float) Math.PI / 5F);
            this.bipedRightLeg.xRot = -((float) Math.PI * 2F / 5F);
            this.bipedLeftLeg.xRot = -((float) Math.PI * 2F / 5F);
            this.bipedRightLeg.yRot = ((float) Math.PI / 14F);
            this.bipedLeftLeg.yRot = -((float) Math.PI / 14F);
            this.bipedRightLeg.zRot = ((float) Math.PI / 14F);
            this.bipedLeftLeg.zRot = -((float) Math.PI / 14F);
            this.skirtTop.xRot = -(20F / 180F * (float) Math.PI);
            this.skirtBottom.xRot = -(30F / 180F * (float) Math.PI);
        }
        bipedRightArm.yRot = bipedLeftArm.yRot = 0.0F;

    }

    @Override
    public void renderToBuffer(PoseStack pose, VertexConsumer consumer, int light, int overlay, float r, float g, float b, float a) {
        for (ModelPart p : drawn()) p.render(pose, consumer, light, overlay, r, g, b, a);
    }
}
