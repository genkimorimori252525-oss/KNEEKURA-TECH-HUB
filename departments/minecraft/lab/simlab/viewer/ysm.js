/* =============================================================================
   SimLab — YSM (Bedrock) モデル/アニメの読み込みと再生
   -----------------------------------------------------------------------------
   霊夢だけは「MC に焼かせた三角形」ではなく、ボーン階層のまま読んでアニメを再生する。
   モデルもモーションも読める JSON で存在し、mod が指定するアニメ名がトレースに
   毎 tick 残っているので、実機と同じデータを同じ順序で当てられる。

   ---------------------------------------------------------------------------
   座標変換の規約 —— 推測ではなく、このリポジトリの simplebedrockmodel の実装から取得。
   (AbstractBedrockEntityModel.convertPivot / convertOrigin / convertRotation,
    BedrockPart.translateAndRotate, BedrockCube.VERTEX_ORDER, FaceItem.getRotatedUVs)

     Java 版のモデル空間は Y が下向き。だから:
       ボーンの平行移動   root : ( pivot.x        , 24 - pivot.y          , pivot.z        )
                          child: ( pivot.x - 親.x , 親.y - pivot.y        , pivot.z - 親.z )
       キューブの最小角   ( origin.x - pivot.x , pivot.y - origin.y - size.y , origin.z - pivot.z )
       いずれも /16 してブロック単位にする。

     ボーンの局所変換 = T(上記) · Rz · Ry · Rx     ← T(pivot)·R·T(-pivot) ではない
     回転は度→ラジアンのみ。符号反転なし。

     面の頂点順は VERTEX_ORDER、UV は [右上, 左上, 左下, 右下]。

     エンティティへの最終変換 (vanilla LivingEntityRenderer と同じ):
       rotY(180 - bodyYaw) · scale(-1,-1,1) · translate(0,-1.501,0)
       scale(-1,-1,1) の行列式は +1 なので巻き順は反転しない。

     YSM の width_scale / height_scale は pivot/origin/size に先に掛ける
     (このモデルは頭 pivot が 33.96 = 24/0.7 で、掛けて初めて標準の 24 に乗る)。
   ============================================================================= */
'use strict';

(function (root) {

  // ===========================================================================
  // mat4 (列優先)
  // ===========================================================================
  const M = {
    ident: () => new Float32Array([1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]),
    mul(a, b, o) {
      o = o || new Float32Array(16);
      for (let c = 0; c < 4; c++) for (let r = 0; r < 4; r++) {
        o[c*4+r] = a[r]*b[c*4] + a[4+r]*b[c*4+1] + a[8+r]*b[c*4+2] + a[12+r]*b[c*4+3];
      }
      return o;
    },
    trans(x, y, z) { const m = M.ident(); m[12]=x; m[13]=y; m[14]=z; return m; },
    scale(x, y, z) { const m = M.ident(); m[0]=x; m[5]=y; m[10]=z; return m; },
    rotX(a) { const c=Math.cos(a), s=Math.sin(a), m=M.ident(); m[5]=c; m[6]=s; m[9]=-s; m[10]=c; return m; },
    rotY(a) { const c=Math.cos(a), s=Math.sin(a), m=M.ident(); m[0]=c; m[2]=-s; m[8]=s; m[10]=c; return m; },
    rotZ(a) { const c=Math.cos(a), s=Math.sin(a), m=M.ident(); m[0]=c; m[1]=s; m[4]=-s; m[5]=c; return m; },
    apply(m, v) {
      return [
        m[0]*v[0] + m[4]*v[1] + m[8]*v[2] + m[12],
        m[1]*v[0] + m[5]*v[1] + m[9]*v[2] + m[13],
        m[2]*v[0] + m[6]*v[1] + m[10]*v[2] + m[14],
      ];
    },
  };
  const DEG = Math.PI / 180;

  // ===========================================================================
  // ジオメトリ
  // ===========================================================================
  /** 8 頂点の並びと面ごとの頂点順 (BedrockCube と同じ)。面は DOWN,UP,NORTH,SOUTH,WEST,EAST。 */
  const CORNERS = [[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0,0,1],[1,0,1],[1,1,1],[0,1,1]];
  const VERTEX_ORDER = [[5,4,0,1],[2,3,7,6],[1,0,3,2],[4,5,6,7],[0,4,7,3],[5,1,2,6]];
  const DIR_NAME = ['down','up','north','south','west','east'];

  /** 面ごと UV。FaceItem.getRotatedUVs と同じ並び [右上,左上,左下,右下]。 */
  function faceUv(cube, i, texW, texH) {
    const f = cube.uv && !Array.isArray(cube.uv) ? cube.uv[DIR_NAME[i]] : null;
    if (!f || !f.uv) return null;
    const sz = f.uv_size || [0, 0];
    if (Math.abs(sz[0]) < 1e-9 && Math.abs(sz[1]) < 1e-9) return null;
    const u1 = f.uv[0]/texW, v1 = f.uv[1]/texH;
    const u2 = (f.uv[0]+sz[0])/texW, v2 = (f.uv[1]+sz[1])/texH;
    switch (f.uv_rotation | 0) {
      case 90:  return [u1,v1, u1,v2, u2,v2, u2,v1];
      case 180: return [u1,v2, u2,v2, u2,v1, u1,v1];
      case 270: return [u2,v2, u2,v1, u1,v1, u1,v2];
      default:  return [u2,v1, u1,v1, u1,v2, u2,v2];
    }
  }

  /**
   * Bedrock geometry を「ボーン階層 + ボーン番号つき頂点」に変換する。
   * 頂点はボーンの局所空間に置く —— 実行時にボーン行列を掛けるだけで動くようにするため。
   *
   * @returns {{bones:Array, verts:Float32Array, boneIndex:Float32Array, count:number,
   *            texW:number, texH:number}}
   *          verts は [x,y,z, u,v, nx,ny,nz] の 8 要素/頂点 (色は不要なので持たない)
   */
  function buildGeometry(geo, wScale, hScale, hiddenBones) {
    const desc = geo.description || {};
    const texW = desc.texture_width || 64, texH = desc.texture_height || 64;
    const S = (p) => [p[0]*wScale, p[1]*hScale, p[2]*wScale];

    const src = geo.bones;
    const byName = new Map(src.map((b) => [b.name, b]));
    const bones = [];
    const boneNo = new Map();
    // 親が先に来るように並べ替える (実行時に 1 パスで world 行列を積めるように)
    const visit = (b, guard) => {
      if (boneNo.has(b.name) || guard > 128) return;
      const par = b.parent && byName.get(b.parent);
      if (par) visit(par, guard + 1);
      boneNo.set(b.name, bones.length);
      const piv = S(b.pivot || [0,0,0]);
      let tx, ty, tz;
      if (par) {
        const pp = S(par.pivot || [0,0,0]);
        tx = piv[0]-pp[0]; ty = pp[1]-piv[1]; tz = piv[2]-pp[2];
      } else {
        tx = piv[0]; ty = 24-piv[1]; tz = piv[2];
      }
      const r = b.rotation || [0,0,0];
      bones.push({
        name: b.name,
        parent: par ? boneNo.get(par.name) : -1,
        t: [tx/16, ty/16, tz/16],
        r: [r[0]*DEG, r[1]*DEG, r[2]*DEG],
      });
    };
    for (const b of src) visit(b, 0);

    const verts = [];
    const boneIdx = [];
    for (const b of src) {
      if (!b.cubes || !b.cubes.length) continue;
      if (hiddenBones && isHidden(b, byName, hiddenBones, 0)) continue;
      const no = boneNo.get(b.name);
      const piv = S(b.pivot || [0,0,0]);
      for (const c of b.cubes) {
        const o = S(c.origin), sz = S(c.size), inf = c.inflate || 0;
        // キューブ自身の回転はボーンの子として畳み込む (静的なので事前計算でよい)
        let pre = null, base = piv;
        if (c.rotation && c.rotation.some((x) => x !== 0) && c.pivot) {
          const cp = S(c.pivot);
          pre = M.trans((cp[0]-piv[0])/16, (piv[1]-cp[1])/16, (cp[2]-piv[2])/16);
          pre = M.mul(pre, M.rotZ(c.rotation[2]*DEG));
          pre = M.mul(pre, M.rotY(c.rotation[1]*DEG));
          pre = M.mul(pre, M.rotX(c.rotation[0]*DEG));
          base = cp;
        }
        const x0 = (o[0]-base[0]-inf)/16;
        const y0 = (base[1]-o[1]-sz[1]-inf)/16;
        const z0 = (o[2]-base[2]-inf)/16;
        const w = (sz[0]+inf*2)/16, h = (sz[1]+inf*2)/16, d = (sz[2]+inf*2)/16;

        const P = CORNERS.map((k) => {
          const v = [x0 + k[0]*w, y0 + k[1]*h, z0 + k[2]*d];
          return pre ? M.apply(pre, v) : v;
        });
        for (let i = 0; i < 6; i++) {
          const uv = faceUv(c, i, texW, texH);
          if (!uv) continue;
          const vo = VERTEX_ORDER[i];
          const p = [P[vo[0]], P[vo[1]], P[vo[2]], P[vo[3]]];
          const e1 = [p[1][0]-p[0][0], p[1][1]-p[0][1], p[1][2]-p[0][2]];
          const e2 = [p[2][0]-p[1][0], p[2][1]-p[1][1], p[2][2]-p[1][2]];
          let n = [e1[1]*e2[2]-e1[2]*e2[1], e1[2]*e2[0]-e1[0]*e2[2], e1[0]*e2[1]-e1[1]*e2[0]];
          const l = Math.hypot(n[0], n[1], n[2]) || 1;
          n = [n[0]/l, n[1]/l, n[2]/l];
          for (const tri of [[0,1,2],[0,2,3]]) {
            for (const k of tri) {
              verts.push(p[k][0], p[k][1], p[k][2], uv[k*2], uv[k*2+1], n[0], n[1], n[2]);
              boneIdx.push(no);
            }
          }
        }
      }
    }
    return {
      bones, texW, texH,
      verts: new Float32Array(verts),
      boneIndex: new Float32Array(boneIdx),
      count: boneIdx.length,
    };
  }

  function isHidden(b, byName, hidden, guard) {
    if (guard > 128) return false;
    if (hidden.has(b.name)) return true;
    const p = b.parent && byName.get(b.parent);
    return p ? isHidden(p, byName, hidden, guard + 1) : false;
  }

  // ===========================================================================
  // molang — 式は 14% だけ、しかも中身は頭追従がほとんど。
  // 必要なのは 四則 / 括弧 / 比較 / 三項 / math.* / 変数 だけ。
  // ===========================================================================
  function molang(expr, vars) {
    if (typeof expr === 'number') return expr;
    if (typeof expr !== 'string') return 0;
    const s = expr.trim();
    if (s === '' || s === 'catmullrom' || s === 'linear' || s === 'step') return 0;
    let i = 0;
    const ws = () => { while (i < s.length && s[i] === ' ') i++; };
    const peek = (t) => { ws(); return s.startsWith(t, i); };
    const eat = (t) => { ws(); if (s.startsWith(t, i)) { i += t.length; return true; } return false; };

    function primary() {
      ws();
      if (eat('(')) { const v = ternary(); eat(')'); return v; }
      if (eat('-')) return -primary();
      if (eat('+')) return primary();
      // 単項 not。'!=' の '!' と取り違えないよう次が '=' でないことを見る。
      // controller の遷移条件はほぼ全部 ! と && と || で書かれているので、
      // ここが無いと条件が軒並み誤判定になる (2026-08-19 に実測して発覚)。
      if (s[i] === '!' && s[i + 1] !== '=') { i++; return primary() ? 0 : 1; }
      // 文字列リテラル。molang の文字列は関数引数にしか現れないが、
      // **読み飛ばさずに正しく消費すること**が重要 —— 途中で切ると i が文字列の中に
      // 取り残され、以降の式がまるごと壊れる。値は String オブジェクトで返し、
      // 数値と区別できるようにする。
      if (s[i] === "'" || s[i] === '"') {
        const q = s[i]; let j = i + 1;
        while (j < s.length && s[j] !== q) j++;
        const lit = s.slice(i + 1, j);
        i = (j < s.length) ? j + 1 : j;
        return new String(lit);
      }
      const m = /^[A-Za-z_][A-Za-z0-9_.]*/.exec(s.slice(i));
      if (m) {
        i += m[0].length;
        const name = m[0].toLowerCase();
        if (eat('(')) {                       // math.xxx(...)
          const args = [];
          if (!peek(')')) { do { args.push(ternary()); } while (eat(',')); }
          eat(')');
          switch (name) {
            case 'math.min': return Math.min(...args);
            case 'math.max': return Math.max(...args);
            case 'math.abs': return Math.abs(args[0]);
            case 'math.clamp': return Math.min(Math.max(args[0], args[1]), args[2]);
            case 'math.sin': return Math.sin(args[0] * DEG);
            case 'math.cos': return Math.cos(args[0] * DEG);
            case 'math.floor': return Math.floor(args[0]);
            case 'math.round': return Math.round(args[0]);
            case 'math.sqrt': return Math.sqrt(args[0]);
            case 'math.pow': return Math.pow(args[0], args[1]);
            case 'math.mod': return args[0] % args[1];
            case 'math.lerp': return args[0] + (args[1]-args[0]) * args[2];
            default: {
              // math 以外の関数呼び出し (ctrl.hold('mainhand', ':sword') 等) は
              // 「正規化した見出し」で vars を引く。呼び出し側は
              //   vars["ctrl.hold(mainhand,:sword)"] = 1
              // の形で与える。空白と引用符を落とすので、パック側の書き方の揺れ
              // (', ' か ',' か) に左右されない。
              const key = name + '(' + args.map((a) => String(a).trim()).join(',') + ')';
              const hit = vars[key];
              return typeof hit === 'number' ? hit : 0;
            }
          }
        }
        // math.* は関数呼び出しだけでなく定数としても現れる。上の分岐は eat('(') が
        // 前提なので、括弧を伴わない math.pi はここへ落ちてくる —— 変数表にも無いので
        // 0 になっていた。これは黙って効く: パックの parallel2 が
        //   v.L1_K1 = v.L1_C / math.pi / v.L1_F
        //   v.L1_K2 = 1 / math.pow(2 * math.pi * v.L1_F, 2)
        // の形でばね定数を導出しているため、math.pi が 0 だと 11 本のばね
        // (髪 / リボン / 胸の揺れもの、parallel3 が積分する) の定数が全て 0 になり、
        // 揺れもの物理が丸ごと死ぬ。
        if (name === 'math.pi') return Math.PI;
        if (name === 'math.e') return Math.E;
        const v = vars[name];
        return typeof v === 'number' ? v : 0;
      }
      const num = /^[0-9]*\.?[0-9]+/.exec(s.slice(i));
      if (num) { i += num[0].length; return parseFloat(num[0]); }
      i++;
      return 0;
    }
    function mul() {
      let v = primary();
      for (;;) { ws();
        if (eat('*')) v *= primary();
        else if (eat('/')) { const d = primary(); v = d === 0 ? 0 : v / d; }
        else return v;
      }
    }
    function add() {
      let v = mul();
      for (;;) { ws();
        if (peek('->')) return v;
        if (eat('+')) v += mul();
        else if (eat('-')) v -= mul();
        else return v;
      }
    }
    function cmp() {
      let v = add();
      ws();
      for (const op of ['<=', '>=', '==', '!=', '<', '>']) {
        if (eat(op)) {
          const r = add();
          switch (op) {
            case '<': return v < r ? 1 : 0;
            case '>': return v > r ? 1 : 0;
            case '<=': return v <= r ? 1 : 0;
            case '>=': return v >= r ? 1 : 0;
            // 文字列が絡む == / != は文字列として比べる。
            // **未設定の変数 (molang では 0 になる) は空文字として扱う** ——
            // パックは ctrl.parcool_state == '' の形で「その状態が無いこと」を書くので、
            // ここを数値の 0 のまま比べると条件が常に偽になり、その分岐のアニメが
            // 1 本も鳴らなくなる (2026-08-19 に実測: pre_main/jump が jump3 も jump も
            // 出せず、実機が混ぜている jump 系のブレンドを再現できていなかった)。
            case '==': return eqLoose(v, r) ? 1 : 0;
            case '!=': return eqLoose(v, r) ? 0 : 1;
          }
        }
      }
      return v;
    }
    function and() {
      let v = cmp();
      for (;;) { ws();
        if (eat('&&')) { const r = cmp(); v = (v && r) ? 1 : 0; }
        else return v;
      }
    }
    function or() {
      let v = and();
      for (;;) { ws();
        if (eat('||')) { const r = and(); v = (v || r) ? 1 : 0; }
        else return v;
      }
    }
    function ternary() {
      const c = or();
      ws();
      if (eat('?')) {
        const a = ternary();
        eat(':');
        const b = ternary();
        return c ? a : b;
      }
      return c;
    }
    /**
     * molang の {@code ==} / {@code !=}。片側でも文字列なら文字列として比べ、
     * そのとき数値の {@code 0} (=未設定の変数) は空文字とみなす。
     * 両側とも数値なら従来どおり厳密比較。
     */
    function eqLoose(a, b) {
      const aS = typeof a === 'object', bS = typeof b === 'object';
      if (!aS && !bS) return a === b;
      const norm = (x) => (typeof x === 'object' ? String(x) : (x === 0 ? '' : String(x)));
      return norm(a) === norm(b);
    }

    try { return ternary(); } catch { return 0; }
  }

  // ===========================================================================
  // アニメーション
  // ===========================================================================
  /** キーフレームの生値を [x,y,z] に均す。数値 1 個 / 配列 / {pre,post} のいずれも来る。 */
  function vec3(v) {
    if (v == null) return null;
    if (typeof v === 'number') return [v, v, v];
    if (typeof v === 'string') return [v, v, v];
    if (Array.isArray(v)) return [v[0] ?? 0, v[1] ?? 0, v[2] ?? 0];
    if (typeof v === 'object') {
      const inner = v.post || v.pre || v.vector;
      return inner ? vec3(inner) : null;
    }
    return null;
  }

  /**
   * {@code parallel*} 系が<b>無条件に</b> {@code scale:0} で隠しているボーンを集める。
   *
   * <p><b>条件付きで隠れているものは対象外。</b> かつては変数を空で評価して 0 なら消していたが、
   * それは「今の変数値では隠れている」だけで「決して出ない」ではない。消すとジオメトリから
   * 頂点ごと失われ、<b>実行時にどう変数を与えても二度と出せなくなる</b>。
   *
   * <p>実害 (2026-08-20 実測): 変数依存で隠れている 220 ボーンが消えていた ——
   * Eyes2/Eyes5/Eyes7 (既定以外の目)、mad2/OpenMouth8 (既定以外の口)、
   * Gohei/Gohei3/baijian (武器) など。そのため v.roaming.yan=4 を与えても Eyes5 の面が
   * 存在せず、**霊夢が白目に見えていた**。御幣が出なかったのも同じ理由。
   *
   * <p>呼び出し側で書くと数値と配列の場合分けを毎回間違える (実際に間違えた) ので、
   * 判定はここに閉じ込める。子孫は行列で潰れるが、生成しないほうが速いので
   * {@link buildGeometry} 側で親をたどって除外する。
   */
  function collectHidden(anims) {
    const hidden = new Set();
    // **変数に依存して隠れているボーンは消してはいけない。**
    const conditional = new Set();
    for (const name of Object.keys(anims)) {
      if (!/^(pre_)?parallel/.test(name)) continue;
      const bones = anims[name].bones || {};
      for (const [bn, ch] of Object.entries(bones)) {
        if (ch.scale === undefined) continue;
        // 式に変数が出てくるなら、隠れているのは**今の変数値では**という話にすぎない。
        // ジオメトリから消すと、実行時にどう変数を与えても二度と出せなくなる。
        if (/[vq].[A-Za-z_]|ysm.|query./.test(JSON.stringify(ch.scale))) {
          conditional.add(bn);
          continue;
        }
        const s = sampleChannel(ch.scale, 0, null, {});
        if (s && Math.abs(s[0]) < 1e-6 && Math.abs(s[1]) < 1e-6 && Math.abs(s[2]) < 1e-6) {
          hidden.add(bn);
        }
      }
    }
    // **どこかのアニメが出しうるボーンは消さない。** collectHidden は下地 (parallel 系)
    // しか見ないが、出し直すのは下地の外であることがある —— 御幣は pre_parallel0 が
    // リテラル 0 で隠し、hold_mainhand:sword1 が 1-v.roaming.jian で出し直す
    // (霊夢が剣を持つと YSM は御幣を代わりに描く、というパックの設計)。
    // 下地だけを見て消すと、この出し直しが効かなくなる。
    for (const a of Object.values(anims)) {
      for (const [bn, ch] of Object.entries((a && a.bones) || {})) {
        if (ch.scale === undefined || !hidden.has(bn)) continue;
        const raw = JSON.stringify(ch.scale);
        if (/[vq].[A-Za-z_]|ysm.|query./.test(raw)) { hidden.delete(bn); continue; }
        const v = sampleChannel(ch.scale, 0, null, {});
        if (!v || Math.abs(v[0]) > 1e-6 || Math.abs(v[1]) > 1e-6 || Math.abs(v[2]) > 1e-6) hidden.delete(bn);
      }
    }
    for (const bn of conditional) hidden.delete(bn);
    return hidden;
  }

  /**
   * 1 チャンネル (rotation / position / scale) を時刻 t 秒で評価する。
   * 定数・キーフレーム表のどちらも来る。値が molang 文字列なら評価する。
   */
  function sampleChannel(ch, t, lengthSec, vars) {
    if (ch == null) return null;
    if (Array.isArray(ch) || typeof ch === 'number' || typeof ch === 'string') {
      const v = vec3(ch);
      return v ? v.map((x) => molangNum(x, vars)) : null;
    }
    if (typeof ch !== 'object') return null;

    // **キー文字列をそのまま持ち回す。** 以前は Object.keys を Number へ潰してから
    // String(t0) で引き直していたが、キーが "0.0" / "1.0" のとき String(Number("0.0"))
    // は "0" になり**元のキーへ戻れない**。引けなかったキーフレームは undefined →
    // vec3(undefined) が null → [0,0,0] として扱われ、そこへ向かって補間されていた。
    //
    // 実害 (2026-08-19 ににーくらが発見): extra95 の AllBody は
    //   {"0.0":[1,1,1], "1.0":[1,1,1], "3.75":[1,1,1]}   ← 常に等倍
    // なのに t=0〜1 で 0.00、t=2 で 0.36、t=3 で 0.73 と評価され、**夢想封印中に
    // 霊夢が消えてから徐々に大きくなる**という症状になっていた
    // (0.36 = (2-1)/(3.75-1) と算術まで一致した)。
    // 回転・位置・スケールすべてに効くので、"0.0" のようなキーを持つアニメは全部壊れていた。
    const entries = Object.keys(ch)
      .map((k) => [Number(k), k])
      .filter((e) => !Number.isNaN(e[0]))
      .sort((a, b) => a[0] - b[0]);
    const times = entries.map((e) => e[0]);
    if (!times.length) {
      const v = vec3(ch);
      return v ? v.map((x) => molangNum(x, vars)) : null;
    }
    let tt = t;
    if (lengthSec && lengthSec > 0) tt = t % lengthSec;
    // 区間を探す
    let i = 0;
    while (i < times.length - 1 && times[i + 1] <= tt) i++;
    const j = Math.min(i + 1, entries.length - 1);
    const t0 = times[i], t1 = times[j];
    const k0 = ch[entries[i][1]], k1 = ch[entries[j][1]];
    // 区間の出口は post、入口は pre を使う (bedrock の段差表現)
    const a = (vec3(k0 && k0.post ? k0.post : k0) || [0,0,0]).map((x) => molangNum(x, vars));
    const b = (vec3(k1 && k1.pre ? k1.pre : k1) || a).map((x) => molangNum(x, vars));
    if (t1 === t0) return a;
    const f = Math.max(0, Math.min(1, (tt - t0) / (t1 - t0)));
    return [a[0] + (b[0]-a[0])*f, a[1] + (b[1]-a[1])*f, a[2] + (b[2]-a[2])*f];
  }

  function molangNum(v, vars) {
    return typeof v === 'number' ? v : molang(v, vars || {});
  }

  /**
   * アニメを 1 本、時刻 t 秒で評価してボーンごとの差分を返す。
   * @returns {Map<string,{r:number[],p:number[],s:number[]}>}
   */
  function sampleAnimation(anim, t, vars) {
    const out = new Map();
    if (!anim || !anim.bones) return out;
    const len = anim.animation_length || 0;
    const loop = anim.loop === true || anim.loop === 'loop';
    const tt = (loop && len > 0) ? (t % len) : Math.min(t, len || t);
    for (const [bn, ch] of Object.entries(anim.bones)) {
      const r = sampleChannel(ch.rotation, tt, loop ? len : 0, vars);
      const p = sampleChannel(ch.position, tt, loop ? len : 0, vars);
      const s = sampleChannel(ch.scale, tt, loop ? len : 0, vars);
      if (r || p || s) out.set(bn, { r, p, s });
    }
    return out;
  }

  /**
   * ボーンの world 行列を積む。アニメの差分は rest の上に載せる。
   *
   * <p>符号は Java 版モデル空間 (Y が下向き) に合わせる:
   * 回転は X/Y を反転、位置は Y を反転。これは bedrock -> Java の変換と同じ向き。
   *
   * @param layers 適用するアニメの評価結果。後のものが優先 (回転/位置は加算、scale は乗算)
   * @returns {Float32Array} bones.length * 16
   */
  /**
   * **衣装ボーン** = scale が v.roaming.* の式で決まるボーン。
   *
   * <p>にーくら 2026-08-25:「指定していないということは、何もしていないときの molang を
   * 維持するという意味」。衣装は<b>状態</b>であってアニメの出力ではない。
   *
   * <p>実測 (2026-08-25): 攻撃アニメは衣装ボーンへ scale キーフレームを直接撃っている
   * (extra 94 件 / main 45 件 / tlm 22 件 / tac 16 件 / slashblade 5 件)。待機中は
   * v.roaming.* の式だけで決まるので実機と完全一致する (E-0: 隠れボーン 49 本が差分 0)
   * のに、技へ入った瞬間にアニメの scale が勝って服が崩れていた。
   */
  function collectCostumeBones(anims) {
    const out = new Set();
    // **実測で数え上げた 13 種** (2026-08-25、実モデルの animations/*.json の scale 式に
    // 実際に出てくる v.roaming.*): wazi 72本 / shoutao 40 / zui 23 / yantong 16 /
    // xiezi 15 / shangyi 12 / bianzi 12 / jian 10 / naian 10 / qianfa 9 / yan 9 /
    // maozi 6 / qunzi 6。手で 7 種だけ書いたときは取りこぼした —— **数えてから書く。**
    // **服だけ。** 接頭辞で v.roaming.* を一括りにしたら 264 本になり、目(yan/yantong)・
    // 口(zui)・髪(bianzi/qianfa)・武器(jian) まで巻き込んだ (2026-08-25 の実測で発覚)。
    // それらは**変わるのが正しい** —— 顔は待機/戦闘で mod が切り替える。
    // 服 = 身に着けている衣類だけに限る:
    //   shangyi 上衣 / qunzi 裙 / shoutao 手袋 / wazi 靴下 / xiezi 靴 /
    //   weijin マフラー / kouzhao マスク / maozi 帽子 / naian
    const RE = /v\.roaming\.(shangyi|qunzi|shoutao|wazi|xiezi|weijin|kouzhao|maozi|naian)\b/;
    for (const a of Object.values(anims || {})) {
      for (const [bn, ch] of Object.entries((a && a.bones) || {})) {
        if (ch.scale === undefined) continue;
        if (RE.test(JSON.stringify(ch.scale))) out.add(bn);
      }
    }
    return out;
  }

  function poseBones(bones, layers, opts) {
    const out = new Float32Array(bones.length * 16);
    const tmp = new Float32Array(16);
    for (let i = 0; i < bones.length; i++) {
      const b = bones[i];
      let rx = b.r[0], ry = b.r[1], rz = b.r[2];
      let tx = b.t[0], ty = b.t[1], tz = b.t[2];
      let sx = 1, sy = 1, sz = 1;
      for (const Lraw of layers) {
        // 層は Map そのもの (重み 1) か {map, weight} のどちらでもよい。
        // animation controller の blend_transition を再現するために重みが要る
        // ——遷移直後は出ていく状態と入ってくる状態がクロスフェードするので、
        // 全重みで足すと「混ぜすぎ」になる (2026-08-19 実測: jump3 を全重みで足すと
        // 誤差が 0.1117 -> 0.1943 と悪化した)。
        const L = (Lraw && Lraw.map) ? Lraw.map : Lraw;
        const w = (Lraw && Lraw.map) ? Lraw.weight : 1;
        // **scale は別の重みを使う。** このパックは scale=0 を「そのボーンを消す」意味で
        // 使っており (hold_mainhand:sword1 が baijian を消す、bow が 2 本消す、run_1 も 1 本)、
        // 表示の ON/OFF は二値なので混ぜてはならない。
        // 重み 0.45 を scale にも掛けると scale=0 が 0.55 になり、**消えるはずの剣が
        // 小さく表示される** (2026-08-19 ににーくらが実機比較で発見)。
        // scaleWeight は「本物のクロスフェード (blend_transition) の分だけ」を受け取り、
        // 当てはめ定数 (CONTROLLER_WEIGHT_FIT) は掛からない。
        const ws = (Lraw && Lraw.map && Lraw.scaleWeight !== undefined) ? Lraw.scaleWeight : w;
        // **衣装ボーンの scale はアニメ層から取らない。**「指示されていないものは動かさない」
        // (にーくら 2026-08-25)。状態の式 (下地の parallel 系) だけが衣装を決める。
        // 下地は生の Map で来る (Lraw.map を持たない) ので、そこだけ通す。
        const pinScale = !!(opts && opts.pinScale && Lraw && Lraw.map && opts.pinScale.has(b.name));
        // mode: 'add' (既定) = 静止姿勢の上に差分を足す / 'set' = 静止姿勢+アニメ値へ
        // 重み w で寄せる (それまでの層の寄与を上書きする)。
        //
        // **どちらが正しいかはパックと層の種類による。** 下地 parallel 系は微小な補正を
        // 重ね合わせるので 'add' が正しい。一方 animation controller が選ぶ状態アニメと
        // mod が名指しするアニメは、どちらも「静止姿勢からの絶対的な姿勢」を書いている
        // 可能性が高く、その場合 'add' だとオフセットが二重にかかる (2026-08-19 実測:
        // コントローラの層を 'add' で足すと誤差が悪化した)。切り替えられるようにして
        // **測って決める**ためのもの。
        const mode = (Lraw && Lraw.map) ? (Lraw.mode || 'add') : 'add';
        if (!L || w === 0) continue;
        const d = L.get(b.name);
        if (!d) continue;
        if (mode === 'set') {
          if (d.r) {
            rx += (b.r[0] + -d.r[0]*DEG - rx) * w;
            ry += (b.r[1] + -d.r[1]*DEG - ry) * w;
            rz += (b.r[2] + d.r[2]*DEG - rz) * w;
          }
          if (d.p) {
            tx += (b.t[0] + d.p[0]/16 - tx) * w;
            ty += (b.t[1] + -d.p[1]/16 - ty) * w;
            tz += (b.t[2] + d.p[2]/16 - tz) * w;
          }
          if (!pinScale && d.s) { sx += (d.s[0]-sx)*ws; sy += (d.s[1]-sy)*ws; sz += (d.s[2]-sz)*ws; }
          continue;
        }
        // **回転は符号を反転しない。** かつて X/Y を反転していたが、animsweep で録った
        // 実機の記録 (316本のアニメ) に対して総当たりしたところ、符号 (1,1,1) が
        // 順序に関係なく上位を独占した (2026-08-19、45本×2フレーム=90点で判定):
        //   zyx (1,1,1)    0.0943   ← 最良
        //   zyx (-1,-1,1)  0.1602   ← 旧実装。順位 29/48、69.9% 悪い
        // 順序 (zyx) と位置の符号 (1,-1,1) は元のままが最良だったので、変えたのは回転の符号だけ。
        //
        // **なぜ今まで気づけなかったか**: それまでの記録は「ほぼ静止した4.8秒」しか無く、
        // 三軸に大きな回転がかかる姿勢が入っていなかったので、順序も符号も差が1.3%しか出ず
        // 判別できなかった。全アニメを一巡して録る animsweep (にーくら案) が初めてこれを可能にした。
        if (d.r) { rx += d.r[0]*DEG*w; ry += d.r[1]*DEG*w; rz += d.r[2]*DEG*w; }
        if (d.p) { tx += d.p[0]/16*w; ty += -d.p[1]/16*w; tz += d.p[2]/16*w; }
        // **scale は乗算ではなく「後勝ちの上書き」。** このパックは
        //   pre_parallel0 : Gohei / Gohei3 の scale = 0   (既定で隠す)
        //   hold_mainhand:sword1 : Gohei  scale = 1-v.roaming.jian  (出し直す)
        //   hold_offhand:sword   : Gohei3 scale = 1-v.roaming.jian  (出し直す)
        //   extra24/43/44/52 …  : Gohei3 scale = 1
        // という「既定で隠して必要なアニメで出し直す」設計で書かれている。
        // 乗算だと pre_parallel0 が 0 にした時点で二度と戻らず、**霊夢の御幣が永久に
        // 消える** (2026-08-19 実測: 記録には Gohei3 の固有 UV 矩形が 126/126 写っている
        // のに Viewer は出していなかった)。
        // 重み ws は「新しい値へどれだけ寄せるか」。ws=1 で完全な上書き、ws=0 で無視。
        if (!pinScale && d.s) { sx += (d.s[0]-sx)*ws; sy += (d.s[1]-sy)*ws; sz += (d.s[2]-sz)*ws; }
      }
      let m = M.trans(tx, ty, tz);
      if (rz) m = M.mul(m, M.rotZ(rz));
      if (ry) m = M.mul(m, M.rotY(ry));
      if (rx) m = M.mul(m, M.rotX(rx));
      if (sx !== 1 || sy !== 1 || sz !== 1) m = M.mul(m, M.scale(sx, sy, sz));
      if (b.parent >= 0) {
        const p = out.subarray(b.parent*16, b.parent*16 + 16);
        M.mul(p, m, tmp);
        out.set(tmp, i*16);
      } else {
        out.set(m, i*16);
      }
    }
    return out;
  }

  /**
   * palette (9 float/ボーン、pal0=回転rad/pal1=位置/pal2=scale。pal3 は無い) から
   * ボーン行列を組み立てる (14-01)。
   *
   * <p><b>`.planning/spikes/004-ysm-bone-map-probe/analysis/condition6.mjs:123-148` から
   * 検証済みの符号・軸規約を verbatim に移植したもの</b> —— 3 回の審査で確定した規約を
   * 再導出しない。変更したのは palette の添字だけ (ワイヤ形式に pal3 が無いので stride
   * 12 → 9)。乗算順序 `T * Rz * Ry * Rx * S` も変えない。
   *
   * <p>{@code slotOf} は `<stamp>.pal.json` の {@code names[slot] = ボーン名} から作った
   * 逆引き {@code Map<name, slot>}。Viewer のボーン番号 (親優先で振り直したもの) と
   * palette slot は 1058/1058 食い違うので、これが両者を繋ぐ唯一の橋になる
   * (実測: MiMa 27/0, Head 156/256, LeftForeArm2 661/764)。
   *
   * @param bones  {@link #buildGeometry} が返す `geo.bones` (親が先に来る並び)
   * @param pal9   この tick の palette (Float32Array、長さ `bones.length_理論値` ではなく
   *               索引の `bones * 9`。ボーン番号ではなく slot 番号で引く)
   * @param slotOf `Map<string, number>` (ボーン名 -> palette slot)
   * @returns {{mats: Float32Array, missing: number}} mats は `bones.length * 16` (列優先
   *          mat4 を4テクセルずつ、poseBones と同じ形 —— そのまま boneTex へ upload できる)。
   *          missing は slot が解決できなかったボーン数 (0 でなければ半端な remap なので
   *          呼び出し側は描画してはならない)
   */
  function matsFromPalette(bones, pal9, slotOf) {
    const COMPS = 9;
    const out = new Float32Array(bones.length * 16), tmp = new Float32Array(16);
    let missing = 0;
    for (let i = 0; i < bones.length; i++) {
      const b = bones[i];
      const s = slotOf.get(b.name);
      let rx, ry, rz, tx, ty, tz, sx, sy, sz;
      if (s === undefined) {
        missing++;
        rx = b.r[0]; ry = b.r[1]; rz = b.r[2]; tx = b.t[0]; ty = b.t[1]; tz = b.t[2]; sx = sy = sz = 1;
      } else {
        const o = s * COMPS;
        rx = -pal9[o]; ry = -pal9[o + 1]; rz = pal9[o + 2];
        tx = b.t[0] + pal9[o + 3] / 16; ty = b.t[1] - pal9[o + 4] / 16; tz = b.t[2] + pal9[o + 5] / 16;
        sx = pal9[o + 6]; sy = pal9[o + 7]; sz = pal9[o + 8];
      }
      let m = M.trans(tx, ty, tz);
      if (rz) m = M.mul(m, M.rotZ(rz));
      if (ry) m = M.mul(m, M.rotY(ry));
      if (rx) m = M.mul(m, M.rotX(rx));
      if (sx !== 1 || sy !== 1 || sz !== 1) m = M.mul(m, M.scale(sx, sy, sz));
      if (b.parent >= 0) {
        M.mul(out.subarray(b.parent * 16, b.parent * 16 + 16), m, tmp);
        out.set(tmp, i * 16);
      } else {
        out.set(m, i * 16);
      }
    }
    return { mats: out, missing };
  }

  // ===========================================================================
  // molang の「文」と timeline (quick 260819)
  // ---------------------------------------------------------------------------
  // Bedrock の animation は bones (見た目) のほかに timeline を持てる。timeline は
  // 「その時刻に実行する molang の文」で、このパックはそこに**ばねの積分器**を書いている
  // (parallel3: 11 本のばね = 髪 / リボン / 胸の揺れもの。parallel2 がその定数を敷く)。
  //
  //   [0]      v.L1_P1    = v.L1_P0 + 0.01 * v.L1_P0dot;
  //   [0]      v.L1_P1dot = v.L1_P0dot + 0.01*(v.L1_K3*math.clamp(q.vertical_speed,-30,1)
  //                                            - v.L1_P1 - v.L1_K1*v.L1_P0dot)/v.L1_K2;
  //   [0.0101] v.L1_P0    = v.L1_P1;
  //
  // molang() は式しか評価しないので、代入と文の並びはここで扱う。**状態は vars に残る**
  // ——呼び出し側が同じ vars を tick 間で持ち回すことで積分が進む。毎 tick 作り直すと
  // ばねは永久に静止したままになる (それが 2026-08-19 時点の gl.js の状態)。
  // ===========================================================================

  /**
   * molang の文列 ({@code a=expr; b=expr;}) を実行し、代入結果を {@code vars} へ書く。
   *
   * <p>代入以外の文 (裸の文字列リテラル = このパックでは中国語の注釈) は読み飛ばす。
   * {@code ==} {@code <=} {@code >=} {@code !=} は代入と誤認しない。
   *
   * @param text 1 文以上。{@code ;} 区切り
   * @param vars 変数表 (小文字キー)。**破壊的に更新する**
   * @param subs 事前置換 (例 {@code {"query.position_delta(0)": 0.5}})。molang が
   *             引数付き query を解さないので、呼び出し側が値を差し込むための逃げ道
   */
  function molangStatements(text, vars, subs) {
    for (let piece of String(text).split(';')) {
      piece = piece.trim();
      if (!piece) continue;
      if (piece[0] === "'" || piece[0] === '"') continue;      // 注釈
      const eq = piece.indexOf('=');
      if (eq <= 0) continue;
      if ('<>!=+-*/'.indexOf(piece[eq - 1]) >= 0) continue;     // <= >= != == += など
      if (piece[eq + 1] === '=') continue;
      const lhs = piece.slice(0, eq).trim().toLowerCase();
      let rhs = piece.slice(eq + 1).trim();
      if (subs) for (const k in subs) rhs = rhs.split(k).join('(' + subs[k] + ')');
      vars[lhs] = molang(rhs, vars);
    }
    return vars;
  }

  /**
   * {@code anim.timeline} を**時刻の昇順で**すべて実行する。1 回の呼び出しが
   * 積分の 1 ステップに相当する (このパックの dt は 0.01)。
   *
   * <p>timeline が無いアニメは何もしない。時刻を跨いだ順序が意味を持つ
   * (parallel3 は [0] で次の値を計算し [0.0101] で確定する) ので、必ず昇順で回すこと。
   */
  function runTimeline(anim, vars, subs) {
    if (!anim || !anim.timeline) return vars;
    const times = Object.keys(anim.timeline).sort((a, b) => parseFloat(a) - parseFloat(b));
    for (const t of times) {
      const body = anim.timeline[t];
      const list = Array.isArray(body) ? body : [body];
      for (const line of list) molangStatements(line, vars, subs);
    }
    return vars;
  }
  // ===========================================================================
  // animation controller の状態機械 (2026-08-19)
  // ---------------------------------------------------------------------------
  // YSM は「mod が名指しした 1 本」だけを再生しているのではない。
  // controller/parallel_controllers.json の状態機械が**エンティティの状態に応じて層を
  // 選び、加算ブレンドする**。これを回さないと実機と一致しない。
  //
  // 実測 (2026-08-19、302本×位相4種の総当たり): 姿勢トレースの tick48 に extra79 を
  // 足すと誤差が 70.1% 減り、jump / jump2 を足すと約 60% 減る。後者は CLAUDE.md の
  // 判例「霊夢は仕様上わずかに浮く → ctrl.jump=true → jump/jump2/jump3 が加算ブレンド」
  // と一致する —— 実機は混ぜており、この Viewer は混ぜていなかった。
  //
  // 入力 (呼び出し側が vars へ入れる):
  //   ctrl.idle / ctrl.walk / ctrl.run / ctrl.fly / ctrl.jump / ctrl.sneak /
  //   ctrl.sneaking / ctrl.sit / ctrl.sleep / ctrl.parcool_state
  //   ctrl.hold(mainhand,:sword) の形の見出し (molang の関数呼び出しはここへ落ちる)
  //   q.all_animations_finished / query.any_animation_finished / query.is_riding
  //   v.idle / v.jumped / v.swing_sword / v.attack / v.wuqi / v.no_hold / v.night ほか
  // ===========================================================================

  /**
   * コントローラ定義から実行状態を作る。返り値を {@link stepControllers} へ渡し続ける。
   *
   * @param json {@code controller/parallel_controllers.json} をパースしたもの
   */
  function initControllers(json) {
    const defs = (json && json.animation_controllers) || {};
    const cur = {}, elapsed = {};
    for (const name in defs) {
      const d = defs[name];
      cur[name] = d.initial_state || Object.keys(d.states || {})[0] || null;
      elapsed[name] = 0;
    }
    return { defs, cur, elapsed, prev: {} };
  }

  /** {@code animations} の 1 要素から、条件を満たすアニメ名を取り出す。 */
  function pickAnims(list, vars, out) {
    for (const item of (list || [])) {
      if (typeof item === 'string') { out.push(item); continue; }
      if (item && typeof item === 'object') {
        for (const nm in item) {
          const cond = item[nm];
          // 条件が無い / 空文字は常に真。数値・式は molang で評価する。
          if (cond === undefined || cond === '' || molang(cond, vars)) out.push(nm);
        }
      }
    }
    return out;
  }

  /**
   * 全コントローラを 1 ステップ進め、**この瞬間に再生されているアニメの一覧**を返す。
   *
   * <p>遷移は定義順に評価し、**最初に真になったものを採る** (Bedrock と同じ)。
   * 遷移したら {@code on_exit} の文を実行し (molang の代入。{@code v.attack} の
   * 回し方などがここに書かれている)、その状態の経過時間を 0 に戻す。
   *
   * <p>ブレンド重み ({@code blend_transition} / {@code blend_transitions}) は**まだ
   * 扱っていない** —— 返すのは「鳴っているか否か」だけ。遷移直後の混ざり具合が
   * 必要になったらここを拡張する。
   *
   * @param ctl  {@link initControllers} の返り値。**破壊的に更新する**
   * @param vars 変数表 (小文字キー)。{@code on_exit} の代入がここへ書かれる
   * @param dt   経過秒 (1 tick なら 0.05)
   * @returns {Array<{controller:string,state:string,anim:string,elapsed:number}>}
   */
  /**
   * 出ていく状態の重み。{@code blend_transitions} (時刻→重みのカーブ) があればそれを線形補間、
   * 無ければ {@code blend_transition} (秒) で 1→0 の直線、どちらも無ければ即座に 0 (瞬時切替)。
   *
   * @param st 出ていく状態の定義
   * @param t  遷移からの経過秒
   */
  function blendWeight(st, t) {
    if (!st) return 0;
    const curve = st.blend_transitions;
    if (curve) {
      const ks = Object.keys(curve).map(parseFloat).sort((a, b) => a - b);
      if (!ks.length) return 0;
      if (t <= ks[0]) return curve[Object.keys(curve)[0]];
      const last = ks[ks.length - 1];
      if (t >= last) return 0;
      for (let i = 1; i < ks.length; i++) {
        if (t <= ks[i]) {
          const a = ks[i - 1], b = ks[i];
          const va = curve[keyOf(curve, a)], vb = curve[keyOf(curve, b)];
          const f = (b === a) ? 0 : (t - a) / (b - a);
          return va + (vb - va) * f;
        }
      }
      return 0;
    }
    const dur = st.blend_transition;
    if (typeof dur !== 'number' || dur <= 0) return 0;
    return t >= dur ? 0 : 1 - t / dur;
  }

  /** {@code blend_transitions} のキーは "0.005600" のような文字列。数値から元のキーを引く。 */
  function keyOf(curve, num) {
    for (const k of Object.keys(curve)) {
      if (parseFloat(k) === num) return k;
    }
    return String(num);
  }

  /**
   * animation controller が選ぶ層に掛ける重みの、実測で当てはめた既定値
   * (2026-08-19、`20260819-043059` の全94tickで検証)。
   *
   * <p><b>これは「まだ理解できていないこと」を数値で埋め合わせている定数である。</b>
   * 実機は mod が名指しするアニメとコントローラの層を、こちらの `poseBones` の
   * 単純加算とは違う形で合成しているらしく、コントローラ層を<b>全重みで足すと混ぜすぎになる</b>。
   *
   * <p>実測 (`ctrl.jump = !onGround`、94tickでの誤差比。1.0未満で改善):
   * <pre>
   *   倍率 0.00 → 1.000 (層なし)      改善 0 / 悪化 0
   *   倍率 0.15 → 0.958               改善 61 / 悪化 7
   *   倍率 0.30 → 0.930               改善 63 / 悪化 10
   *   倍率 0.45 → 0.917  ← 最良        改善 68 / 悪化 13
   *   倍率 0.60 → 0.923               改善 68 / 悪化 14
   *   倍率 1.00 → 1.008               改善 57 / 悪化 27
   * </pre>
   *
   * <p><b>合成の正しい規則が判ったら、この定数は消えるべきである。</b>
   * 消えないまま残っているなら、それは「まだ判っていない」という印。
   */
  const CONTROLLER_WEIGHT_FIT = 0.45;

  /**
   * @param opts {@code {weightScale}} —— コントローラ層に掛ける倍率。既定 1 (素の意味論)。
   *             実機に寄せたいときは {@link CONTROLLER_WEIGHT_FIT} を渡す。
   *             <b>既定を 1 のままにしてあるのは、当てはめ定数をライブラリの既定へ
   *             埋め込まないため</b> —— 使う側が「当てはめを使っている」と自覚できるようにする。
   */
  function stepControllers(ctl, vars, dt, opts) {
    const scale = (opts && typeof opts.weightScale === 'number') ? opts.weightScale : 1;
    const active = [];
    for (const name in ctl.defs) {
      const def = ctl.defs[name];
      const states = def.states || {};
      let sName = ctl.cur[name];
      let st = states[sName];
      if (!st) { active.length === 0; continue; }
      // 遷移を評価する (定義順、最初に真になったもの)
      let moved = null;
      for (const tr of (st.transitions || [])) {
        for (const target in tr) {
          if (molang(tr[target], vars)) { moved = target; break; }
        }
        if (moved) break;
      }
      if (moved && states[moved]) {
        for (const line of (st.on_exit || [])) molangStatements(line, vars);
        // 出ていく状態を控える。blend_transition のあいだ鳴り続けて減衰する。
        ctl.prev = ctl.prev || {};
        ctl.prev[name] = { state: sName, def: st, t: 0, elapsed: ctl.elapsed[name] };
        ctl.cur[name] = moved;
        ctl.elapsed[name] = 0;
        sName = moved;
        st = states[moved];
      } else {
        ctl.elapsed[name] += dt;
      }

      // 出ていく状態の減衰
      let outW = 0;
      const pv = ctl.prev && ctl.prev[name];
      if (pv) {
        pv.t += dt;
        pv.elapsed += dt;
        outW = blendWeight(pv.def, pv.t);
        if (outW <= 0) {
          delete ctl.prev[name];
        } else {
          for (const a of pickAnims(pv.def.animations, vars, [])) {
            active.push({ controller: name, state: pv.state, anim: a, elapsed: pv.elapsed,
              weight: outW * scale, scaleWeight: outW });
          }
        }
      }
      // 入ってくる (=現在の) 状態は、出ていく分の残りを受け取る
      const inW = 1 - outW;
      if (inW > 0) {
        for (const a of pickAnims(st.animations, vars, [])) {
          active.push({ controller: name, state: sName, anim: a, elapsed: ctl.elapsed[name],
            weight: inW * scale, scaleWeight: inW });
        }
      }
    }
    return active;
  }
  root.YSM = {
    collectCostumeBones,
    M, DEG, buildGeometry, molang, molangNum, molangStatements, runTimeline,
    initControllers, stepControllers, blendWeight, CONTROLLER_WEIGHT_FIT,
    collectHidden, sampleChannel, sampleAnimation, poseBones, matsFromPalette,
    VERTEX_ORDER, CORNERS,
  };

})(typeof window !== 'undefined' ? window : globalThis);
