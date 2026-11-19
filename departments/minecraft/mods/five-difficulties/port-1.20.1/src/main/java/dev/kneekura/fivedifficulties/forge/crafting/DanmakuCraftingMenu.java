package dev.kneekura.fivedifficulties.forge.crafting;

import dev.kneekura.fivedifficulties.core.x1.X1DanmakuCrafting;
import dev.kneekura.fivedifficulties.core.x1.X1DanmakuCrafting.ColorInput;
import dev.kneekura.fivedifficulties.forge.PortRegistries;
import dev.kneekura.fivedifficulties.forge.X1Config;
import dev.kneekura.fivedifficulties.forge.item.THLaserItem;
import dev.kneekura.fivedifficulties.forge.item.THShotItem;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.Container;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ClickType;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.inventory.ResultContainer;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.DyeItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Block;

/**
 * Port of X1 {@code ContainerDanmakuCrafting} / {@code ContainerDanmakuCraftingLaser} with their slots
 * ({@code SlotDanmakuCraftingA}, {@code SlotDanmakuResult}, {@code SlotLaserResult}). Slot order, positions
 * and X1's shift-click ranges (copied from the vanilla crafting table, so they do not match this layout)
 * are kept; the arithmetic lives in {@link X1DanmakuCrafting}.
 */
public class DanmakuCraftingMenu extends AbstractContainerMenu {
    private final boolean laser;
    private final ContainerLevelAccess access;
    private final Player player;
    private final SimpleContainer matrix = new SimpleContainer(9);
    private final SimpleContainer material = new SimpleContainer(1);
    private final SimpleContainer speed = new SimpleContainer(1);
    private final SimpleContainer way = new SimpleContainer(1);
    private final SimpleContainer copy = new SimpleContainer(1);
    private final SimpleContainer color = new SimpleContainer(1);
    private final SimpleContainer bound = new SimpleContainer(1);
    private final SimpleContainer gravity = new SimpleContainer(1);
    private final ResultContainer result = new ResultContainer();

    public static DanmakuCraftingMenu shot(int id, Inventory inv) {
        return new DanmakuCraftingMenu(PortRegistries.DANMAKU_CRAFTING_MENU.get(), id, inv, ContainerLevelAccess.NULL, false);
    }

    public static DanmakuCraftingMenu laser(int id, Inventory inv) {
        return new DanmakuCraftingMenu(PortRegistries.LASER_CRAFTING_MENU.get(), id, inv, ContainerLevelAccess.NULL, true);
    }

    public DanmakuCraftingMenu(MenuType<?> type, int id, Inventory inv, ContainerLevelAccess access, boolean laser) {
        super(type, id);
        this.laser = laser;
        this.access = access;
        this.player = inv.player;
        addSlot(new ResultSlot(result, 0, 228, 35));
        addSlot(new InputSlot(material, 0, 8, 17, laser ? 5 : 2));
        addSlot(new InputSlot(way, 0, 8, 35, 0));
        addSlot(new InputSlot(speed, 0, 8, 53, 0));
        addSlot(new InputSlot(copy, 0, 192, 17, 1));
        addSlot(new InputSlot(color, 0, 69, 17, 3));
        if (!laser) {
            addSlot(new InputSlot(gravity, 0, 69, 35, 0));
            addSlot(new InputSlot(bound, 0, 69, 53, 4));
        }
        for (int l = 0; l < 3; ++l) {
            for (int i = 0; i < 3; ++i) addSlot(new InputSlot(matrix, i + l * 3, 134 + i * 18, 17 + l * 18, 0));
        }
        for (int l = 0; l < 3; ++l) {
            for (int i = 0; i < 9; ++i) addSlot(new Slot(inv, i + l * 9 + 9, 48 + i * 18, 84 + l * 18));
        }
        for (int l = 0; l < 9; ++l) addSlot(new Slot(inv, l, 48 + l * 18, 142));
        onCraftMatrixChanged();
    }

    public boolean isLaser() {
        return laser;
    }

    /** SlotDanmakuCraftingA.isItemValid */
    private static boolean valid(int type, ItemStack s) {
        if (s.isEmpty()) return false;
        return switch (type) {
            case 0 -> s.is(PortRegistries.POWER_ITEM_SMALL.get());
            case 1 -> s.is(PortRegistries.POINT_ITEM.get());
            case 2 -> s.getItem() instanceof THShotItem;
            case 3 -> s.getItem() instanceof DyeItem || s.is(Items.GUNPOWDER) || s.is(Items.DIAMOND);
            case 4 -> s.is(PortRegistries.POWER_ITEM_BIG.get());
            case 5 -> s.getItem() instanceof THLaserItem;
            default -> false;
        };
    }

    private final class InputSlot extends Slot {
        private final int type;

        InputSlot(Container c, int index, int x, int y, int type) {
            super(c, index, x, y);
            this.type = type;
        }

        @Override
        public boolean mayPlace(ItemStack s) {
            return valid(type, s);
        }

        @Override
        public void setChanged() {
            super.setChanged();
            onCraftMatrixChanged();
        }
    }

    private X1DanmakuCrafting.Inputs inputs() {
        X1DanmakuCrafting.Inputs in = new X1DanmakuCrafting.Inputs();
        in.laser = laser;
        in.maxNumber = laser ? X1Config.laserMaxNumber() : X1Config.shotMaxNumber();
        ItemStack m = material.getItem(0);
        in.materialCount = m.getCount();
        CompoundTag nbt = m.getTag();
        // getTagCompound() != null: shot / laser items only get a tag from crafting or creative use
        in.materialHasTag = nbt != null;
        if (in.materialHasTag) {
            in.number = nbt.getShort("Number");
            in.form = nbt.getByte("DanmakuForm");
            in.speed = nbt.getByte("Speed");
            in.color = nbt.getByte("Color");
            in.special = nbt.getInt("Special");
            in.gravity = nbt.getByte("Gravity");
        }
        in.wayCount = way.getItem(0).getCount();
        in.speedCount = speed.getItem(0).getCount();
        in.copyCount = copy.getItem(0).getCount();
        in.gravityCount = laser ? 0 : gravity.getItem(0).getCount();
        in.boundCount = laser ? 0 : bound.getItem(0).getCount();
        ItemStack c = color.getItem(0);
        if (c.getItem() instanceof DyeItem dye) {
            in.colorInput = ColorInput.DYE;
            in.dyeDamage = 15 - dye.getDyeColor().getId(); // 1.7.10 dye damage order
        } else if (c.is(Items.GUNPOWDER)) {
            in.colorInput = ColorInput.GUNPOWDER;
        } else if (c.is(Items.DIAMOND)) {
            in.colorInput = ColorInput.DIAMOND;
        }
        for (int i = 0; i < 9; i++) in.matrix[i] = !matrix.getItem(i).isEmpty();
        return in;
    }

    /** onCraftMatrixChanged */
    public void onCraftMatrixChanged() {
        X1DanmakuCrafting.Result r = X1DanmakuCrafting.result(inputs());
        if (r == null) {
            result.setItem(0, ItemStack.EMPTY);
        } else {
            ItemStack made = new ItemStack(material.getItem(0).getItem(), r.count());
            CompoundTag nbt = made.getOrCreateTag();
            nbt.putShort("Number", r.number());
            nbt.putByte("DanmakuForm", r.form());
            nbt.putByte("Speed", r.speed());
            nbt.putByte("Color", r.color());
            if (!laser) {
                nbt.putInt("Special", r.special());
                nbt.putByte("Gravity", r.gravity());
            }
            result.setItem(0, made);
        }
        broadcastChanges();
    }

    private final class ResultSlot extends Slot {
        ResultSlot(Container c, int index, int x, int y) {
            super(c, index, x, y);
        }

        @Override
        public boolean mayPlace(ItemStack s) {
            return false;
        }

        @Override
        public void onTake(Player taker, ItemStack stack) {
            X1DanmakuCrafting.Uses u = X1DanmakuCrafting.uses(inputs());
            for (int i = 0; i < 9; i++) if (!matrix.getItem(i).isEmpty()) matrix.removeItem(i, u.matrixEach());
            use(way, u.way());
            use(speed, u.speed());
            if (!laser) {
                use(gravity, u.gravity());
                use(bound, u.bound());
            }
            use(material, u.material());
            use(copy, u.copy());
            super.onTake(taker, stack);
            onCraftMatrixChanged();
        }

        private void use(SimpleContainer c, int n) {
            if (n > 0 && !c.getItem(0).isEmpty()) c.removeItem(0, n); // decrStackSize clamps to the stack
        }
    }

    /** slotClick: X1 recomputes the result after every click. */
    @Override
    public void clicked(int slot, int button, ClickType type, Player p) {
        super.clicked(slot, button, type, p);
        onCraftMatrixChanged();
    }

    /** transferStackInSlot with X1's (vanilla crafting table) index ranges. */
    @Override
    public ItemStack quickMoveStack(Player p, int index) {
        ItemStack copyStack = ItemStack.EMPTY;
        Slot slot = this.slots.get(index);
        if (slot.hasItem()) {
            ItemStack s = slot.getItem();
            copyStack = s.copy();
            if (index == 0) {
                if (!moveItemStackTo(s, 10, 46, true)) return ItemStack.EMPTY;
                slot.onQuickCraft(s, copyStack);
            } else if (index >= 10 && index < 37) {
                if (!moveItemStackTo(s, 37, 46, false)) return ItemStack.EMPTY;
            } else if (index >= 37 && index < 46) {
                if (!moveItemStackTo(s, 10, 37, false)) return ItemStack.EMPTY;
            } else if (!moveItemStackTo(s, 10, 46, false)) {
                return ItemStack.EMPTY;
            }
            if (s.isEmpty()) slot.set(ItemStack.EMPTY);
            else slot.setChanged();
            if (s.getCount() == copyStack.getCount()) return ItemStack.EMPTY;
            slot.onTake(p, s);
        }
        return copyStack;
    }

    /** onContainerClosed: every input is dropped at the player. */
    @Override
    public void removed(Player p) {
        super.removed(p);
        if (p.level().isClientSide) return;
        for (SimpleContainer c : new SimpleContainer[] {matrix, way, speed, copy, color, gravity, bound, material}) {
            for (int i = 0; i < c.getContainerSize(); i++) {
                ItemStack s = c.removeItemNoUpdate(i);
                if (!s.isEmpty()) p.drop(s, false);
            }
        }
    }

    @Override
    public boolean stillValid(Player p) {
        Block block = laser ? PortRegistries.LASER_CRAFTING_TABLE.get() : PortRegistries.DANMAKU_CRAFTING_TABLE.get();
        return stillValid(access, p, block);
    }

    // test helpers (the runtime scenario drives the menu without a client)
    public SimpleContainer materialSlot() { return material; }
    public SimpleContainer waySlot() { return way; }
    public SimpleContainer colorSlot() { return color; }
    public SimpleContainer matrixSlots() { return matrix; }
    public SimpleContainer copySlot() { return copy; }
    public ResultContainer resultSlot() { return result; }
}
