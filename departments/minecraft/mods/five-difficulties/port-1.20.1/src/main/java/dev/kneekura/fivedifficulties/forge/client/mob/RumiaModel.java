package dev.kneekura.fivedifficulties.forge.client.mob;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import dev.kneekura.fivedifficulties.forge.entity.mob.RumiaEntity;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeDeformation;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.util.Mth;

/** Port of X1 {@code ModelRumia}: boxes generated from the X1 constructor; animation ported by hand. */
public class RumiaModel extends EntityModel<RumiaEntity> {
    // ---- generated from ModelRumia.java ----
    private final ModelPart head;
    private final ModelPart longHair;
    private final ModelPart body;
    private final ModelPart skirt;
    private final ModelPart skirt2;
    private final ModelPart rightArm;
    private final ModelPart leftArm;
    private final ModelPart rightLeg;
    private final ModelPart leftLeg;

    public RumiaModel(ModelPart root) {
        this.head = root.getChild("head");
        this.longHair = root.getChild("head").getChild("longhair");
        this.body = root.getChild("body");
        this.skirt = root.getChild("skirt");
        this.skirt2 = root.getChild("skirt").getChild("skirt2");
        this.rightArm = root.getChild("rightarm");
        this.leftArm = root.getChild("leftarm");
        this.rightLeg = root.getChild("rightleg");
        this.leftLeg = root.getChild("leftleg");
    }

    public static LayerDefinition createBodyLayer() {
        MeshDefinition mesh = new MeshDefinition();
        PartDefinition root = mesh.getRoot();
        PartDefinition d_head = root.addOrReplaceChild("head", CubeListBuilder.create().texOffs(0, 0).addBox(-4F, -3F, -4F, 8F, 8F, 8F),
                PartPose.offsetAndRotation(0F, 0F, 0F, 0F, 0F, 0F));
        PartDefinition d_longHair = d_head.addOrReplaceChild("longhair", CubeListBuilder.create().texOffs(24, 0).addBox(-4F, 4F, -3F, 8F, 5F, 3F),
                PartPose.offsetAndRotation(0F, 0F, 4F, 0F, 0F, 0F));
        PartDefinition d_body = root.addOrReplaceChild("body", CubeListBuilder.create().texOffs(32, 8).addBox(-3F, 5F, -2F, 6F, 7F, 4F),
                PartPose.offsetAndRotation(0F, 0F, 0F, 0F, 0F, 0F));
        PartDefinition d_skirt = root.addOrReplaceChild("skirt", CubeListBuilder.create().texOffs(0, 16).addBox(-4F, 0F, -4F, 8F, 5F, 8F),
                PartPose.offsetAndRotation(0F, 10F, 0F, 0F, 0F, 0F));
        PartDefinition d_skirt2 = d_skirt.addOrReplaceChild("skirt2", CubeListBuilder.create().texOffs(24, 32).addBox(-5F, -5F, -5F, 10F, 6F, 10F),
                PartPose.offsetAndRotation(0F, 9F, 0F, 0F, 0F, 0F));
        PartDefinition d_rightArm = root.addOrReplaceChild("rightarm", CubeListBuilder.create().texOffs(48, 0).addBox(-1F, -1F, -1F, 2F, 8F, 2F),
                PartPose.offsetAndRotation(-4F, 6F, 0F, 0F, 0F, 0F));
        PartDefinition d_leftArm = root.addOrReplaceChild("leftarm", CubeListBuilder.create().texOffs(56, 0).addBox(-1F, -1F, -1F, 2F, 8F, 2F),
                PartPose.offsetAndRotation(4F, 6F, 0F, 0F, 0F, 0F));
        PartDefinition d_rightLeg = root.addOrReplaceChild("rightleg", CubeListBuilder.create().texOffs(50, 16).addBox(-1F, 0F, -2F, 3F, 12F, 4F),
                PartPose.offsetAndRotation(-2F, 12F, 0F, 0F, 0F, 0F));
        PartDefinition d_leftLeg = root.addOrReplaceChild("leftleg", CubeListBuilder.create().texOffs(50, 16).addBox(-2F, 0F, -2F, 3F, 12F, 4F),
                PartPose.offsetAndRotation(2F, 12F, 0F, 0F, 0F, 0F));
        return LayerDefinition.create(mesh, 64, 64);
    }

    /** The parts X1's render() draws, in its order. */
    private ModelPart[] drawn() {
        return new ModelPart[] {head, body, skirt, rightArm, rightLeg, leftArm, leftLeg};
    }

    @Override
    public void setupAnim(RumiaEntity e, float movement, float far, float tick, float yaw, float pitch) {
        this.head.yRot = yaw / (180F / (float) Math.PI);
        this.head.xRot = pitch / (180F / (float) Math.PI);
        this.body.yRot = Mth.sin(Mth.sqrt(this.attackTime) * (float) Math.PI * 2.0F) * 0.2F;
        this.skirt.xRot = 0F;
        if (e.getSpellCardMotion() < -15) {
            rightArm.xRot = -0.7F - Mth.sin(tick / 10F) * 0.1F - Mth.sin((float) (30F + e.getSpellCardMotion()) / 180F * 3.141593F) * 4F;
        } else if (e.getSpellCardMotion() < 0) {
            rightArm.xRot = -0.7F - Mth.sin(tick / 10F) * 0.1F - Mth.sin((float) (-e.getSpellCardMotion()) / 180F * 3.141593F) * 4F;
        } else {
            rightArm.zRot = 90F / 180F * (float) Math.PI;
            leftArm.zRot = -rightArm.zRot;
        }
        if (this.riding) {
            this.rightArm.xRot = -((float) Math.PI / 5F);
            this.leftArm.xRot = -((float) Math.PI / 5F);
            this.rightLeg.xRot = -((float) Math.PI * 2F / 5F);
            this.leftLeg.xRot = -((float) Math.PI * 2F / 5F);
            this.rightLeg.yRot = ((float) Math.PI / 14F);
            this.leftLeg.yRot = -((float) Math.PI / 14F);
            this.rightLeg.zRot = ((float) Math.PI / 14F);
            this.leftLeg.zRot = -((float) Math.PI / 14F);
            this.skirt.xRot += -((float) Math.PI / 5F);
        } else if (e.getFlyingHeight() == 0) {
            rightLeg.xRot = Mth.cos(movement) * 0.7F * far;
            leftLeg.xRot = Mth.cos(movement + (float) Math.PI) * 0.7F * far;
            rightLeg.zRot = 0F;
            leftLeg.zRot = 0F;
            if (movement > 0F) {
                this.rightArm.xRot = Mth.cos(movement + (float) Math.PI) * 2.0F * far * 0.5F;
                this.leftArm.xRot = Mth.cos(movement) * 2.0F * far * 0.5F;
                rightArm.yRot = -10F / 180F * (float) Math.PI;
                rightArm.zRot = 20F / 180F * (float) Math.PI;
                leftArm.yRot = -rightArm.yRot;
                leftArm.zRot = -rightArm.zRot;
            } else {
                rightArm.xRot = -0.7F - Mth.sin(tick / 10F) * 0.1F;
                rightArm.yRot = 0.0F;
                rightArm.zRot = -0.6457718F;
                leftArm.xRot = rightArm.xRot;
                leftArm.yRot = 0.0F;
                leftArm.zRot = 0.6457718F;
            }
        } else {
            rightLeg.zRot = Math.abs(Mth.sin(tick / 10F) * 0.1F);
            leftLeg.zRot = -rightLeg.zRot;
            rightLeg.xRot = Math.abs(Mth.sin(tick / 10F) * 0.2F);
            leftLeg.xRot = rightLeg.zRot;
            rightArm.zRot = 90F / 180F * (float) Math.PI;
            rightArm.yRot = 0.0F;
            rightArm.xRot = 0.0F;
            leftArm.zRot = -rightArm.zRot;
            leftArm.yRot = 0.0F;
            leftArm.xRot = 0.0F;
        }

    }

    @Override
    public void renderToBuffer(PoseStack pose, VertexConsumer consumer, int light, int overlay, float r, float g, float b, float a) {
        for (ModelPart p : drawn()) p.render(pose, consumer, light, overlay, r, g, b, a);
    }
}
