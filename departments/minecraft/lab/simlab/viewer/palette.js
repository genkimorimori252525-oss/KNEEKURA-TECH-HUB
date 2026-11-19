/* =============================================================================
   SimLab — palette (palmask-deflate-v1) デコーダ
   -----------------------------------------------------------------------------
   Java 側の唯一の書き手は SimPaletteCodec.java (14-01)。ここはその読み手。
   1 レコードの生バイト列 (圧縮前) は mask || payload:
     mask    = ceil(bones/8) バイト、LSB-first、ビット b = ボーン b がこのレコードに含まれる
     payload = マスクが立ったボーンごとに 9 x float32 リトルエンディアン (pal0/pal1/pal2 のみ、
               pal3 は書かない —— golden 全標本で厳密 0 と裏取り済み)
   圧縮は Deflater レベル9・既定 (zlib ラップ、RFC 1950)。ブラウザの
   DecompressionStream('deflate') と node の zlib.inflateSync はどちらもこの形式を読める
   ('deflate-raw' ではない)。

   解凍は呼び出し側が注入する (ブラウザは非同期の DecompressionStream、node は同期の
   zlib.inflateSync) —— このファイルは inflate 済みバイト列だけを扱う。

   classic script として書く (IIFE, 依存ゼロ、ビルド無し) —— ysm.js / pick.js と同じ流儀。
   ============================================================================= */
'use strict';

(function (root) {

  const CODEC = 'palmask-deflate-v1';

  /** 1 ボーンあたり、ワイヤに乗る float 数 (pal0/pal1/pal2)。SimPaletteCodec.COMPS と同じ値。 */
  const COMPS = 9;

  /** 8 ビット中の立っているビット数 (mask の popcount に使う)。 */
  function popcountByte(v) {
    v = v - ((v >> 1) & 0x55);
    v = (v & 0x33) + ((v >> 2) & 0x33);
    return (v + (v >> 4)) & 0x0f;
  }

  /**
   * 1 レコード (解凍済みバイト列) を {@code state9} (9 float/ボーン) へ復号する。
   *
   * <p>{@code inflatedBytes} のサイズを {@code ceil(bones/8) + 36 * popcount(mask)} と
   * 厳密に突き合わせてから初めて {@code state9} へ触れる (圧縮爆弾対策 —— T-14-01)。
   * 合わなければ {@link Error} を投げ、{@code state9} は一切書き換えない。
   *
   * @param state9        書き換え先 (長さ {@code bones * COMPS})。keyframe ならまずゼロにする
   * @param inflatedBytes 解凍済みバイト列 (Uint8Array)
   * @param keyframe      K レコードなら true (デコードは状態を丸ごとゼロにしてから埋める)
   * @param bones         ボーン本数 (索引の {@code bones} —— レコード自身からは取らない)
   */
  function decodeRecord(state9, inflatedBytes, keyframe, bones) {
    const maskBytes = Math.ceil(bones / 8);
    if (inflatedBytes.length < maskBytes) {
      throw new Error('[SimPalette] 破損したレコード: 解凍後サイズ ' + inflatedBytes.length
        + ' バイトがマスク長 ' + maskBytes + ' バイトより小さい');
    }
    let popcount = 0;
    for (let i = 0; i < maskBytes; i++) popcount += popcountByte(inflatedBytes[i]);
    const expected = maskBytes + 36 * popcount;
    if (inflatedBytes.length !== expected) {
      throw new Error('[SimPalette] 破損したレコード: 解凍後サイズ ' + inflatedBytes.length
        + ' バイトが期待値 ' + expected + ' バイト (mask=' + maskBytes + ' + 36*popcount(' + popcount
        + ')) と一致しない');
    }

    // ここまで来て初めて state9 へ触れる。
    if (keyframe) state9.fill(0);
    const dv = new DataView(inflatedBytes.buffer, inflatedBytes.byteOffset, inflatedBytes.byteLength);
    let off = maskBytes;
    for (let b = 0; b < bones; b++) {
      const set = (inflatedBytes[b >> 3] >> (b & 7)) & 1;
      if (set) {
        for (let k = 0; k < COMPS; k++) {
          state9[b * COMPS + k] = dv.getFloat32(off, true);
          off += 4;
        }
      }
    }
  }

  /**
   * 索引 (`<stamp>.pal.json` を読んだもの、{@code binUrl} 付き) 上の逐次デコード状態を持つ。
   *
   * <p>{@code fetchRecord(byteOffset, byteLen)} はレコード i の生バイト列 (圧縮済み、
   * Uint8Array 相当) を返す非同期関数、{@code inflate(bytes)} はそれを解凍する非同期関数
   * (ブラウザは {@code DecompressionStream}、node は {@code zlib.inflateSync} をラップしたもの)。
   * どちらも呼び出し側が注入する —— このファイルは HTTP も zlib も知らない。
   *
   * <p>{@code at(tick)} はその tick の {@code state9} (Float32Array, 長さ {@code bones*9})
   * を返す。前進 (直前のフレームの次) は差分だけ復号し、後退やジャンプは直前以前の
   * 最も近い K まで巻き戻してから前進する —— K の外は自己完結しないため。
   * その tick に記録が無ければ ({@code slots[tick] === -1}) {@code null} を返す。
   */
  function makeStream(index, fetchRecord, inflate) {
    // **索引は差し替わりうる** (ライブでは 5 秒ごとの checkpoint で伸びる) ので let。
    let idx = index;
    const bones = idx.bones;
    const state9 = new Float32Array(bones * COMPS);
    let curFrame = -1;

    const offsets = [0];
    /** 足りない分だけ伸ばす。既存フレームの位置は動かない (bin は追記のみ)。 */
    function growOffsets() {
      while (offsets.length - 1 < idx.lens.length) {
        const i = offsets.length - 1;
        offsets.push(offsets[i] + idx.lens[i]);
      }
    }
    growOffsets();

    /**
     * ライブで伸びた索引へ差し替える。
     *
     * <p><b>state9 と curFrame は捨てない。</b> 捨てると差分チェーンの現在位置が
     * 失われ、次の at() が最寄りの K まで巻き戻して読み直すことになる ——
     * 5 秒ごとにそれをやると、checkpoint のたびに数十フレームを復号し直す。
     * bin は追記のみなので、いま state9 が指しているフレームは新しい索引でも同じフレーム。
     *
     * <p><b>同じ run の続きであることを確かめてから差し替える。</b> 別 run のものを
     * 繋ぐと、前の run の姿勢が残った state9 へ新しい bin を差分適用することになり、
     * <b>壊れた姿勢を黙って描く</b>。gt0 (run 開始時の gameTime) が run の同一性を持つ。
     *
     * @return 差し替えたら true。別 run / 後退している索引なら false
     *         (呼び出し側は作り直すこと。黙って古い索引を使い続けない)
     */
    function extend(next) {
      if (!next || next.bones !== bones || !next.lens || !next.slots || !next.kinds) return false;
      if (next.gt0 !== idx.gt0) return false;                 // 別の run
      if (next.lens.length < idx.lens.length) return false;   // 後退している (書き直された)
      idx = next;
      growOffsets();
      return true;
    }

    function nearestKeyframeAtOrBefore(frame) {
      for (let i = frame; i >= 0; i--) {
        if (idx.kinds[i] === 'K') return i;
      }
      return -1;
    }

    async function decodeFrame(i) {
      const raw = await fetchRecord(offsets[i], idx.lens[i]);
      const inflated = await inflate(raw);
      decodeRecord(state9, inflated, idx.kinds[i] === 'K', bones);
      curFrame = i;
    }

    async function at(tick) {
      if (tick < 0 || tick >= idx.slots.length) return null;
      const frame = idx.slots[tick];
      if (frame === -1 || frame === undefined) return null;
      if (frame === curFrame) return state9;
      if (curFrame !== -1 && frame > curFrame) {
        for (let i = curFrame + 1; i <= frame; i++) await decodeFrame(i);
      } else {
        const k = nearestKeyframeAtOrBefore(frame);
        if (k === -1) {
          throw new Error('[SimPalette] frame ' + frame + ' より前にキーフレームが無い (kinds[0] は "K" のはず)');
        }
        for (let i = k; i <= frame; i++) await decodeFrame(i);
      }
      return state9;
    }

    return {
      at,
      extend,
      get bones() { return bones; },
      /** 索引がいま持っているフレーム数 (伸びたかどうかの判定に使う)。 */
      get frames() { return idx.lens.length; },
      /** 索引がいま覆っている tick 数 (= slots.length)。 */
      get ticks() { return idx.slots.length; },
    };
  }

  root.SimPalette = { CODEC, COMPS, decodeRecord, makeStream };

})(typeof window !== 'undefined' ? window : globalThis);
