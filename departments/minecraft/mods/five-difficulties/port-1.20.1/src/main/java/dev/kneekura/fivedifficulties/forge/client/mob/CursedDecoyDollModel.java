package dev.kneekura.fivedifficulties.forge.client.mob;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import dev.kneekura.fivedifficulties.forge.entity.mob.CursedDecoyDollEntity;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeDeformation;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.util.Mth;

/** Port of X1 {@code ModelCursedDecoyDoll}: boxes generated from the X1 constructor; animation ported by hand. */
public class CursedDecoyDollModel extends EntityModel<CursedDecoyDollEntity> {
    // ---- generated from ModelCursedDecoyDoll.java ----
    private final ModelPart bipedBody;
    private final ModelPart bipedRightArm;
    private final ModelPart bipedLeftArm;
    private final ModelPart bipedRightLeg;
    private final ModelPart bipedLeftLeg;
    private final ModelPart skirtTop;
    private final ModelPart bipedHead;
    private final ModelPart longHair;
    private final ModelPart leftBraid;
    private final ModelPart rightBraid;
    private final ModelPart leftRibbon;
    private final ModelPart rightRibbon;

    public CursedDecoyDollModel(ModelPart root) {
        this.bipedBody = root.getChild("bipedbody");
        this.bipedRightArm = root.getChild("bipedrightarm");
        this.bipedLeftArm = root.getChild("bipedleftarm");
        this.bipedRightLeg = root.getChild("bipedrightleg");
        this.bipedLeftLeg = root.getChild("bipedleftleg");
        this.skirtTop = root.getChild("skirttop");
        this.bipedHead = root.getChild("bipedhead");
        this.longHair = root.getChild("longhair");
        this.leftBraid = root.getChild("leftbraid");
        this.rightBraid = root.getChild("rightbraid");
        this.leftRibbon = root.getChild("leftribbon");
        this.rightRibbon = root.getChild("rightribbon");
    }

    public static LayerDefinition createBodyLayer() {
        MeshDefinition mesh = new MeshDefinition();
        PartDefinition root = mesh.getRoot();
        PartDefinition d_bipedBody = root.addOrReplaceChild("bipedbody", CubeListBuilder.create().texOffs(32, 8).addBox(-3F, 0F, -2F, 6F, 6F, 4F),
                PartPose.offsetAndRotation(0F, 10F, 0F, 0F, 0F, 0F));
        PartDefinition d_bipedRightArm = root.addOrReplaceChild("bipedrightarm", CubeListBuilder.create().texOffs(32, 0).addBox(0F, -1F, -1F, 4F, 6F, 2F),
                PartPose.offsetAndRotation(-4F, 11F, 0F, 0F, 0F, 0.5235988F));
        PartDefinition d_bipedLeftArm = root.addOrReplaceChild("bipedleftarm", CubeListBuilder.create().texOffs(32, 0).addBox(-4F, -1F, -1F, 4F, 6F, 2F),
                PartPose.offsetAndRotation(4F, 11F, 0F, 0F, 0F, -0.5235988F));
        PartDefinition d_bipedRightLeg = root.addOrReplaceChild("bipedrightleg", CubeListBuilder.create().texOffs(36, 22).addBox(-1F, 0F, -2F, 3F, 7F, 4F),
                PartPose.offsetAndRotation(-2F, 17F, 0F, 0F, 0F, 0F));
        PartDefinition d_bipedLeftLeg = root.addOrReplaceChild("bipedleftleg", CubeListBuilder.create().texOffs(36, 22).addBox(-2F, 0F, -2F, 3F, 7F, 4F),
                PartPose.offsetAndRotation(2F, 17F, 0F, 0F, 0F, 0F));
        PartDefinition d_skirtTop = root.addOrReplaceChild("skirttop", CubeListBuilder.create().texOffs(0, 16).addBox(-4F, 0F, -5F, 8F, 7F, 6F),
                PartPose.offsetAndRotation(0F, 16F, 2F, 0F, 0F, 0F));
        PartDefinition d_bipedHead = root.addOrReplaceChild("bipedhead", CubeListBuilder.create().texOffs(0, 0).addBox(-4F, -8F, -4F, 8F, 8F, 8F),
                PartPose.offsetAndRotation(0F, 10F, 0F, 0F, 0F, 0F));
        PartDefinition d_longHair = root.addOrReplaceChild("longhair", CubeListBuilder.create().texOffs(0, 49).addBox(-5F, 0F, -5F, 10F, 7F, 8F),
                PartPose.offsetAndRotation(0F, 4F, 2F, 0F, 0F, 0F));
        PartDefinition d_leftBraid = root.addOrReplaceChild("leftbraid", CubeListBuilder.create().texOffs(0, 32).addBox(0F, 0F, -1F, 1F, 6F, 1F),
                PartPose.offsetAndRotation(3F, 5F, -3F, -0.2443461F, 0F, 0F));
        PartDefinition d_rightBraid = root.addOrReplaceChild("rightbraid", CubeListBuilder.create().texOffs(0, 32).addBox(-1F, 0F, -1F, 1F, 6F, 1F),
                PartPose.offsetAndRotation(-3F, 5F, -3F, -0.2443461F, 0F, 0F));
        PartDefinition d_leftRibbon = root.addOrReplaceChild("leftribbon", CubeListBuilder.create().texOffs(46, 59).addBox(0F, -3F, 0F, 5F, 4F, 1F),
                PartPose.offsetAndRotation(-4F, 4F, 0F, 0.4461433F, 0F, -0.7853982F));
        PartDefinition d_rightRibbon = root.addOrReplaceChild("rightribbon", CubeListBuilder.create().texOffs(46, 59).addBox(0F, -3F, -1F, 5F, 4F, 1F),
                PartPose.offsetAndRotation(-4F, 4F, 0F, -0.4461411F, 3.141593F, 0.3490659F));
        return LayerDefinition.create(mesh, 64, 64);
    }

    /** The parts X1's render() draws, in its order. */
    private ModelPart[] drawn() {
        return new ModelPart[] {bipedBody, bipedRightArm, bipedLeftArm, bipedRightLeg, bipedLeftLeg, skirtTop, bipedHead, longHair, leftBraid, rightBraid, leftRibbon, rightRibbon};
    }

    @Override
    public void setupAnim(CursedDecoyDollEntity e, float movement, float far, float tick, float yaw, float pitch) {
        // ModelCursedDecoyDoll has no animation.

    }

    @Override
    public void renderToBuffer(PoseStack pose, VertexConsumer consumer, int light, int overlay, float r, float g, float b, float a) {
        for (ModelPart p : drawn()) p.render(pose, consumer, light, overlay, r, g, b, a);
    }
}
