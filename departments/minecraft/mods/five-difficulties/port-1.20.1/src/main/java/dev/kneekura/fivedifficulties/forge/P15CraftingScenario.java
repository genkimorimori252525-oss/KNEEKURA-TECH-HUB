package dev.kneekura.fivedifficulties.forge;

import com.mojang.authlib.GameProfile;
import dev.kneekura.fivedifficulties.forge.crafting.DanmakuCraftingMenu;
import dev.kneekura.fivedifficulties.forge.entity.THShotEntity;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.inventory.ClickType;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.common.util.FakePlayer;
import net.minecraftforge.common.util.FakePlayerFactory;
import net.minecraftforge.event.entity.EntityJoinLevelEvent;
import net.minecraftforge.event.server.ServerStartedEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import java.util.UUID;

/** P15 dedicated-server scenario: the danmaku / laser crafting tables (FIVE_DIFFICULTIES_P15_RUNTIME_SCENARIO=1). */
@Mod.EventBusSubscriber(modid = FiveDifficultiesPort.MOD_ID, bus = Mod.EventBusSubscriber.Bus.FORGE)
public final class P15CraftingScenario {
    public static final String ENV = "FIVE_DIFFICULTIES_P15_RUNTIME_SCENARIO";
    private static ServerLevel level;
    private static double bx, by, bz;
    private static int shots;
    private static boolean counting;

    private P15CraftingScenario() {}

    private static boolean enabled() {
        return "1".equals(System.getenv(ENV));
    }

    @SubscribeEvent
    public static void onJoin(EntityJoinLevelEvent event) {
        if (!enabled() || event.getLevel().isClientSide || !counting) return;
        Entity e = event.getEntity();
        if (e instanceof THShotEntity && Math.abs(e.getX() - bx) < 48 && Math.abs(e.getZ() - bz) < 48) shots++;
    }

    @SubscribeEvent
    public static void onServerStarted(ServerStartedEvent event) {
        if (!enabled()) return;
        level = event.getServer().overworld();
        BlockPos spawn = level.getSharedSpawnPos();
        bx = spawn.getX() - 70 + 0.5D;
        bz = spawn.getZ() - 70 + 0.5D;
        by = level.getHeight(Heightmap.Types.MOTION_BLOCKING, spawn.getX() - 70, spawn.getZ() - 70);
        try {
            run();
            FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P15_RUNTIME_SCENARIO_PASS");
            ScenarioShutdown.finished(level.getServer(), ENV);
        } catch (Throwable failure) {
            FiveDifficultiesPort.LOGGER.error("FIVE_DIFFICULTIES_P15_RUNTIME_SCENARIO_FAIL", failure);
            ScenarioShutdown.failed(level.getServer());
        }
    }

    private static void run() {
        FakePlayer p = FakePlayerFactory.get(level, new GameProfile(UUID.fromString("00000000-0000-0000-0000-0000f9150001"), "[FDP15]"));
        p.moveTo(bx, by, bz, -90F, 0F);
        p.getInventory().clearContent();

        // 1. danmaku table: 2 plain shots, 3 small power for the number, one centre power, blue dye
        DanmakuCraftingMenu menu = new DanmakuCraftingMenu(PortRegistries.DANMAKU_CRAFTING_MENU.get(), 0, p.getInventory(),
                ContainerLevelAccess.NULL, false);
        menu.materialSlot().setItem(0, new ItemStack(PortRegistries.SHOT_ITEMS.get(0).get(), 2));
        menu.waySlot().setItem(0, new ItemStack(PortRegistries.POWER_ITEM_SMALL.get(), 3));
        menu.matrixSlots().setItem(4, new ItemStack(PortRegistries.POWER_ITEM_SMALL.get(), 1));
        menu.colorSlot().setItem(0, new ItemStack(Items.BLUE_DYE));
        menu.onCraftMatrixChanged();
        ItemStack made = menu.resultSlot().getItem(0);
        require(made.is(PortRegistries.SHOT_ITEMS.get(0).get()) && made.getCount() == 1, "result " + made);
        CompoundTag t = made.getTag();
        require(t != null && t.getShort("Number") == 4 && t.getByte("DanmakuForm") == 0 && t.getByte("Color") == 1,
                "Number 4, point form, blue: " + t);
        menu.clicked(0, 0, ClickType.PICKUP, p); // take it
        require(ItemStack.isSameItemSameTags(menu.getCarried(), made), "the crafted shot is on the cursor");
        require(menu.waySlot().isEmpty() && menu.matrixSlots().getItem(4).isEmpty()
                && menu.materialSlot().getItem(0).getCount() == 1, "3 power, the centre power and one material used");
        require(menu.resultSlot().getItem(0).isEmpty() == false, "the remaining plain shot shows a new (plain) result");
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P15_CRAFT_PASS number=4 form=0 color=1");

        // 2. the crafted item fires its four shots
        ItemStack crafted = menu.getCarried().copy();
        menu.setCarried(ItemStack.EMPTY);
        p.setItemInHand(InteractionHand.MAIN_HAND, crafted);
        shots = 0;
        counting = true;
        p.getMainHandItem().use(level, p, InteractionHand.MAIN_HAND);
        counting = false;
        require(shots == 4, "the crafted item fires 4 shots, saw " + shots);
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P15_FIRE_PASS shots=4");

        // 3. closing the menu drops the inputs
        int before = level.getEntitiesOfClass(net.minecraft.world.entity.item.ItemEntity.class,
                p.getBoundingBox().inflate(4)).size();
        menu.removed(p);
        int after = level.getEntitiesOfClass(net.minecraft.world.entity.item.ItemEntity.class,
                p.getBoundingBox().inflate(4)).size();
        require(after - before >= 2, "closing drops the material and the dye, dropped " + (after - before));

        // 4. laser table: Laser Max Number 8
        DanmakuCraftingMenu lm = new DanmakuCraftingMenu(PortRegistries.LASER_CRAFTING_MENU.get(), 0, p.getInventory(),
                ContainerLevelAccess.NULL, true);
        lm.materialSlot().setItem(0, new ItemStack(PortRegistries.LASER_ITEMS.get(0).get()));
        lm.waySlot().setItem(0, new ItemStack(PortRegistries.POWER_ITEM_SMALL.get(), 20));
        lm.onCraftMatrixChanged();
        ItemStack laser = lm.resultSlot().getItem(0);
        require(laser.is(PortRegistries.LASER_ITEMS.get(0).get()) && laser.getTag().getShort("Number") == 8
                && !laser.getTag().contains("Gravity"), "laser result " + laser.getTag());
        lm.clicked(0, 0, ClickType.PICKUP, p);
        require(lm.waySlot().getItem(0).getCount() == 13, "20 > 8: 7 used (X1), left " + lm.waySlot().getItem(0).getCount());
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P15_LASER_PASS number=8 powerUsed=7");

        // 5. the block: light 15, opens its menu
        BlockPos at = BlockPos.containing(bx + 2, by, bz);
        level.setBlockAndUpdate(at, PortRegistries.DANMAKU_CRAFTING_TABLE.get().defaultBlockState());
        require(level.getBlockState(at).getLightEmission(level, at) == 15, "the table glows at 15");
        level.getBlockState(at).use(level, p, InteractionHand.MAIN_HAND,
                new BlockHitResult(Vec3.atCenterOf(at), Direction.UP, at, false));
        require(p.containerMenu instanceof DanmakuCraftingMenu m && !m.isLaser(), "using the block opens the danmaku menu");
        p.closeContainer();
        FiveDifficultiesPort.LOGGER.info("FIVE_DIFFICULTIES_P15_BLOCK_PASS light=15 opens=danmaku");
    }

    private static void require(boolean ok, String what) {
        if (!ok) throw new IllegalStateException("P15 scenario failed: " + what);
    }
}
