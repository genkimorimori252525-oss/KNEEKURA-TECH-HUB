package dev.kneekura.fivedifficulties.forge.client.mob;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import dev.kneekura.fivedifficulties.forge.entity.mob.TozikoEntity;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeDeformation;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.util.Mth;

/** Port of X1 {@code ModelToziko}: boxes generated from the X1 constructor; animation ported by hand. */
public class TozikoModel extends EntityModel<TozikoEntity> {
    // ---- generated from ModelToziko.java ----
    private final ModelPart Body;
    private final ModelPart RightArm;
    private final ModelPart LeftArm;
    private final ModelPart Leg1;
    private final ModelPart Leg2;
    private final ModelPart Leg3;
    private final ModelPart SkirtTop;
    private final ModelPart SkirtBottom;
    private final ModelPart HeadBase;
    private final ModelPart BackHair;
    private final ModelPart LeftHair;
    private final ModelPart RightHair;
    private final ModelPart Cup;
    private final ModelPart CupLeft;
    private final ModelPart CupRight;
    private final ModelPart CupRibbon;

    public TozikoModel(ModelPart root) {
        this.Body = root.getChild("body");
        this.RightArm = root.getChild("rightarm");
        this.LeftArm = root.getChild("leftarm");
        this.Leg1 = root.getChild("leg1");
        this.Leg2 = root.getChild("leg2");
        this.Leg3 = root.getChild("leg3");
        this.SkirtTop = root.getChild("skirttop");
        this.SkirtBottom = root.getChild("skirtbottom");
        this.HeadBase = root.getChild("headbase");
        this.BackHair = root.getChild("headbase").getChild("backhair");
        this.LeftHair = root.getChild("headbase").getChild("lefthair");
        this.RightHair = root.getChild("headbase").getChild("righthair");
        this.Cup = root.getChild("headbase").getChild("cup");
        this.CupLeft = root.getChild("headbase").getChild("cup").getChild("cupleft");
        this.CupRight = root.getChild("headbase").getChild("cup").getChild("cupright");
        this.CupRibbon = root.getChild("headbase").getChild("cup").getChild("cupribbon");
    }

    public static LayerDefinition createBodyLayer() {
        MeshDefinition mesh = new MeshDefinition();
        PartDefinition root = mesh.getRoot();
        PartDefinition d_Body = root.addOrReplaceChild("body", CubeListBuilder.create().texOffs(32, 6).addBox(-3F, 0F, -2F, 6F, 9F, 4F),
                PartPose.offsetAndRotation(0F, 2F, 0F, 0F, 0F, 0F));
        PartDefinition d_RightArm = root.addOrReplaceChild("rightarm", CubeListBuilder.create().texOffs(48, 0).addBox(-2F, -1F, -1F, 2F, 8F, 2F),
                PartPose.offsetAndRotation(-3F, 3F, 0F, -1.570796F, 0F, 0F));
        PartDefinition d_LeftArm = root.addOrReplaceChild("leftarm", CubeListBuilder.create().texOffs(48, 0).addBox(0F, -1F, -1F, 2F, 8F, 2F),
                PartPose.offsetAndRotation(3F, 3F, 0F, -1.570796F, 0F, 0F));
        PartDefinition d_Leg1 = root.addOrReplaceChild("leg1", CubeListBuilder.create().texOffs(32, 17).addBox(-4F, 0F, -4F, 8F, 7F, 8F),
                PartPose.offsetAndRotation(0F, 12F, 0F, 0F, 0F, 0F));
        PartDefinition d_Leg2 = root.addOrReplaceChild("leg2", CubeListBuilder.create().texOffs(32, 17).addBox(-3F, 0F, -3F, 6F, 4F, 6F),
                PartPose.offsetAndRotation(0F, 17F, 0F, 0F, 0F, 0F));
        PartDefinition d_Leg3 = root.addOrReplaceChild("leg3", CubeListBuilder.create().texOffs(32, 17).addBox(-2F, 0F, -2F, 4F, 4F, 4F),
                PartPose.offsetAndRotation(0F, 20F, 0F, 0F, 0F, 0F));
        PartDefinition d_SkirtTop = root.addOrReplaceChild("skirttop", CubeListBuilder.create().texOffs(0, 16).addBox(-4F, 0F, -4F, 8F, 4F, 8F),
                PartPose.offsetAndRotation(0F, 8F, 0F, 0F, 0F, 0F));
        PartDefinition d_SkirtBottom = root.addOrReplaceChild("skirtbottom", CubeListBuilder.create().texOffs(16, 32).addBox(-5F, 0F, -5F, 10F, 7F, 10F),
                PartPose.offsetAndRotation(0F, 12F, 0F, 0F, 0F, 0F));
        PartDefinition d_HeadBase = root.addOrReplaceChild("headbase", CubeListBuilder.create().texOffs(0, 0).addBox(-4F, -8F, -4F, 8F, 8F, 8F),
                PartPose.offsetAndRotation(0F, 2F, 0F, 0F, 0F, 0F));
        PartDefinition d_BackHair = d_HeadBase.addOrReplaceChild("backhair", CubeListBuilder.create().texOffs(0, 48).addBox(-4F, -2F, -3F, 8F, 2F, 3F),
                PartPose.offsetAndRotation(0F, 2F, 4F, 0F, 0F, 0F));
        PartDefinition d_LeftHair = d_HeadBase.addOrReplaceChild("lefthair", CubeListBuilder.create().texOffs(11, 56).addBox(-4F, -2F, 0F, 8F, 5F, 1F),
                PartPose.offsetAndRotation(5F, -3F, 0F, 0F, -1.570796F, 0F));
        PartDefinition d_RightHair = d_HeadBase.addOrReplaceChild("righthair", CubeListBuilder.create().texOffs(11, 56).addBox(-4F, -2F, 0F, 8F, 5F, 1F),
                PartPose.offsetAndRotation(-5F, -3F, 0F, 0F, 1.570796F, 0F));
        PartDefinition d_Cup = d_HeadBase.addOrReplaceChild("cup", CubeListBuilder.create().texOffs(0, 32).addBox(-2F, -8F, -2F, 4F, 6F, 4F),
                PartPose.offsetAndRotation(0F, -6F, 0F, 0F, 0F, 0F));
        PartDefinition d_CupLeft = d_Cup.addOrReplaceChild("cupleft", CubeListBuilder.create().texOffs(0, 42).addBox(0F, 4F, 0F, 4F, 1F, 1F),
                PartPose.offsetAndRotation(2F, -7F, 0F, 0F, 0F, 0F));
        PartDefinition d_CupRight = d_Cup.addOrReplaceChild("cupright", CubeListBuilder.create().texOffs(0, 42).addBox(-4F, 4F, 0F, 4F, 1F, 1F),
                PartPose.offsetAndRotation(-2F, -7F, 0F, 0F, 0F, 0F));
        PartDefinition d_CupRibbon = d_Cup.addOrReplaceChild("cupribbon", CubeListBuilder.create().texOffs(0, 44).addBox(-2F, 2F, 0F, 5F, 4F, 1F),
                PartPose.offsetAndRotation(2F, -7F, 1F, 0F, -0.4833219F, -0.5205006F));
        return LayerDefinition.create(mesh, 64, 64);
    }

    /** The parts X1's render() draws, in its order. */
    private ModelPart[] drawn() {
        return new ModelPart[] {Body, RightArm, LeftArm, Leg1, Leg2, Leg3, SkirtTop, SkirtBottom, HeadBase};
    }

    @Override
    public void setupAnim(TozikoEntity e, float movement, float far, float tick, float yaw, float pitch) {
        this.HeadBase.yRot = yaw / (180F / (float) Math.PI);
        this.HeadBase.xRot = pitch / (180F / (float) Math.PI);
        this.Body.yRot = Mth.sin(Mth.sqrt(this.attackTime) * (float) Math.PI * 2.0F) * 0.2F;
        this.SkirtTop.xRot = 0F;
        if (e.getSpellCardMotion() < -15) {
            RightArm.xRot = -0.7F - Mth.sin(tick / 10F) * 0.1F - Mth.sin((float) (30F + e.getSpellCardMotion()) / 180F * 3.141593F) * 4F;
        } else if (e.getSpellCardMotion() < 0) {
            RightArm.xRot = -0.7F - Mth.sin(tick / 10F) * 0.1F - Mth.sin((float) (-e.getSpellCardMotion()) / 180F * 3.141593F) * 4F;
        } else {
            // X1 quirk kept: the left arm copies the right arm's Z, not its Y.
            RightArm.yRot = 90F / 180F * (float) Math.PI;
            LeftArm.yRot = -RightArm.zRot;
        }
        if (this.riding) {
            this.RightArm.xRot = -((float) Math.PI / 5F);
            this.LeftArm.xRot = -((float) Math.PI / 5F);
            this.SkirtTop.xRot += -((float) Math.PI / 5F);
        } else if (e.getFlyingHeight() == 0) {
            if (movement > 0F) {
                this.RightArm.xRot = Mth.cos(movement + (float) Math.PI) * 2.0F * far * 0.5F;
                this.LeftArm.xRot = Mth.cos(movement) * 2.0F * far * 0.5F;
                RightArm.yRot = -90F / 180F * (float) Math.PI;
                RightArm.zRot = 20F / 180F * (float) Math.PI;
                LeftArm.yRot = -RightArm.yRot;
                LeftArm.zRot = -RightArm.zRot;
            } else {
                RightArm.xRot = -0.7F - Mth.sin(tick / 10F) * 0.1F;
                RightArm.yRot = 0.0F;
                RightArm.zRot = -0.6457718F;
                LeftArm.xRot = RightArm.xRot;
                LeftArm.yRot = 0.0F;
                LeftArm.zRot = 0.6457718F;
            }
        } else {
            RightArm.zRot = 0.0F;
            RightArm.yRot = Mth.sin(tick / 13F) * 0.1F;
            RightArm.xRot = -80F / 180F * (float) Math.PI + Mth.sin(tick / 10F) * 0.1F;
            LeftArm.zRot = 0.0F;
            LeftArm.yRot = -RightArm.yRot;
            LeftArm.xRot = RightArm.xRot;
        }

    }

    @Override
    public void renderToBuffer(PoseStack pose, VertexConsumer consumer, int light, int overlay, float r, float g, float b, float a) {
        for (ModelPart p : drawn()) p.render(pose, consumer, light, overlay, r, g, b, a);
    }
}
