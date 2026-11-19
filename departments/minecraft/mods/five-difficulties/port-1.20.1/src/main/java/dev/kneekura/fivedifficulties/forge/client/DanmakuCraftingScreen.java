package dev.kneekura.fivedifficulties.forge.client;

import dev.kneekura.fivedifficulties.forge.FiveDifficultiesPort;
import dev.kneekura.fivedifficulties.forge.crafting.DanmakuCraftingMenu;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.client.resources.language.I18n;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.player.Inventory;

/** Port of X1 GuiDanmakuCrafting / GuiDanmakuCraftingLaser: a 256-wide background and X1's labels. */
public final class DanmakuCraftingScreen extends AbstractContainerScreen<DanmakuCraftingMenu> {
    private static final ResourceLocation SHOT_BG =
            new ResourceLocation(FiveDifficultiesPort.MOD_ID, "textures/gui/danmaku_crafting_table.png");
    private static final ResourceLocation LASER_BG =
            new ResourceLocation(FiveDifficultiesPort.MOD_ID, "textures/gui/laser_crafting_table.png");

    public DanmakuCraftingScreen(DanmakuCraftingMenu menu, Inventory inv, Component title) {
        super(menu, inv, title);
        this.imageWidth = 256;
    }

    @Override
    protected void renderLabels(GuiGraphics g, int mouseX, int mouseY) {
        int c = 4210752;
        g.drawString(font, I18n.get(menu.isLaser() ? "laserCrafting.name" : "danmakuCrafting.name"), 6, 6, c, false);
        g.drawString(font, I18n.get("danmakuCrafting.form"), 134, 6, c, false);
        g.drawString(font, I18n.get("danmakuCrafting.copy"), 192, 6, c, false);
        g.drawString(font, I18n.get("danmakuCrafting.material"), 26, 22, c, false);
        g.drawString(font, I18n.get("danmakuCrafting.number"), 26, 39, c, false);
        g.drawString(font, I18n.get("danmakuCrafting.speed"), 26, 56, c, false);
        g.drawString(font, I18n.get("danmakuCrafting.color"), 87, 22, c, false);
        if (!menu.isLaser()) {
            g.drawString(font, I18n.get("danmakuCrafting.gravity"), 87, 39, c, false);
            g.drawString(font, I18n.get("danmakuCrafting.bound"), 87, 56, c, false);
        }
        g.drawString(font, I18n.get("container.inventory"), 48, this.imageHeight - 96 + 2, c, false);
    }

    @Override
    protected void renderBg(GuiGraphics g, float partialTick, int mouseX, int mouseY) {
        int k = (this.width - this.imageWidth) / 2;
        int l = (this.height - this.imageHeight) / 2;
        g.blit(menu.isLaser() ? LASER_BG : SHOT_BG, k, l, 0, 0, this.imageWidth, this.imageHeight);
    }

    @Override
    public void render(GuiGraphics g, int mouseX, int mouseY, float partialTick) {
        renderBackground(g);
        super.render(g, mouseX, mouseY, partialTick);
        renderTooltip(g, mouseX, mouseY);
    }
}
