package com.github.tartaricacid.touhoulittlemaid.sim;

import com.github.tartaricacid.touhoulittlemaid.TouhouLittleMaid;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.EntityType;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

/**
 * 水槽へ放てるモブの一覧を書き出す。
 *
 * <h3>なぜコマンドではなくファイルなのか</h3>
 * にーくら 2026-08-20:
 * <blockquote>
 * このサイトに霊夢のコードを置くなんて、どうして遠回りする必要が有るんだ。
 * jar を読み込む実機さながらの処理機構を施しておけば、jar 側の変更に応じて
 * 対応できるから、とりのこされる心配もないだろ？
 * </blockquote>
 * この一覧は <b>jar が書き、サイトは読むだけ</b>。Viewer はモブの名前を 1 つも持たない。
 * mods/ に別の mod を足せば選択肢が勝手に増え、抜けば消える —— サイト側の対応は要らない。
 *
 * <p>コマンド (RCON) 経由にしなかったのは、一覧が<b>起動時に 1 度決まって以後変わらない</b>ため。
 * 変わらないものを毎回問い合わせる必要はないし、水槽が立つ前でも読める方が都合がよい。
 *
 * <p>なお {@code simlab/scenarios/smoke.json} のコメントには
 * 「候補一覧は {@code /tlm sim entities}」と書いてあるが、<b>そのコマンドは実在しない</b>
 * （2026-08-20 に確認。サーバ側の sim コマンドは 1 つも登録されていない）。このクラスがその役目を負う。
 *
 * <h3>本番の挙動を変えない</h3>
 * 読むだけで、レジストリにも世界にも触らない。{@code SimLab.begin()} からしか呼ばれず、
 * sim を起動しない通常のゲームでは実行されない。
 */
public final class SimCatalog {

    /** 書き出すファイル名。serve.mjs がこの名前で読む。 */
    public static final String FILE_NAME = "entities.json";

    private SimCatalog() {}

    /**
     * {@code <outRoot>/entities.json} へ登録済み EntityType の一覧を書く。
     *
     * <p>失敗しても sim は走る —— カタログは観察の道具であって、水槽の一部ではない。
     * 例外はログに残して握る。
     *
     * @param outRoot トレースの出力ルート ({@code tlm.sim.out})
     */
    public static void write(Path outRoot) {
        try {
            List<EntityType<?>> types = new ArrayList<>();
            for (EntityType<?> type : BuiltInRegistries.ENTITY_TYPE) {
                types.add(type);
            }
            // id で並べる。mod ごとに固まり、同じ mod 内は名前順になるので人が探しやすい。
            types.sort(Comparator.comparing(t -> String.valueOf(BuiltInRegistries.ENTITY_TYPE.getKey(t))));

            JsonArray arr = new JsonArray();
            int summonable = 0;
            for (EntityType<?> type : types) {
                ResourceLocation id = BuiltInRegistries.ENTITY_TYPE.getKey(type);
                if (id == null) {
                    continue;
                }
                JsonObject o = new JsonObject();
                o.addProperty("id", id.toString());
                o.addProperty("mod", id.getNamespace());
                // MobCategory。放つ相手を絞り込むのに使う (MONSTER / CREATURE / MISC ...)。
                o.addProperty("category", type.getCategory().getName());
                // canSummon() が false のものは /summon が拒否する (player, ender_dragon の一部など)。
                // **一覧からは消さない** —— 「在るが放てない」と「無い」は違う情報なので、印だけ付けて渡す。
                o.addProperty("summonable", type.canSummon());
                // 翻訳キー。サーバ側では訳せないので、そのまま渡して Viewer の判断に委ねる。
                o.addProperty("translationKey", type.getDescriptionId());
                arr.add(o);
                if (type.canSummon()) {
                    summonable++;
                }
            }

            JsonObject root = new JsonObject();
            root.addProperty("//", "水槽へ放てるモブの一覧。SimCatalog が jar から書き出す。手で編集しても次の起動で上書きされる。");
            root.addProperty("count", arr.size());
            root.addProperty("summonable", summonable);
            root.add("entities", arr);

            Files.createDirectories(outRoot);
            Path file = outRoot.resolve(FILE_NAME);
            Files.write(file, root.toString().getBytes(StandardCharsets.UTF_8));
            TouhouLittleMaid.LOGGER.info("[SIM] entity catalog: {} types ({} summonable) -> {}",
                    arr.size(), summonable, file);
        } catch (Exception e) {
            // カタログが無くても水槽は立つ。Viewer 側は「一覧が無い」と表示すればよい。
            TouhouLittleMaid.LOGGER.warn("[SIM] entity catalog を書けなかった", e);
        }
    }
}
