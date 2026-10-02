package com.github.tartaricacid.touhoulittlemaid.sim.client;

import net.minecraft.client.Minecraft;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.api.distmarker.OnlyIn;

import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.stream.Stream;

/**
 * spike 004 の採取物に添える <b>JAR の SHA-256</b>（{@link SimBoneProbe} と
 * {@link SimBoneCapture} が共有する）。
 *
 * <p><b>難読名に依存する経路なので、どのビルドで採ったのかが後から判らないと結果が使えない。</b>
 * YSM が上がれば同じフィールド名は別のものを指しうる —— そのとき古い採取物を
 * 「同じもの」として扱わないための印。
 *
 * <p>2 箇所に同じものを書かないためだけに切り出してある（片方だけ直す事故を防ぐ）。
 */
@OnlyIn(Dist.CLIENT)
public final class SimBoneProbeHashes {

    private SimBoneProbeHashes() {}

    /**
     * {@code mods} の中の ysm / touhoulittlemaid の JAR を SHA-256 で。
     * 全部出すと 99 行になるので、この経路に関わる 2 つだけに絞る。
     */
    public static List<String> modJarHashes() {
        List<String> out = new ArrayList<>();
        try {
            Path mods = Minecraft.getInstance().gameDirectory.toPath().resolve("mods");
            if (!Files.isDirectory(mods)) {
                out.add("mods dir 無し: " + mods);
                return out;
            }
            try (Stream<Path> s = Files.list(mods)) {
                for (Path p : s.toList()) {
                    String n = p.getFileName().toString().toLowerCase(Locale.ROOT);
                    if (!n.endsWith(".jar")) {
                        continue;
                    }
                    if (!n.startsWith("ysm") && !n.startsWith("touhoulittlemaid")) {
                        continue;
                    }
                    out.add("jar.sha256   = " + sha256(p) + "  " + p.getFileName());
                }
            }
        } catch (Throwable t) {
            out.add("jar hash 取得失敗: " + t);
        }
        return out;
    }

    private static String sha256(Path p) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] buf = new byte[1 << 16];
            try (InputStream in = Files.newInputStream(p)) {
                int n;
                while ((n = in.read(buf)) > 0) {
                    md.update(buf, 0, n);
                }
            }
            StringBuilder sb = new StringBuilder();
            for (byte b : md.digest()) {
                sb.append(String.format("%02x", b));
            }
            return sb.toString();
        } catch (Throwable t) {
            return "(失敗)";
        }
    }
}
