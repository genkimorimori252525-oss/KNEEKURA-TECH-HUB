package com.github.tartaricacid.touhoulittlemaid.sim;

import com.github.tartaricacid.touhoulittlemaid.TouhouLittleMaid;
import com.github.tartaricacid.touhoulittlemaid.entity.passive.reimu.EntityReimu;
import com.github.tartaricacid.touhoulittlemaid.sim.trace.SimCh;
import com.github.tartaricacid.touhoulittlemaid.sim.trace.SimDelta;
import com.github.tartaricacid.touhoulittlemaid.sim.trace.SimProbe;
import com.github.tartaricacid.touhoulittlemaid.sim.trace.SimStackAttrib;
import com.github.tartaricacid.touhoulittlemaid.sim.trace.SimTrace;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.mojang.authlib.GameProfile;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.common.util.FakePlayer;
import net.minecraftforge.common.util.FakePlayerFactory;

import javax.annotation.Nullable;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

/**
 * 検証の 1 区画。1 ワールドに {@code scenario.spacing} 間隔で複数並べ、同時に走らせる。
 *
 * <p>アリーナは「誰を・いつ」だけを持ち、「何を記録するか」は {@link SimProbe} に委ねる。
 *
 * <p><b>追跡は型を列挙せず範囲で行う</b> —— 毎 tick アリーナ範囲の全エンティティを取得して
 * 前 tick との差分を取る。こうすると弾のクラスを 1 つも知らなくてよく、
 * 他 mod の弾でも新しく足した弾でも自動で記録に載る。
 */
public final class SimArena {
    /**
     * 落ちた物を消すまでの tick 数。**0 で実機のまま**(6000 tick = 5 分)。
     *
     * <p>にーくら 2026-08-23:「特にドロップアイテムが多くあると 60fps 前後になるね。
     * 水槽ではドロップアイテムを 1 秒で消すようにしないか？ もちろん、任意で ONOFF を
     * 切り替えられる方が好ましいかな。」
     *
     * <p><b>これは水槽を実機と違わせる設定なので、黙って効かせない。</b>
     * 値が変わるたびトレースの {@code log} チャンネルへ 1 行残す —— 記録を後から読む人が
     * 「なぜ物が消えているのか」を推測しなくて済むように。
     *
     * <p><b>実機との差は「メイドのアイテム拾い」に出る。</b> 霊夢も TLM のメイドなので
     * 落ちた物を拾う。1 秒で消すとその挙動は起きにくくなる。戦闘の観察には邪魔なだけだが、
     * 拾いの検証をするときは off にすること。
     *
     * <p>実現は Forge の {@code ItemEntity.lifespan} を縮めるだけ。discard() で消すのではなく
     * <b>バニラ自身の消滅経路</b>({@code ItemEntity.tick} の {@code age >= lifespan}、
     * ItemExpireEvent のフック込み)を通るので、他 mod の挙動も壊さない。
     */
    public static volatile int itemTtlTicks = 20;
    /** 直前にトレースへ書いた値。変わったときだけ 1 行書くための覚え。 */
    private int loggedItemTtl = Integer.MIN_VALUE;
    /**
     * 無音がこの tick 数続いたら「時間は進んでいる」とだけ書く ({@link SimCh#TICK})。
     *
     * <p>2 tick = 100ms。Viewer の時計が持つ緩衝の目標 (3〜4 tick) より細かいので、
     * 静かな間も底に触れずに進み続けられる。費用は無音時だけ 10 行/秒 (約 200B/秒) ——
     * 戦闘中の記録が 700KB/分 出ることを思えば無視できる。
     */
    private static final int TICK_MARK_EVERY = 2;
    private long lastTraceLines = -1L;
    private long lastMarkTick = -1L;

    /** 場外落下の判定。床からこれだけ下がったら「落ちた」とみなして戻す (void ワールドは底が無い)。 */
    private static final double VOID_GUARD_DEPTH = 32.0D;

    private enum State { WARMUP, RUNNING, DONE }

    private final int index;
    private final SimScenario scenario;
    private final String runId;
    private final ServerLevel level;
    private final int originX;
    private final int originZ;
    private final int floorY;
    private final AABB box;
    private final SimTrace trace;

    private State state = State.WARMUP;
    private int warmupTicks;
    private long tick;

    /** 追跡中の entity id。範囲スキャンの差分でここが増減する。 */
    private final Set<Integer> tracked = new HashSet<>();
    /** actor の spawn 位置 (場外落下時に戻す先)。 */
    private final Map<Integer, Vec3> homes = new LinkedHashMap<>();
    /** 役割つき actor (summary 用)。 */
    private final List<Entity> actors = new ArrayList<>();
    /** entity id -> シナリオが指定した role。ここに無いものは戦闘の副産物。 */
    private final Map<Integer, String> actorRoles = new LinkedHashMap<>();
    /** 見た目パラメータ ({@code getSync*}) を持つ entity の id。毎 tick のリフレクション判定を避ける。 */
    private final Set<Integer> visualIds = new HashSet<>();

    @Nullable
    private EntityReimu reimu;
    /**
     * 弾の台帳 —— id → その弾の型（{@code touhou_little_maid:reimu_needle} など）。
     * {@code proj ev:"gone"} には型が入っていなかった（実測: spawn 141件は type 有、
     * gone 141件は type 無で、欠落はここちょうど）ので、消えるときに引くために持つ。
     */
    private final java.util.Map<Integer, String> projType = new java.util.LinkedHashMap<>();

    /**
     * 弾の台帳（クラス → EntityType の登録 id）とスタック走査器。
     *
     * <p><b>実体は {@link SimStackAttrib} に在る</b> —— このクラスは Minecraft 依存が深く
     * JUnit に載らないため、走査そのものを試験できるように MC 非依存の純クラスへ切り出した
     * （{@code SimStackAttribTest}）。ここに残るのは保持と委譲だけで、
     * <b>{@link #onDamage} の帰属判定分岐は一切変えていない</b>。
     */
    private final SimStackAttrib stackAttrib = new SimStackAttrib();

    /**
     * 弾の台帳 —— id → <b>その弾を撃った時点の</b>霊夢の phase。
     * 被弾は着弾時に起きるが、技への帰属は<b>発射時</b>でなければ意味が無い
     * （追尾・滞留する弾では発射から着弾までに phase が変わる）。
     */
    private final java.util.Map<Integer, String> projPhase = new java.util.LinkedHashMap<>();

    /**
     * 13-04: 行単位デルタ判定(「前と同じ行は書かない」)。{@code pos}/{@code phys}/{@code anim}
     * の3チャンネルに使う。projPhase/projType と同じ持ち回し方(アリーナの寿命ぶん1つ、
     * id が消えたら forget する)。
     */
    private final SimDelta delta = new SimDelta();

    private String prevSection = "";

    // ---- summary 用カウンタ ----
    private int projSpawned;
    private double dmgByReimu;
    private double dmgToReimu;
    private int hitsByReimu;
    private int voidRescues;

    public SimArena(int index, SimScenario scenario, ServerLevel level, Path outDir, String runId) {
        this.index = index;
        this.scenario = scenario;
        this.runId = runId;
        this.level = level;
        this.originX = index * scenario.spacing;
        this.originZ = 0;
        this.floorY = scenario.floor == null ? 64 : scenario.floor.y;

        double r = Math.max(64.0D, (scenario.floor == null ? 32 : scenario.floor.radius) + 48.0D);
        this.box = new AABB(originX - r, floorY - 64, originZ - r, originX + r, floorY + 128, originZ + r);

        this.trace = SimTrace.open(outDir.resolve("arena-" + index + ".jsonl"));
    }

    public int index() {
        return this.index;
    }

    public boolean done() {
        return this.state == State.DONE;
    }

    public SimTrace trace() {
        return this.trace;
    }

    /** この座標がこのアリーナの担当範囲か (ダメージイベントの振り分け用)。 */
    public boolean contains(Entity e) {
        return this.box.contains(e.getX(), e.getY(), e.getZ());
    }

    // =========================================================================
    // セットアップ
    // =========================================================================

    /** chunk の forceload を要求する。void ワールドでは forceload しないと entity が tick しない。 */
    public void requestChunks() {
        int cr = ((scenario.floor == null ? 32 : scenario.floor.radius) >> 4) + 2;
        int cx = originX >> 4;
        int cz = originZ >> 4;
        for (int dx = -cr; dx <= cr; dx++) {
            for (int dz = -cr; dz <= cr; dz++) {
                this.level.setChunkForced(cx + dx, cz + dz, true);
            }
        }
    }

    private boolean chunksReady() {
        return this.level.isLoaded(new BlockPos(originX, floorY, originZ));
    }

    private void placeFloor() {
        SimScenario.FloorSpec f = this.scenario.floor;
        if (f == null) {
            return;
        }
        Block block = BuiltInRegistries.BLOCK.get(new ResourceLocation(f.block));
        if (block == Blocks.AIR) {
            TouhouLittleMaid.LOGGER.warn("[SIM] unknown floor block '{}', falling back to barrier", f.block);
            block = Blocks.BARRIER;
        }
        int placed = 0;
        for (int dx = -f.radius; dx <= f.radius; dx++) {
            for (int dz = -f.radius; dz <= f.radius; dz++) {
                // UPDATE_CLIENTS(2) のみ: 近傍更新を走らせないので広い床でも一瞬で置ける
                this.level.setBlock(new BlockPos(originX + dx, f.y, originZ + dz), block.defaultBlockState(), 2);
                placed++;
            }
        }
        this.trace.log(0, "floor placed: " + f.block + " r=" + f.radius + " (" + placed + " blocks) at y=" + f.y);
        placeWalls(f);
    }

    /**
     * 床の外周に壁を立てる。{@code floor.wallHeight} が 0 なら何もしない。
     *
     * <p><b>なぜ要るのか (2026-08-25 実測)</b>: Viewer は 2026-08-20 からチャンバーの
     * 4 面の壁を高さ 16 で描いていたが、<b>世界には壁が 1 個も無かった</b>。
     * {@code setBlock} を呼ぶ経路は床の円盤とシナリオの {@code blocks} の 2 つだけで、
     * 壁を置くコードがそもそも存在しなかった。絵だけの壁だったので、モブは端から落ちて
     * {@code VOID RESCUE} (下の {@code VOID_GUARD_DEPTH}) に拾われていた ——
     * <b>「壁に阻まれた」ではなく「落ちてから戻された」</b>ので、位置も速度も別物になる。
     *
     * <p>置き方は Viewer の {@code buildChamber} が描いていた枠に合わせる:
     * 外周の輪 ({@code |dx| == radius} または {@code |dz| == radius}) の上に、
     * 床の 1 つ上 ({@code y + 1}) から {@code wallHeight} 段。こうすると Viewer が
     * 引いている縦線が壁ブロックの外側の面と一致する。
     */
    private void placeWalls(SimScenario.FloorSpec f) {
        if (f.wallHeight <= 0) {
            return;
        }
        Block block = BuiltInRegistries.BLOCK.get(new ResourceLocation(f.wallBlock));
        if (block == Blocks.AIR) {
            TouhouLittleMaid.LOGGER.warn("[SIM] unknown wall block '{}', falling back to barrier", f.wallBlock);
            block = Blocks.BARRIER;
        }
        int placed = 0;
        for (int dx = -f.radius; dx <= f.radius; dx++) {
            for (int dz = -f.radius; dz <= f.radius; dz++) {
                // 外周の輪だけ。内側は床のまま (踏める面積を壁で潰さない)。
                if (Math.abs(dx) != f.radius && Math.abs(dz) != f.radius) {
                    continue;
                }
                for (int h = 1; h <= f.wallHeight; h++) {
                    // UPDATE_CLIENTS(2) のみ: 床と同じ理由 (近傍更新を走らせない)。
                    this.level.setBlock(new BlockPos(originX + dx, f.y + h, originZ + dz),
                            block.defaultBlockState(), 2);
                    placed++;
                }
            }
        }
        this.trace.log(0, "walls placed: " + f.wallBlock + " h=" + f.wallHeight
                + " (" + placed + " blocks) around r=" + f.radius);
    }

    /**
     * 構造物 (階段・柱・足場) を置く。移動/ジャンプの検証はここで作った段差の上に
     * ターゲットを置き、接敵のために登るかを見る形で行う。
     */
    private void placeBlocks() {
        for (SimScenario.BlockSpec b : this.scenario.blocks) {
            Block block = BuiltInRegistries.BLOCK.get(new ResourceLocation(b.block));
            if (block == Blocks.AIR && !"minecraft:air".equals(b.block)) {
                TouhouLittleMaid.LOGGER.warn("[SIM] unknown block '{}' in blocks[], skipped", b.block);
                this.trace.log(0, "SKIPPED unknown block: " + b.block);
                continue;
            }
            int x0 = (int) Math.floor(Math.min(b.from[0], b.to[0])), x1 = (int) Math.floor(Math.max(b.from[0], b.to[0]));
            int y0 = (int) Math.floor(Math.min(b.from[1], b.to[1])), y1 = (int) Math.floor(Math.max(b.from[1], b.to[1]));
            int z0 = (int) Math.floor(Math.min(b.from[2], b.to[2])), z1 = (int) Math.floor(Math.max(b.from[2], b.to[2]));
            int n = 0;
            for (int x = x0; x <= x1; x++) {
                for (int y = y0; y <= y1; y++) {
                    for (int z = z0; z <= z1; z++) {
                        this.level.setBlock(new BlockPos(originX + x, y, originZ + z), block.defaultBlockState(), 2);
                        n++;
                    }
                }
            }
            this.trace.log(0, "blocks: " + b.block + " " + x0 + "," + y0 + "," + z0
                    + " -> " + x1 + "," + y1 + "," + z1 + " (" + n + ")");
        }
    }

    /**
     * spawn 前に、前回までの run の残骸エンティティを掃除する。
     *
     * <p>{@code keepAlive: true} のシナリオはワールドが run 間で保存されるため、掃除ステップが
     * 無いと起動のたびに actor が積み上がり、計測が汚染される。掃いた数が 0 のときも黙らず、
     * 必ずログとトレースの両方へ報告する ({@code guardVoid} の VOID RESCUE ログと同じ思想 ——
     * 黙って直すと原因が消える)。
     */
    private void clearArena() {
        List<Entity> leftover = this.level.getEntities((Entity) null, this.box, e -> !(e instanceof Player));
        Map<String, Integer> byType = new LinkedHashMap<>();
        for (Entity e : leftover) {
            byType.merge(SimProbe.typeId(e), 1, Integer::sum);
            e.discard();
        }
        int n = leftover.size();
        TouhouLittleMaid.LOGGER.info("[SIM] arena {} cleared {} leftover entities before spawn: {}",
                this.index, n, byType);
        this.trace.log(0, "arena cleared: " + n + " leftover entities removed " + byType);
    }

    /**
     * owner 役の FakePlayer。霊夢の一部の判断 ({@code ReimuGroundAttackTask} /
     * {@code ReimuFlightDecisionPolicy}) が {@code getOwner()} を見るため、
     * プレイヤー不在のヘッドレスでも owner を用意しておく。アリーナ毎に別 UUID にして
     * 位置が互いに干渉しないようにする。
     */
    private FakePlayer spawnOperator() {
        UUID uuid = UUID.nameUUIDFromBytes(("tlm-simop-" + this.index).getBytes(java.nio.charset.StandardCharsets.UTF_8));
        FakePlayer op = FakePlayerFactory.get(this.level, new GameProfile(uuid, "simop_" + this.index));
        op.moveTo(originX, floorY + 1, originZ - 6, 0.0F, 0.0F);
        return op;
    }

    private void spawnActors() {
        FakePlayer op = spawnOperator();

        for (SimScenario.ActorSpec spec : this.scenario.actors) {
            EntityType<?> type = EntityType.byString(spec.type).orElse(null);
            if (type == null) {
                TouhouLittleMaid.LOGGER.error("[SIM] unknown entity type '{}' — skipped."
                        + " Run `/tlm sim entities` for the list of ids available in this instance.", spec.type);
                this.trace.log(0, "SKIPPED unknown entity type: " + spec.type);
                continue;
            }
            Entity e = type.create(this.level);
            if (e == null) {
                TouhouLittleMaid.LOGGER.error("[SIM] entity type '{}' refused to create", spec.type);
                continue;
            }

            double x = originX + spec.pos[0];
            double y = spec.pos[1];
            double z = originZ + spec.pos[2];
            e.moveTo(x, y, z, 0.0F, 0.0F);

            if (e instanceof Mob mob) {
                mob.finalizeSpawn(this.level, this.level.getCurrentDifficultyAt(mob.blockPosition()),
                        MobSpawnType.COMMAND, null, null);
                mob.setPersistenceRequired();
                if (spec.noAi) {
                    mob.setNoAi(true);
                }
                if (spec.hp != null && mob.getAttribute(Attributes.MAX_HEALTH) != null) {
                    mob.getAttribute(Attributes.MAX_HEALTH).setBaseValue(spec.hp);
                    mob.setHealth(spec.hp.floatValue());
                }
            }

            if (e instanceof EntityReimu r) {
                // owner を持たせる。tame 済みにしないと owner 判定が通らない経路がある。
                r.setTame(true);
                r.setOwnerUUID(op.getUUID());
                this.reimu = r;
            }

            boolean added = this.level.addFreshEntity(e);
            this.actors.add(e);
            this.actorRoles.put(e.getId(), spec.role == null ? SimCh.ROLE_TARGET : spec.role);
            this.homes.put(e.getId(), new Vec3(x, y, z));
            this.trace.log(0, "spawned " + spec.type + " as " + spec.role + " id=" + e.getId()
                    + " at " + String.format(java.util.Locale.ROOT, "%.1f/%.1f/%.1f", x, y, z)
                    + " added=" + added + " alive=" + e.isAlive() + " removed=" + e.isRemoved());
            if (!added) {
                TouhouLittleMaid.LOGGER.error("[SIM] addFreshEntity REFUSED for {} (id={}) — "
                        + "it will be absent from the whole run", spec.type, e.getId());
            }
        }
    }

    /**
     * 最初の数 tick だけ actor の生存状態を記録する。
     *
     * <p>「湧いたはずのものが記録に一度も出てこない」は原因が全く見えない事故なので、
     * 消えたのが <b>level から (getEntity==null)</b> なのか <b>死んだ (alive=false)</b> なのか
     * <b>アリーナ範囲外へ出た (inBox=false)</b> なのかを最初に切り分けられるようにしておく。
     */
    private void diagnoseActors(long t) {
        for (Entity a : this.actors) {
            Entity live = this.level.getEntity(a.getId());
            this.trace.log(t, "diag id=" + a.getId() + " type=" + SimProbe.typeId(a)
                    + " inLevel=" + (live != null)
                    + " alive=" + a.isAlive()
                    + " removed=" + a.isRemoved()
                    + " reason=" + a.getRemovalReason()
                    + " pos=" + String.format(java.util.Locale.ROOT, "%.2f/%.2f/%.2f", a.getX(), a.getY(), a.getZ())
                    + " inBox=" + this.box.contains(a.getX(), a.getY(), a.getZ()));
        }
    }

    /** 1 行目の {@code ch:meta}。Viewer が箱を正しい大きさで描くための hitbox 表を含む。 */
    private void writeMeta() {
        this.trace.event(0, SimCh.META, o -> {
            o.addProperty("scenario", this.scenario.name);
            o.addProperty("run", this.runId);
            o.addProperty("seed", this.scenario.seed);
            o.addProperty("arena", this.index);
            o.addProperty("duration", this.scenario.duration);
            o.addProperty("originX", this.originX);
            o.addProperty("originZ", this.originZ);
            o.addProperty("floorY", this.floorY);
            o.addProperty("floorRadius", this.scenario.floor == null ? 0 : this.scenario.floor.radius);
            // **絵と当たり判定を一致させるために出す。** Viewer はこれまで壁を高さ 16 で
            // 描いていたが、世界に壁があるかどうかを知る手立てが無かった (2026-08-25)。
            // 0 なら「枠は描くが当たり判定は無い」と Viewer 側が明示できる。
            o.addProperty("floorWallHeight", this.scenario.floor == null ? 0 : this.scenario.floor.wallHeight);
            o.addProperty("gameTime", this.level.getGameTime());
            // 13-04: 行単位デルタの契約を宣言する。値は SimDelta が持つ定数から取る
            // (数字を2箇所に書かない)。読み側(simlab/stats.mjs 等)の「欠測=前の値」
            // という前方フィルの契約はこの2フィールドが根拠になる。
            o.addProperty("delta", SimDelta.DELTA_MODE);
            o.addProperty("keyframe", SimDelta.KEYFRAME_TICKS);

            // 置いた構造物。Viewer はこれを箱として描き、「どの段差を登ったか」を目で追えるようにする。
            JsonArray blocks = new JsonArray();
            for (SimScenario.BlockSpec b : this.scenario.blocks) {
                JsonObject jb = new JsonObject();
                jb.addProperty("block", b.block);
                jb.addProperty("x0", (int) Math.floor(Math.min(b.from[0], b.to[0])));
                jb.addProperty("y0", (int) Math.floor(Math.min(b.from[1], b.to[1])));
                jb.addProperty("z0", (int) Math.floor(Math.min(b.from[2], b.to[2])));
                jb.addProperty("x1", (int) Math.floor(Math.max(b.from[0], b.to[0])));
                jb.addProperty("y1", (int) Math.floor(Math.max(b.from[1], b.to[1])));
                jb.addProperty("z1", (int) Math.floor(Math.max(b.from[2], b.to[2])));
                blocks.add(jb);
            }
            o.add("blocks", blocks);

            JsonArray mods = new JsonArray();
            net.minecraftforge.fml.ModList.get().getMods().forEach(m -> mods.add(m.getModId()));
            o.add("mods", mods);

            // 出てくる可能性のある型の hitbox 表。Viewer はこれを見て箱を描く。
            JsonObject types = new JsonObject();
            for (Entity e : this.actors) {
                JsonObject t = new JsonObject();
                t.addProperty("w", SimTrace.r3(e.getBbWidth()));
                t.addProperty("h", SimTrace.r3(e.getBbHeight()));
                types.add(SimProbe.typeId(e), t);
            }
            o.add("types", types);
        });
    }

    // =========================================================================
    // tick
    // =========================================================================

    /** SimRunner から毎 tick 呼ばれる。 */
    public void tick() {
        try {
            switch (this.state) {
                case WARMUP -> tickWarmup();
                case RUNNING -> tickRunning();
                case DONE -> { }
            }
        } catch (Exception e) {
            TouhouLittleMaid.LOGGER.error("[SIM] arena {} tick failed", this.index, e);
            finish("error");
        }
    }

    private void tickWarmup() {
        this.warmupTicks++;
        if (!chunksReady()) {
            if (this.warmupTicks > 200) {
                TouhouLittleMaid.LOGGER.warn("[SIM] arena {} chunks not loaded after 200 ticks, proceeding anyway",
                        this.index);
            } else {
                return;
            }
        }
        placeFloor();
        placeBlocks();
        clearArena();
        spawnActors();
        writeMeta();
        this.trace.log(0, "arena " + this.index + " ready: " + this.actors.size() + " actors"
                + (this.reimu == null ? " (no reimu)" : " reimu=" + this.reimu.getId()));
        this.state = State.RUNNING;
    }

    /**
     * 落ちた物の寿命を縮める({@link #itemTtlTicks})。**毎 tick 見る**ので、
     * 走っている最中に on にしたら既に落ちている物にも即座に効く。
     * off にしても、既に縮めた物は戻らない(縮めた事実は取り消せない) —— そう書いてある。
     */
    private void shortenItemLifetime(long t, Entity e) {
        int ttl = itemTtlTicks;
        if (ttl != this.loggedItemTtl) {
            this.loggedItemTtl = ttl;
            this.trace.log(t, ttl > 0
                    ? "item lifetime shortened to " + ttl + " ticks (tank setting; real game is 6000)"
                    : "item lifetime restored to the real game's 6000 ticks");
        }
        if (ttl <= 0 || !(e instanceof ItemEntity item)) {
            return;
        }
        if (item.lifespan > ttl) {
            item.lifespan = ttl;
        }
    }

    private void tickRunning() {
        long t = this.tick++;

        if (t < 3L) {
            diagnoseActors(t);
        }

        // --- 範囲内の全エンティティを取得し、前 tick との差分で spawn/gone を出す ---
        List<Entity> present = this.level.getEntities((Entity) null, this.box, e -> true);
        Set<Integer> seen = new HashSet<>(present.size() * 2);

        for (Entity e : present) {
            int id = e.getId();
            seen.add(id);
            if (this.tracked.add(id)) {
                onEntityAppeared(t, e);
                // **後から水槽へ放たれた霊夢を拾う。**
                // シナリオの actors から生まれた霊夢は spawnActors が this.reimu へ入れるが、
                // 走っている水槽へ /summon した霊夢はこの経路を通る。拾わないと
                // ai / anim / phys が 1 行も出ず、Viewer 側は表情 molang を受け取れないので
                // 顔が崩れて見える（2026-08-20 実測: 8670行のトレースで ch:anim が 0 行だった）。
                if (this.reimu == null && e instanceof EntityReimu adopted) {
                    this.reimu = adopted;
                    this.trace.log(t, "reimu adopted (summoned into a running tank): id=" + adopted.getId());
                }
            }
            shortenItemLifetime(t, e);
            SimProbe.pos(this.trace, t, e, this.delta);
            if (this.visualIds.contains(id)) {
                SimProbe.visual(this.trace, t, e);
            }
            guardVoid(t, e);
        }

        this.tracked.removeIf(id -> {
            if (seen.contains(id)) {
                return false;
            }
            SimProbe.gone(this.trace, t, id, "removed");
            // id 再利用対策(T-13-12): この id が別の entity として戻ってきたとき、
            // 前の entity の値を引き継がないよう台帳を忘れる。水槽は何度も出し入れするので
            // 実際に起きる。
            this.delta.forget(id);
            String goneType = this.projType.get(id);
            this.trace.event(t, SimCh.PROJ, o -> {
                o.addProperty("ev", "gone");
                o.addProperty("id", id);
                // 実測で type が欠けていたのはここだけ。台帳から引いて埋める。
                o.addProperty("type", goneType == null ? "-" : goneType);
            });
            this.projType.remove(id);
            this.projPhase.remove(id);
            return true;
        });

        // --- 霊夢の ai / anim / phys ---
        if (this.reimu != null && !this.reimu.isAlive()) {
            // 手放す。**次に放たれた霊夢を拾えるようにするため。**
            // 水槽は何度も出し入れするので、死んだ参照を握り続けると 2 体目以降が記録されない。
            // 13-04: id 再利用対策として、手放す時点でも台帳を忘れる
            // (tracked.removeIf の gone 側と合わせた二重の手当て。次に同じ id が
            // 使われたとき、前の霊夢の値を引き継がないようにするため)。
            this.delta.forget(this.reimu.getId());
            this.reimu = null;
        }
        if (this.reimu != null) {
            this.prevSection = SimProbe.reimu(this.trace, t, this.reimu, this.prevSection, this.delta);
        }

        markTimePassing(t);

        if (t + 1 >= this.scenario.duration) {
            finish("duration");
        }
    }

    /**
     * 何も書かなかった tick が続いたら、「時間は進んでいる」とだけ書く ({@link SimCh#TICK})。
     *
     * <p><b>行デルタ化の副作用を塞ぐ。</b> 静かな水槽は行を 1 つも書かないので、記録の上で
     * 「水槽が固まった」と「何も起きていない」が区別できない。実測 (2026-08-23、
     * にーくらの記録 2 本): <b>時間の 38〜57% が完全に無音、最長 18.6 秒</b>。
     * Viewer の時計はその間「データが尽きた」と読んでブレーキを踏み、底に触れ、
     * 緩衝の目標を 18.8 tick まで膨らませていた。
     *
     * <p>判定は {@link SimTrace#lines()} が増えたかどうか —— 「この tick で何か書いたか」を
     * 呼び出し側で数え直さずに済む唯一の値。賑やかなときは 1 行も増えない。
     */
    private void markTimePassing(long t) {
        long lines = this.trace.lines();
        if (lines != this.lastTraceLines) {
            this.lastTraceLines = lines;
            this.lastMarkTick = t;
            return;
        }
        if (this.lastMarkTick >= 0L && t - this.lastMarkTick < TICK_MARK_EVERY) {
            return;
        }
        this.trace.event(t, SimCh.TICK, null);
        this.lastMarkTick = t;
        this.lastTraceLines = this.trace.lines();
    }

    /**
     * 呼び出しスタックから「この被弾を起こした弾クラス」を探す。
     *
     * <p>実体と理由の記述は {@link SimStackAttrib} に在る。ここは委譲のみ。
     *
     * @return 見つかった弾クラスの登録 id。見つからない/例外なら null
     */
    private String projTypeFromStack() {
        return this.stackAttrib.resolve();
    }


    /**
     * 霊夢の現在の phase を読む。<b>読むだけで、何も書き戻さない。</b>
     * 取れないときは {@code "-"}（推測で値を作らない）。
     */
    private String currentPhase() {
        if (this.reimu == null || !this.reimu.isAlive()) {
            return "-";
        }
        try {
            String raw = com.github.tartaricacid.touhoulittlemaid.entity.ai.reimu.debug.ReimuAiDebug
                    .section(this.reimu).replace('\n', ' ').replaceAll("§.", "");
            Object phase = com.github.tartaricacid.touhoulittlemaid.sim.trace.SimSection.parse(raw).get("phase");
            return phase == null ? "-" : String.valueOf(phase);
        } catch (Throwable ignored) {
            return "-";   // 記録のために本編を落とさない
        }
    }

    private void onEntityAppeared(long t, Entity e) {
        boolean projectile = e instanceof Projectile;
        // シナリオが置いた actor だけが reimu/target。戦闘の副産物 (経験値オーブ等) は other。
        String role = this.actorRoles.get(e.getId());
        if (role == null) {
            role = projectile ? SimCh.ROLE_PROJECTILE
                    : (e instanceof EntityReimu ? SimCh.ROLE_REIMU : SimCh.ROLE_OTHER);
        }
        SimProbe.spawn(this.trace, t, e, role);
        if (SimProbe.hasVisual(e)) {
            this.visualIds.add(e.getId());
        }

        if (projectile) {
            this.projSpawned++;
            Projectile p = (Projectile) e;
            Entity owner = p.getOwner();
            Vec3 v = p.getDeltaMovement();
            String projTypeId = SimProbe.typeId(p);
            String firedPhase = currentPhase();
            this.projType.put(p.getId(), projTypeId);
            this.projPhase.put(p.getId(), firedPhase);
            this.stackAttrib.register(p.getClass(), projTypeId);
            this.trace.event(t, SimCh.PROJ, o -> {
                o.addProperty("ev", "spawn");
                o.addProperty("id", p.getId());
                o.addProperty("type", projTypeId);
                // phase: この弾を撃った時点の霊夢の技。着弾時ではなく発射時であることが要点。
                o.addProperty("phase", firedPhase);
                o.addProperty("owner", owner == null ? -1 : owner.getId());
                o.addProperty("vx", SimTrace.r3(v.x));
                o.addProperty("vy", SimTrace.r3(v.y));
                o.addProperty("vz", SimTrace.r3(v.z));
                o.addProperty("w", SimTrace.r3(p.getBbWidth()));
                o.addProperty("h", SimTrace.r3(p.getBbHeight()));
            });
        }
    }

    /**
     * 場外落下の救済。void ワールドでは落ちたら二度と戻らず、
     * 「なぜか途中から何も起きなくなったトレース」になってしまうので、
     * 元の位置へ戻したうえで<b>必ずログに残す</b> (黙って直すと原因が消える)。
     */
    private void guardVoid(long t, Entity e) {
        if (e.getY() >= this.floorY - VOID_GUARD_DEPTH) {
            return;
        }
        Vec3 home = this.homes.get(e.getId());
        if (home == null) {
            return;
        }
        e.teleportTo(home.x, home.y, home.z);
        e.setDeltaMovement(Vec3.ZERO);
        e.fallDistance = 0.0F;
        this.voidRescues++;
        this.trace.log(t, "VOID RESCUE id=" + e.getId() + " fell below y=" + (this.floorY - VOID_GUARD_DEPTH)
                + ", teleported home");
    }

    // =========================================================================
    // イベント受け口 (SimEvents から)
    // =========================================================================

    /**
     * {@code LivingDamageEvent} から呼ばれる。誰が誰にどの弾で何ダメージ、を残す。
     *
     * <p>攻撃者が {@code DamageSource} に載っていないとき、直接エンティティが projectile なら
     * その owner まで辿る。<b>ただし霊夢の弾幕は attacker も directEntity も持たない
     * {@code magic} ソースで飛ぶため、これでも帰属できない</b> —— 推測で埋めることはせず、
     * {@code attacker=-1} のまま記録する (Analyzer 側で「攻撃者情報なし」として明示的に数える)。
     */
    public void onDamage(long runTick, LivingEntity victim, DamageSource src, float amount) {
        Entity direct = src.getDirectEntity();
        Entity fromSource = src.getEntity();
        final Entity attacker = (fromSource == null && direct instanceof Projectile p && p.getOwner() != null)
                ? p.getOwner() : fromSource;
        boolean fromReimu = this.reimu != null && attacker != null && attacker.getId() == this.reimu.getId();
        boolean toReimu = this.reimu != null && victim.getId() == this.reimu.getId();
        if (fromReimu) {
            this.dmgByReimu += amount;
            this.hitsByReimu++;
        }
        if (toReimu) {
            this.dmgToReimu += amount;
        }
        // 技への帰属。**推測は一切しない。** 判定できなかったものは "none" と書いて表に出す。
        //   direct —— 直接の当たり元が台帳にある弾。phase は<b>その弾を撃った時点</b>のもの
        //   melee  —— attacker と direct が両方とも霊夢。phase は被弾 tick の現在値
        //   none   —— どちらでもない（attacker=-1 かつ direct=-1 の magic ソースはここ）
        //             この残りを埋めるのは 10-02 の仕事で、この計画では埋まらない
        int directId = direct == null ? -1 : direct.getId();
        int attackerId = attacker == null ? -1 : attacker.getId();
        int reimuId = this.reimu == null ? -1 : this.reimu.getId();
        String attrib;
        String hitProjType = null;
        String hitPhase = null;
        if (directId >= 0 && this.projType.containsKey(directId)) {
            attrib = "direct";
            hitProjType = this.projType.get(directId);
            hitPhase = this.projPhase.get(directId);
        } else if (reimuId >= 0 && attackerId == reimuId && directId == reimuId) {
            attrib = "melee";
            hitPhase = currentPhase();
        } else {
            // 第3段: attacker も direct も持たない magic ソース。
            // DamageSource がエンティティ参照を一切持たないので、**呼び出しスタックしか手が無い**。
            // 見つからなければ "none" のまま。フィールドを捏造しない。
            String byStack = projTypeFromStack();
            if (byStack != null) {
                attrib = "stack";
                hitProjType = byStack;
                // **着弾時**の phase しか付けられない（発射時は辿れない）。
                // 追尾/滞留する弾では別の技の行に載りうる —— SimCh の javadoc に明記してある。
                hitPhase = currentPhase();
            } else {
                attrib = "none";
            }
        }
        final String fAttrib = attrib;
        final String fProjType = hitProjType;
        final String fPhase = hitPhase;
        this.trace.event(runTick, SimCh.DMG, o -> {
            o.addProperty("victim", victim.getId());
            o.addProperty("attacker", attacker == null ? -1 : attacker.getId());
            o.addProperty("direct", direct == null ? -1 : direct.getId());
            o.addProperty("amount", SimTrace.r2(amount));
            o.addProperty("src", src.getMsgId());
            o.addProperty("hpAfter", SimTrace.r2(Math.max(0.0F, victim.getHealth() - amount)));
            o.addProperty("attrib", fAttrib);
            if (fProjType != null) {
                o.addProperty("projType", fProjType);
            }
            if (fPhase != null) {
                o.addProperty("phase", fPhase);
            }
        });
    }

    /** {@code ServerLevel#playSeededSound} の Mixin から呼ばれる。 */
    public void onSound(long runTick, String soundId, String source, double x, double y, double z,
                        float volume, float pitch) {
        this.trace.event(runTick, SimCh.SOUND, o -> {
            o.addProperty("id", soundId);
            o.addProperty("src", source);
            o.addProperty("x", SimTrace.r3(x));
            o.addProperty("y", SimTrace.r3(y));
            o.addProperty("z", SimTrace.r3(z));
            o.addProperty("vol", SimTrace.r2(volume));
            o.addProperty("pitch", SimTrace.r2(pitch));
        });
    }

    /** 音の座標がこのアリーナのものか。 */
    public boolean containsPos(double x, double y, double z) {
        return this.box.contains(x, y, z);
    }

    public long currentTick() {
        return Math.max(0L, this.tick - 1);
    }

    // =========================================================================
    // 終了
    // =========================================================================

    public void finish(String reason) {
        if (this.state == State.DONE) {
            return;
        }
        long t = Math.max(0L, this.tick - 1);
        this.trace.event(t, SimCh.END, o -> {
            o.addProperty("reason", reason);
            o.addProperty("ticks", this.tick);
            o.addProperty("projSpawned", this.projSpawned);
            o.addProperty("hitsByReimu", this.hitsByReimu);
            o.addProperty("dmgByReimu", SimTrace.r2(this.dmgByReimu));
            o.addProperty("dmgToReimu", SimTrace.r2(this.dmgToReimu));
            o.addProperty("voidRescues", this.voidRescues);

            JsonArray arr = new JsonArray();
            for (Entity e : this.actors) {
                JsonObject a = new JsonObject();
                a.addProperty("id", e.getId());
                a.addProperty("type", SimProbe.typeId(e));
                a.addProperty("alive", e.isAlive());
                if (e instanceof LivingEntity le) {
                    a.addProperty("hp", SimTrace.r2(le.getHealth()));
                    a.addProperty("maxHp", SimTrace.r2(le.getMaxHealth()));
                }
                arr.add(a);
            }
            o.add("actors", arr);
        });
        this.trace.close();
        this.state = State.DONE;
        TouhouLittleMaid.LOGGER.info("[SIM] arena {} finished ({}): {} ticks, {} projectiles, {} hits, {} dmg dealt",
                this.index, reason, this.tick, this.projSpawned, this.hitsByReimu,
                String.format(java.util.Locale.ROOT, "%.1f", this.dmgByReimu));
        // 13-04: 行単位デルタの効き具合。0件でも出す(clearArenaの掃除件数を0でも出す既存の方針と同じ
        // —— 黙って直すと原因が消える)。実機確認(Task 3)はこの行を読んでskippedがwrittenを
        // 大きく上回っているかを見る。
        TouhouLittleMaid.LOGGER.info("[SIM] arena {} delta: written={} skipped={} keyframes={}",
                this.index, this.delta.written(), this.delta.skipped(), this.delta.keyframes());
    }

    /** {@code summary.json} 用の 1 アリーナ分。 */
    public JsonObject summary() {
        JsonObject o = new JsonObject();
        o.addProperty("arena", this.index);
        o.addProperty("trace", this.trace.file().getFileName().toString());
        o.addProperty("ticks", this.tick);
        o.addProperty("lines", this.trace.lines());
        o.addProperty("projSpawned", this.projSpawned);
        o.addProperty("hitsByReimu", this.hitsByReimu);
        o.addProperty("dmgByReimu", SimTrace.r2(this.dmgByReimu));
        o.addProperty("dmgToReimu", SimTrace.r2(this.dmgToReimu));
        o.addProperty("voidRescues", this.voidRescues);
        return o;
    }
}
