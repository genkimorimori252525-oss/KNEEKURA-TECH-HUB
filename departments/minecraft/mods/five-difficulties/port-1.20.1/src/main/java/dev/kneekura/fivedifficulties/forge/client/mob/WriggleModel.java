package dev.kneekura.fivedifficulties.forge.client.mob;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import dev.kneekura.fivedifficulties.forge.entity.mob.WriggleEntity;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.util.Mth;

/**
 * Port of X1 {@code ModelWriggle}, the only {@code ModelTouhouDefault} model: a part tree rooted at the body
 * (head, arms, legs; braids, long hair and antennae on the head; a three-part cloak; trousers on the legs).
 * {@code setDefaultPause} resets the body / head / arm / leg pivots every frame from shoulder 2.4, body 7,
 * legs 12. X1 sets {@code mirror} after {@code addBox}, so nothing is mirrored.
 */
public class WriggleModel extends EntityModel<WriggleEntity> {
    private static final float PI = 3.141593F;
    private static final float SHOULDER = 2.4F, BODY_HEIGHT = 7F, LEG_HEIGHT = 12F;
    private final ModelPart body, head, rightArm, leftArm, rightLeg, leftLeg, manto1, manto2, manto3;

    public WriggleModel(ModelPart root) {
        this.body = root.getChild("body");
        this.head = body.getChild("head");
        this.rightArm = body.getChild("right_arm");
        this.leftArm = body.getChild("left_arm");
        this.rightLeg = body.getChild("right_leg");
        this.leftLeg = body.getChild("left_leg");
        this.manto1 = body.getChild("manto1");
        this.manto2 = manto1.getChild("manto2");
        this.manto3 = manto2.getChild("manto3");
    }

    private static CubeListBuilder box(int u, int v, float x, float y, float z, float w, float h, float d) {
        return CubeListBuilder.create().texOffs(u, v).addBox(x, y, z, w, h, d);
    }

    public static LayerDefinition createBodyLayer() {
        MeshDefinition mesh = new MeshDefinition();
        PartDefinition root = mesh.getRoot();
        PartDefinition body = root.addOrReplaceChild("body", box(32, 8, -3F, 0F, -2F, 6, 7, 4), PartPose.offset(0F, 5F, 0F));
        PartDefinition head = body.addOrReplaceChild("head", box(0, 0, -4F, -8F, -4F, 8, 8, 8), PartPose.offset(0F, 5F, 0F));
        body.addOrReplaceChild("right_arm", box(56, 0, -2F, -1F, -1F, 2, 8, 2), PartPose.offset(-2F, 6F, 0F));
        body.addOrReplaceChild("left_arm", box(56, 0, 0F, -1F, -1F, 2, 8, 2), PartPose.offset(2F, 6F, 0F));
        PartDefinition rightLeg = body.addOrReplaceChild("right_leg", box(32, 19, -1F, 0F, -2F, 3, 11, 4), PartPose.offset(-2F, 13F, 0F));
        PartDefinition leftLeg = body.addOrReplaceChild("left_leg", box(32, 19, -2F, 0F, -2F, 3, 11, 4), PartPose.offset(2F, 13F, 0F));
        // defaultAddChildSetting order: braids, long hair on the head; then Wriggle's antennae, cloak, trousers.
        head.addOrReplaceChild("right_braid", box(0, 16, -1F, 0F, -1F, 1, 4, 1),
                PartPose.offsetAndRotation(-2.95F, -3F, -3F, -0.2443461F, 0F, 0F));
        head.addOrReplaceChild("left_braid", box(0, 16, 0F, 0F, -1F, 1, 4, 1),
                PartPose.offsetAndRotation(2.95F, -3F, -3F, -0.2443461F, 0F, 0F));
        head.addOrReplaceChild("long_hair", box(24, 0, -4F, 0F, -3F, 8, 2, 3), PartPose.offset(0F, 0F, 4F));
        head.addOrReplaceChild("right_touch", box(4, 16, 0F, -6F, 0F, 1, 6, 1), PartPose.offset(-3F, -8F, -4F));
        head.addOrReplaceChild("left_touch", box(4, 16, -1F, -6F, 0F, 1, 6, 1), PartPose.offset(3F, -8F, -4F));
        PartDefinition m1 = body.addOrReplaceChild("manto1", box(38, 47, -6F, 0F, -1F, 12, 6, 1), PartPose.offset(0F, 0F, 2F));
        PartDefinition m2 = m1.addOrReplaceChild("manto2", box(38, 54, -6F, 0F, -1F, 12, 4, 1), PartPose.offset(0F, 6F, 0F));
        m2.addOrReplaceChild("manto3", box(38, 59, -6F, 0F, -1F, 12, 4, 1), PartPose.offset(0F, 4F, 0F));
        rightLeg.addOrReplaceChild("right_zubon", box(0, 32, -2F, 0F, -2.5F, 4, 6, 5), PartPose.offset(0F, -2.5F, 0F));
        leftLeg.addOrReplaceChild("left_zubon", box(0, 32, -2F, 0F, -2.5F, 4, 6, 5), PartPose.offset(0F, -2.5F, 0F));
        return LayerDefinition.create(mesh, 64, 64);
    }

    private static float rad(float degree) {
        return degree / 180F * PI;
    }

    @Override
    public void setupAnim(WriggleEntity e, float movement, float far, float tick, float yaw, float pitch) {
        // setDefaultPause
        head.setPos(0F, 0F, 0F);
        body.setPos(0F, -(BODY_HEIGHT + LEG_HEIGHT - 25F), 0F);
        rightArm.setPos(-SHOULDER, 2F, 0F);
        leftArm.setPos(SHOULDER, 2F, 0F);
        rightLeg.setPos(-2F, BODY_HEIGHT, 0F);
        leftLeg.setPos(2F, BODY_HEIGHT, 0F);
        // ModelTouhouDefault.setRotationAnglesTHKaguya
        body.xRot = 0F;
        head.yRot = yaw / 57.29578F;
        head.xRot = pitch / 57.29578F;
        rightArm.xRot = Mth.cos(movement * 0.6662F + PI) * 2.0F * far * 0.5F;
        rightArm.yRot = rad(90F);
        leftArm.xRot = Mth.cos(movement * 0.6662F) * 2.0F * far * 0.5F;
        leftArm.yRot = rad(90F);
        rightLeg.xRot = Mth.cos(movement * 0.6662F) * 0.5F * far;
        leftLeg.xRot = Mth.cos(movement * 0.6662F + PI) * 0.5F * far;
        rightLeg.yRot = leftLeg.yRot = rightLeg.zRot = leftLeg.zRot = 0F;
        if (this.riding) {
            body.y = -1F;
            rightArm.xRot += -rad(36F);
            leftArm.xRot += -rad(36F);
            rightLeg.xRot = -rad(72F);
            leftLeg.xRot = -rad(72F);
            rightLeg.yRot = rad(13F);
            leftLeg.yRot = -rad(13F);
            rightLeg.zRot = rad(13F);
            leftLeg.zRot = -rad(13F);
        }
        rightArm.yRot = leftArm.yRot = 0F;
        // ModelWriggle.setRotationAnglesTHKaguya
        manto1.xRot = (float) Math.sin((double) (movement + tick) / 10.0D) * 0.1F + 0.3F;
        manto2.xRot = (float) Math.sin((double) (movement * 1.2F + tick) / 7.8D) * 0.25F + 0.25F;
        manto3.xRot = (float) Math.sin((double) (movement * 1.5F + tick) / 5.3D) * 0.3F + 0.20F;
        if (!this.riding) {
            if (e.getFlyingHeight() == 0) {
                rightLeg.xRot = Mth.cos(movement) * 0.7F * far;
                leftLeg.xRot = Mth.cos(movement + PI) * 0.7F * far;
                rightLeg.zRot = 0F;
                leftLeg.zRot = 0F;
                if (movement > 0F) {
                    rightArm.xRot = Mth.cos(movement + PI) * 2.0F * far * 0.5F;
                    leftArm.xRot = Mth.cos(movement) * 2.0F * far * 0.5F;
                    rightArm.yRot = rad(-10F);
                    rightArm.zRot = rad(20F);
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
                rightArm.xRot = rad(0F);
                rightArm.zRot = rad(20F + Mth.sin(tick / 10F) * 5F);
                leftArm.xRot = rad(0F);
                leftArm.zRot = rad(-20F - Mth.sin(tick / 10F) * 5F);
            }
        }
        // setRotationAnglesAfterTHKaguya: the spell-card declaration swing.
        if (e.getSpellCardMotion() < -15) {
            rightArm.xRot = -0.7F - Mth.sin(tick / 10F) * 0.1F - Mth.sin(rad(30F + e.getSpellCardMotion())) * 4F;
        } else if (e.getSpellCardMotion() < 0) {
            rightArm.xRot = -0.7F - Mth.sin(tick / 10F) * 0.1F - Mth.sin(rad(-e.getSpellCardMotion())) * 4F;
        }
    }

    @Override
    public void renderToBuffer(PoseStack pose, VertexConsumer consumer, int light, int overlay, float r, float g, float b, float a) {
        body.render(pose, consumer, light, overlay, r, g, b, a);
    }
}
