/* =============================================================================
   SimLab — WebGL レンダラ (「実機」モード)
   -----------------------------------------------------------------------------
   モブの形は【自前で組み立てない】。Minecraft 自身に描かせて記録したものを貼るだけ。

     クライアントで  /tlmsim dumpmodels
       → SimVertexRecorder が実際の EntityRenderer の出力 (座標/UV/法線) を記録
       → simlab/models/<ns>/<path>.json
       → ここが /api/model?type=... で読んで、そのまま三角形として描く

   これにより Bedrock の pivot 規約・Y 反転・box UV の展開・面の巻き順を
   こちら側で再実装する必要がなくなる。自前実装だとモブが増えるたびに同種のバグを
   踏み直すことになる (ゾンビ 1 体で何度も踏んだ)。バニラも GeckoLib も YSM も同じ経路。

   記録時は向きを 0 に固定してある。MC のレンダラは rotY(180 - bodyYaw) を掛けるので、
   記録済みデータには 180° が入っている。実際の向きにするには rotY(-yaw) を足せばよい。
   ============================================================================= */
'use strict';

window.SimGL = (function () {

  /** 弾の見た目 (対応する *Renderer.java の写し)。弾はモデルではなくビルボード。 */
  const BULLETS = {
    'touhou_little_maid:musou_myouju_bullet': {
      textures: ['touhou_little_maid:textures/entity/reimu/myouju/red.png',
                 'touhou_little_maid:textures/entity/reimu/myouju/blue.png',
                 'touhou_little_maid:textures/entity/reimu/myouju/green.png'],
      halfSize: 1.44, frames: 7, frameTicks: 2,
    },
  };

  const BLOCK_TEX = {
    'minecraft:barrier': null,
    'minecraft:stone': 'minecraft:textures/block/stone.png',
    'minecraft:smooth_stone': 'minecraft:textures/block/smooth_stone.png',
    'minecraft:oak_planks': 'minecraft:textures/block/oak_planks.png',
  };

  // ===========================================================================
  // mat4 (列優先)
  // ===========================================================================
  const M = {
    ident: () => new Float32Array([1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]),
    mul(a, b) {
      const o = new Float32Array(16);
      for (let c = 0; c < 4; c++) for (let r = 0; r < 4; r++) {
        o[c*4+r] = a[r]*b[c*4] + a[4+r]*b[c*4+1] + a[8+r]*b[c*4+2] + a[12+r]*b[c*4+3];
      }
      return o;
    },
    persp(fovy, asp, near, far) {
      const f = 1 / Math.tan(fovy / 2), nf = 1 / (near - far);
      return new Float32Array([f/asp,0,0,0, 0,f,0,0, 0,0,(far+near)*nf,-1, 0,0,2*far*near*nf,0]);
    },
    trans(x, y, z) { const m = M.ident(); m[12]=x; m[13]=y; m[14]=z; return m; },
    scale(x, y, z) { const m = M.ident(); m[0]=x; m[5]=y; m[10]=z; return m; },
    rotY(a) { const c=Math.cos(a), s=Math.sin(a), m=M.ident(); m[0]=c; m[2]=-s; m[8]=s; m[10]=c; return m; },
    rotX(a) { const c=Math.cos(a), s=Math.sin(a), m=M.ident(); m[5]=c; m[6]=s; m[9]=-s; m[10]=c; return m; },
    // 死亡モーション(横に倒れる)用。実機 LivingEntityRenderer.setupRotations は
    // Axis.ZP.rotationDegrees(...) で**局所 Z 軸**まわりに回す。原点は足元なので、
    // 足を軸にして倒れる。rotX/rotY と対称。
    rotZ(a) { const c=Math.cos(a), s=Math.sin(a), m=M.ident(); m[0]=c; m[1]=s; m[4]=-s; m[5]=c; return m; },
  };
  const sub = (a, b) => [a[0]-b[0], a[1]-b[1], a[2]-b[2]];
  const cross = (a, b) => [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
  const dot = (a, b) => a[0]*b[0] + a[1]*b[1] + a[2]*b[2];
  const norm = (a) => { const l = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0]/l, a[1]/l, a[2]/l]; };

  // ===========================================================================
  // GL 基盤
  // ===========================================================================
  let gl = null, canvas = null;
  let progLine = null, progTex = null, progBB = null;
  // 直近の render() が GPU へ上げた view-projection 行列。
  // SimPick.viewProjection(cam,W,H) と一致することを lastVP() 経由で実行時に
  // 確認できる (床クリックが「絵と違う行列」を invert する事故は無音になるため)。
  let lastVP = null;
  const LOC = { pos: 0, uv: 1, nrm: 2, tint: 3, head: 4, col: 1, corner: 0 };
  const TEX_ATTRS = [{ loc: LOC.pos, n: 3 }, { loc: LOC.uv, n: 2 }, { loc: LOC.nrm, n: 3 }, { loc: LOC.tint, n: 3 }];
  const VSTRIDE = 11;  // SimVertexRecorder.STRIDE と一致させること
  const textures = new Map();
  const models = new Map();      // entity type -> {state, mesh, texId, quads}
  const meshes = { chamber: null, blocks: null };
  let currentKey = null;
  let status = '';
  // 描けなかったものの記録。**透明と「居ない」を同じ絵にしないため**(HANDOFF §1)。
  let missMesh = null, missBuf = null, missStatus = '';

  /* ===========================================================================
     被弾の赤 と 死亡モーション —— 記録を変えずに、実機と同じ見え方を作る

     水槽には「殴られたのに何も起きない」「死んだのに立ったまま消える」しか無かった
     (にーくら 2026-08-23「攻撃が被弾した際の赤くなる奴もない」「横に倒れながら赤くなるよね？」)。

     **記録に hurtTime / deathTime は無い。足す必要も無い** —— どちらも実機の規則が
     決まっているので、既に在るものから導ける:
       赤   … dmg 行(victim, t) から 10 tick (実機 hurtDuration=10, LivingEntity.java)
       倒れ … hp が 0 以下になった tick からの経過 (実機 deathTime 1→20 で削除)
     実測: 死んだモブは例外なく hp0 の 19〜20 tick 後に gone (5 体中 5 体) ——
     実機の deathTime の寿命と一致するので、倒れ切ったところで自然に消える。
     おかげで jar の変更も録り直しも要らず、**既に在る記録でもそのまま動く**。
     =========================================================================== */
  const DEATH_AT = new Map();   // id -> hp<=0 を最初に見た tick
  const SOMER_AT = new Map();   // id -> 宙返りが始まった tick (phys.somer が真になった最初)
  /* **経路によって回転の符号が変わる。** 実機の合成は
   *   trans · rotY(180-yaw) · [rotZ(倒れ) · rotX(宙返り)] · scale(-1,-1,1) · trans(0,-1.501,0)
   * で、skinned(ysm 再合成)経路はこれを 1 対 1 で再現している ⇒ そのままの符号でよい。
   * 一方、姿勢記録 と 汎用モデル の経路は rotY(-yaw) しか掛けない ——
   * つまり模型空間が実機に対して rotY(180)·scale(-1,-1,1) だけずれている。
   * X/Z 軸まわりの回転を 180 度の Y 回転で共役すると符号が反転する:
   *     rotY(180) · rotX(a) · rotY(-180) = rotX(-a)   (rotZ も同じ)
   * ⇒ **この 2 経路では倒れも宙返りも符号を反転させる。** 揃えないと、同じ霊夢が
   *   モデルの読み込み具合によって前に回ったり後ろに回ったりする。 */
  const MIRRORED = -1;          // rotY(-yaw) 系の経路に掛ける符号
  const SOMER_DEG = 36;         // 実機 EntityMaidRenderer.setupRotations: 36 度/tick
  const SOMER_MAX = 360;        // 1 回転で止まる
  const HURT_TICKS = 10;        // 実機 hurtDuration
  const DEATH_TICKS = 20;       // 実機 deathTime の寿命
  const FLASH_A = 0.70;         // 実機 OverlayTexture の RED = alpha 178/255

  /** その tick に殴られていた者たち。**1 フレームに 1 回だけ引く**(entity ごとに
   *  引くと O(体数 × 事象数) になる)。範囲問い合わせは store が既に公開している。 */
  function hurtMapAt(D, tick) {
    const m = new Map();
    const st = D && D.store;
    if (!st || !st.eventsInRange) return m;
    // [t-9, t] = 実機で hurtTime が 10→1 の 10 tick。ここに居れば赤い。
    for (const r of st.eventsInRange('dmg', tick - (HURT_TICKS - 1), tick)) {
      if (r && r.victim !== undefined) m.set(r.victim, r.t);
    }
    return m;
  }

  /**
   * 宙返りの角度[rad]。**実機と同じ式**(EntityMaidRenderer.setupRotations):
   *   角度 = min(経過tick × 36度, 360度) を局所 X 軸へ。
   * 起点は「phys.somer が真になった最初の tick」——死亡の DEATH_AT と同じ作り。
   * 記録は真偽だけ持ち、角度はここで導く(phys はデルタなので変化した tick には必ず行が出る)。
   */
  function somersaultRad(id, somer, tick, partial) {
    if (!somer) { SOMER_AT.delete(id); return 0; }
    let at = SOMER_AT.get(id);
    if (at === undefined || tick < at) { at = tick; SOMER_AT.set(id, at); }
    const el = Math.max(0, (tick + partial) - at);
    return Math.min(SOMER_MAX, el * SOMER_DEG) * Math.PI / 180;
  }

  /** この entity の「赤さ」と「倒れ角」。実機 LivingEntityRenderer と同じ式。 */
  function entityFx(e, p, tick, partial, hurt) {
    let dead = DEATH_AT.get(e.id);
    if (p && typeof p.hp === 'number') {
      // hp は前方フィルされるので、追従再生では「最初に 0 以下を見た tick」= 死んだ tick。
      if (p.hp > 0) { if (dead !== undefined) { DEATH_AT.delete(e.id); dead = undefined; } }
      else if (dead === undefined || tick < dead) { dead = tick; DEATH_AT.set(e.id, dead); }
    }
    let tilt = 0;
    if (dead !== undefined) {
      // 実機: f = sqrt((deathTime + partialTick - 1)/20 * 1.6) を 1 で頭打ち、× 90°。
      // deathTime は死んだ tick で 1 なので (deathTime + partial - 1) は経過そのもの。
      const el = Math.max(0, (tick + partial) - dead);
      const f = Math.min(1, Math.sqrt(el / DEATH_TICKS * 1.6));
      tilt = f * Math.PI / 2;
    }
    // 実機の条件は hurtTime>0 || deathTime>0 —— 死んでいる間はずっと赤い。
    const flash = (dead !== undefined || hurt.has(e.id)) ? FLASH_A : 0;
    return { flash, tilt };
  }

  /** 属性のロケーションは必ず固定する。自動割り当てだと aUV/aNrm が入れ替わって面が消える。 */
  function compile(vs, fs, attribs) {
    const p = gl.createProgram();
    for (const [type, src] of [[gl.VERTEX_SHADER, vs], [gl.FRAGMENT_SHADER, fs]]) {
      const s = gl.createShader(type);
      gl.shaderSource(s, src); gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
      gl.attachShader(p, s);
    }
    for (const [name, loc] of Object.entries(attribs)) gl.bindAttribLocation(p, loc, name);
    gl.linkProgram(p);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p));
    return p;
  }

  const VS_LINE = `#version 300 es
    in vec3 aPos; in vec4 aCol; uniform mat4 uVP; out vec4 vCol;
    void main(){ vCol=aCol; gl_Position=uVP*vec4(aPos,1.0); }`;
  const FS_LINE = `#version 300 es
    precision mediump float; in vec4 vCol; out vec4 o;
    void main(){ o=vCol; }`;
  const VS_TEX = `#version 300 es
    in vec3 aPos; in vec2 aUV; in vec3 aNrm; in vec3 aTint; in float aHead;
    uniform mat4 uVP; uniform mat4 uModel; uniform mat4 uHead;
    out vec2 vUV; out float vSh; out vec3 vTint;
    void main(){
      vUV=aUV; vTint=aTint;
      vec3 n=normalize(mat3(uModel)*aNrm);
      vSh=0.58+0.42*max(n.y,0.0)+0.14*max(abs(n.x),abs(n.z))-0.08*max(-n.y,0.0);
      vec3 p = aHead > 0.5 ? (uHead*vec4(aPos,1.0)).xyz : aPos;
      gl_Position=uVP*uModel*vec4(p,1.0);
    }`;
  const FS_TEX = `#version 300 es
    precision mediump float;
    in vec2 vUV; in float vSh; in vec3 vTint; uniform sampler2D uTex;
    uniform float uFlash; out vec4 o;
    void main(){
      vec4 t=texture(uTex,vUV);
      if(t.a<0.06) discard;
      // uFlash: 被弾/死亡の赤。実機は OverlayTexture の RED 行 = RGB(255,0,0) を
      // alpha 178/255(≈0.70) で重ねる (OverlayTexture.java の画素値から)。
      // 条件も実機と同じ「hurtTime>0 || deathTime>0」(LivingEntityRenderer.getOverlayCoords)。
      o=vec4(mix(t.rgb*vTint*vSh, vec3(1.0,0.0,0.0), uFlash),1.0);
    }`;
  const VS_BB = `#version 300 es
    in vec2 aCorner; in vec2 aUV;
    uniform mat4 uVP; uniform vec3 uCenter; uniform vec3 uRight; uniform vec3 uUp;
    uniform float uHalf; uniform float uSpin;
    out vec2 vUV;
    void main(){
      float c=cos(uSpin), s=sin(uSpin);
      vec2 p=vec2(aCorner.x*c-aCorner.y*s, aCorner.x*s+aCorner.y*c)*uHalf;
      vUV=aUV;
      gl_Position=uVP*vec4(uCenter+uRight*p.x+uUp*p.y,1.0);
    }`;
  const FS_BB = `#version 300 es
    precision mediump float;
    in vec2 vUV; uniform sampler2D uTex; uniform float uAlpha; uniform vec4 uFrame;
    out vec4 o;
    void main(){
      vec4 t=texture(uTex, vec2(uFrame.x+vUV.x*uFrame.z, uFrame.y+vUV.y*uFrame.w));
      o=vec4(t.rgb*t.a*uAlpha, t.a*uAlpha);
    }`;

  /* ---------------------------------------------------------------------------
     霊夢だけはボーンを動かして描く (焼いた三角形ではない)。
     ボーン行列は RGBA32F テクスチャに載せ、頂点シェーダが自分のボーン番号で引く。
     1058 ボーンぶんの行列を uniform に置くのは無理なので、テクスチャが唯一の現実解。
     --------------------------------------------------------------------------- */
  const VS_SKIN = `#version 300 es
    in vec3 aPos; in vec2 aUV; in vec3 aNrm; in float aBone;
    uniform mat4 uVP; uniform mat4 uModel; uniform sampler2D uBones;
    out vec2 vUV; out float vSh;
    mat4 boneMat(int b){
      return mat4(texelFetch(uBones, ivec2(0,b), 0), texelFetch(uBones, ivec2(1,b), 0),
                  texelFetch(uBones, ivec2(2,b), 0), texelFetch(uBones, ivec2(3,b), 0));
    }
    void main(){
      mat4 B = boneMat(int(aBone + 0.5));
      vec4 p = B * vec4(aPos, 1.0);
      vUV = aUV;
      vec3 n = normalize(mat3(uModel) * mat3(B) * aNrm);
      vSh = 0.58 + 0.42*max(n.y,0.0) + 0.14*max(abs(n.x),abs(n.z)) - 0.08*max(-n.y,0.0);
      gl_Position = uVP * uModel * p;
    }`;
  const FS_SKIN = `#version 300 es
    precision mediump float;
    in vec2 vUV; in float vSh; uniform sampler2D uTex; uniform float uFlash; out vec4 o;
    void main(){
      vec4 t = texture(uTex, vUV);
      if (t.a < 0.06) discard;
      // progTex の FS_TEX と同じ被弾の赤。霊夢だけ赤くならないのは不自然なので、
      // 再合成(skinned)経路にも同じ uniform を持たせる。
      o = vec4(mix(t.rgb * vSh, vec3(1.0, 0.0, 0.0), uFlash), 1.0);
    }`;
  let progSkin = null;

  function init(cv) {
    canvas = cv;
    gl = cv.getContext('webgl2', { antialias: true, alpha: false });
    if (!gl) return false;
    progSkin = compile(VS_SKIN, FS_SKIN, { aPos: LOC.pos, aUV: LOC.uv, aNrm: LOC.nrm, aBone: LOC.head });
    progLine = compile(VS_LINE, FS_LINE, { aPos: LOC.pos, aCol: LOC.col });
    progTex = compile(VS_TEX, FS_TEX, { aPos: LOC.pos, aUV: LOC.uv, aNrm: LOC.nrm, aTint: LOC.tint, aHead: LOC.head });
    progBB = compile(VS_BB, FS_BB, { aCorner: LOC.corner, aUV: LOC.uv });
    gl.enable(gl.DEPTH_TEST);
    // アニメライブラリは**トレースに依らない**ので起動時に索引だけ読む。
    // これで「水槽を立てずに YSM アニメを見る」(S6) がそのまま動く。
    loadPoseLibrary();
    // MC のモデルは裏面も描く前提のものが多い (entityCutoutNoCull)。記録した頂点も同じなので裏面を切らない。
    gl.disable(gl.CULL_FACE);
    return true;
  }
  const available = () => !!gl;

  /**
   * 資産 (テクスチャ / アニメの頂点) が後から届いたときに、呼び出し側へ「描き直せ」と言う口。
   *
   * <p>**静止した絵は自分では直らない。** トレース再生中は描画ループが毎フレーム回るので
   * 遅れて届いた資産も次のフレームで乗るが、アニメブラウザ (S6) のように 1 コマだけ
   * 描いて止まる画面では、**白いプレースホルダのまま固まる** (2026-08-24 に踏んだ:
   * texture2.png は 200 で取れているのに霊夢が真っ白のままだった)。
   *
   * <p>rAF で 1 フレームにまとめる —— 316 枚が同時に届いても描き直しは 1 回。
   */
  let assetReady = null;
  let assetReadyQueued = false;
  function notifyAssetReady() {
    if (!assetReady || assetReadyQueued) return;
    assetReadyQueued = true;
    requestAnimationFrame(() => { assetReadyQueued = false; if (assetReady) assetReady(); });
  }

  function tex(id) {
    if (!id) return null;
    let t = textures.get(id);
    if (t) return t;
    t = { tex: gl.createTexture() };
    textures.set(id, t);
    gl.bindTexture(gl.TEXTURE_2D, t.tex);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array([255,255,255,255]));
    const img = new Image();
    img.onload = () => {
      gl.bindTexture(gl.TEXTURE_2D, t.tex);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      notifyAssetReady();
    };
    // '@blockatlas' は吸い出したブロックアトラス。ブロックの UV はこの 1 枚を指す。
    img.src = id === '@blockatlas' ? '/api/blockatlas' : '/api/tex?id=' + encodeURIComponent(id);
    return t;
  }

  function makeMesh(attrs, data, count, extra) {
    const vao = gl.createVertexArray(), vbo = gl.createBuffer();
    gl.bindVertexArray(vao);
    gl.bindBuffer(gl.ARRAY_BUFFER, vbo);
    gl.bufferData(gl.ARRAY_BUFFER, data, gl.STATIC_DRAW);
    const stride = attrs.reduce((a, x) => a + x.n, 0) * 4;
    let off = 0;
    for (const a of attrs) {
      gl.enableVertexAttribArray(a.loc);
      gl.vertexAttribPointer(a.loc, a.n, gl.FLOAT, false, stride, off);
      off += a.n * 4;
    }
    // 追加の頂点属性 (頭マスクなど) は別バッファで持つ。
    // 本体データを組み直さずに足せるので、ポーズを差し替えても使い回せる。
    const bufs = [vbo];
    if (extra) {
      for (const x of extra) {
        const b = gl.createBuffer();
        bufs.push(b);
        gl.bindBuffer(gl.ARRAY_BUFFER, b);
        gl.bufferData(gl.ARRAY_BUFFER, x.data, gl.STATIC_DRAW);
        gl.enableVertexAttribArray(x.loc);
        gl.vertexAttribPointer(x.loc, x.n, gl.FLOAT, false, 0, 0);
      }
    }
    gl.bindVertexArray(null);
    // **バッファも返す。** 返さないと消せない —— GL の資源は GC で還らないので、
    // 捨てる側 (disposeMesh) が名指しで delete する必要がある。
    // 2026-08-25 時点で deleteBuffer/deleteVertexArray はこのファイルに 1 つも
    // 無く、作ったメッシュは GPU に残りっぱなしだった。
    return { vao, count, bufs };
  }

  /** メッシュを捨てる。GL の資源は GC で還らないので明示的に消す。 */
  function disposeMesh(m) {
    if (!m) return;
    try {
      if (m.vao) gl.deleteVertexArray(m.vao);
      if (m.bufs) for (const b of m.bufs) gl.deleteBuffer(b);
    } catch (e) { /* context lost 等。捨てる側で騒がない */ }
  }

  // ===========================================================================
  // MC が吐いたモデルを読む
  // ===========================================================================
  function model(type) {
    let m = models.get(type);
    if (m) return m;
    m = { state: 'loading' };
    models.set(type, m);
    fetch('/api/model?type=' + encodeURIComponent(type))
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error('未書き出し'))))
      .then((j) => {
        // frames = 実際に形が違うポーズだけ (同じ形は書き出し側で 1 本に畳まれている)
        m.raw = (j.frames || [j.verts]).map((v) => new Float32Array(v));
        m.poses = j.poses || null;
        m.walkFrames = j.walkFrames || 10;
        m.texId = j.texture || null;
        m.head = j.head || null;
        // 頭マスク: 区間表現をほどいて 1 頂点 1 float にする
        if (m.head && m.head.ranges) {
          const n = m.raw[0].length / VSTRIDE;
          const mask = new Float32Array(n);
          for (const [a, b] of m.head.ranges) for (let i = a; i < b && i < n; i++) mask[i] = 1;
          m.headMask = mask;
        }
        m.meshCache = new Map();
        m.state = 'ready';
        status = `${models.size} モデル読込済`;
        loadPoses(type, m);
      })
      .catch(() => { m.state = 'missing'; status = '/tlmsim dumpmodels をクライアントで実行するとモブの見た目が出る'; });
    return m;
  }

  /**
   * 姿勢セット (/tlmsim dumpposes の成果) を読む。
   *
   * <p>霊夢の姿勢は mod が送る molang 式で決まる。トレースの {@code ch:anim.molang} には
   * <b>実際に送られた式そのもの</b>が入っているので、式で引けるようにしておけば
   * 「そのとき命令された姿勢」をそのまま出せる。
   */
  function loadPoses(type, m) {
    fetch('/api/poses?type=' + encodeURIComponent(type))
      .then((r) => (r.ok ? r.json() : null))
      .then((j) => {
        if (!j || !j.frames || !j.frames.length) return;
        m.poseFrames = j.frames.map((v) => {
          const d = new Float32Array(v);
          const extra = (m.headMask && m.headMask.length === d.length / VSTRIDE)
            ? [{ loc: LOC.head, n: 1, data: m.headMask }] : null;
          return makeMesh(TEX_ATTRS, d, d.length / VSTRIDE, extra);
        });
        m.byMolang = new Map();
        for (const [name, slot] of Object.entries(j.poses || {})) {
          const expr = (j.molang || {})[name];
          if (expr != null && slot >= 0) m.byMolang.set(expr, slot);
        }
        if (j.texture) m.poseTexId = j.texture;
        status = `姿勢 ${m.byMolang.size} 種 / 形 ${m.poseFrames.length} 本`;
      })
      .catch(() => { /* 未収集なら通常のポーズ選択のまま */ });
  }

  /**
   * 歩行位相。MC は毎 tick 「min(水平移動距離*4, 1)」を足し込んでいるので、
   * トレースの速度から同じように積む。これで手足の振りが実機と同じ位相になる。
   *
   * 13-02: 「作り直す」から「伸ばす」へ。walkPos の外形(id -> Float32Array、
   * meshFor が wp[t] で直接読む)は変えない —— 伸ばすときの長さ/直近accの持ち回りは
   * 別の側の Map(walkLen/walkAcc)に持つ。growWalk は poseYsm の catch-up ループと
   * 同じ型(前回どこまで処理したかを1変数に持ち、次はそこから先だけ回し、終わったら
   * 境界を更新する)。新規entityは walkLen が未設定(=0扱い)なので自然に t=0 から
   * 積み始まり、既存entityは前回の境界の続きから積む —— 同じループが両方を扱える。
   */
  const walkPos = new Map();   // entity id -> Float32Array(tick) (外形は不変)
  const walkLen = new Map();   // entity id -> 埋め済みの長さ(= 次に書くtick)
  const walkAcc = new Map();   // entity id -> 直近のacc(伸ばすときの継続点)
  let walkBoundary = -1;       // 全entity共通で処理済みの最終tick

  function growWalkBuf(buf, need) {
    if (buf.length >= need) return buf;
    let cap = buf.length || 64;
    while (cap < need) cap *= 2;
    const nb = new Float32Array(cap);
    nb.set(buf);
    return nb;
  }
  /**
   * 歩行位相を新しい tick ぶんだけ伸ばす。
   *
   * **ここが 160fps → 20fps の主犯だった**(にーくら 2026-08-23、実測で確定)。
   * 旧実装には 2 つの欠陥があり、しかも**掛け算で効いていた**:
   *
   *   1. 1 体 1 tick の速度を読むために `D.frameAt(t,0)` を呼んでいた。frameAt は
   *      「**これまでに存在した全エンティティ**」を回してフレームを組み立てる関数で、
   *      欲しいのは 1 体ぶんの vx/vz だけ。O(全レーン) を O(log n) で済む場所に使っていた。
   *   2. **死んだモブの伸長を止めていなかった。** `D.entities` は「これまで」を持つ
   *      入れ物なので、1 時間前に死んだ husk も毎 ingest ここへ来て、
   *      誰も読まないバッファを maxTick まで伸ばし続けていた。
   *
   *   費用 = (これまでのモブ数) × (新しい tick 数) × (これまでのレーン数)。3 つとも
   *   録画とともに伸びる。実測: 弾 8,000 発・モブ 150 体で **1 ingest 49.5ms**
   *   —— 20 回/秒 走るので、これだけで CPU を 1 コア食い切る。
   *
   * 直し方は「今のことは今のものだけで計算する」。stateAt は当の entity のレーンを
   * 二分探索するだけで、他人のレーンを 1 本も触らない。
   * (等価性は実記録の全 9,293 ケースで確認済み: frameAt(t,0).pos.get(id) と一致)
   */
  function growWalk(D) {
    const to = D.maxTick;
    const st = D.store;
    const floor = Math.max(0, D.minTick || 0);
    for (const e of D.entities.values()) {
      if (e.role === 'projectile') continue;
      let len = walkLen.get(e.id) || 0;
      if (to < len - 1) continue; // 既に処理済み(このentityぶんは伸ばすものが無い)
      // **死んだものは凍らせる。** 生きていた間ぶんは既に積んであり、その先は
      // 誰も読まない(描かれないので meshFor が呼ばれない)。
      if (e.goneAt !== undefined && e.goneAt < len) continue;
      // 窓より前は store が持っていない。そこから積み直しても 0 が並ぶだけなので、
      // 湧いた tick か窓の左端の**遅い方**から始める(A-3 の窓と噛み合って O(窓) になる)。
      if (len === 0) len = Math.max(0, Math.min(e.first || 0, to), floor);
      let buf = growWalkBuf(walkPos.get(e.id) || new Float32Array(64), to + 1);
      let acc = walkAcc.get(e.id) || 0;
      for (let t = len; t <= to; t++) {
        // **frameAt ではなく当の entity のレーンを引く。** ここが O(全レーン) → O(log n)。
        const p = st ? st.stateAt('pos', e.id, t) : D.frameAt(t, 0).pos.get(e.id);
        if (p) acc += Math.min(Math.hypot(p.vx || 0, p.vz || 0) * 4, 1);
        buf[t] = acc;
      }
      walkPos.set(e.id, buf);
      walkLen.set(e.id, to + 1);
      walkAcc.set(e.id, acc);
    }
    walkBoundary = to;
  }
  /** ストアが忘れた id を、こちらでも忘れる(index.html の履歴の切り捨てから呼ばれる)。
   *  walkPos は絶対 tick 索引の Float32Array なので、entity が消えても誰も読まないまま
   *  残る —— 4 時間なら 1 体 1.1MB。DEATH_AT も一緒に落とす(id の使い回しで
   *  生きているモブが倒れて出るのを防ぐ)。 */
  function forgetEntities(ids) {
    if (!ids || !ids.length) return;
    for (const id of ids) {
      walkPos.delete(id); walkLen.delete(id); walkAcc.delete(id);
      DEATH_AT.delete(id); SOMER_AT.delete(id);
    }
  }
  function resetWalk() {
    walkPos.clear(); walkLen.clear(); walkAcc.clear();
    walkBoundary = -1;
  }

  const slotOf = (m, name) => {
    if (!m.poses) return 0;
    let s = m.poses[name];
    if (s === undefined) s = m.poses[name.replace('aggro_', '')];
    if (s === undefined) s = m.poses.idle;
    return s === undefined ? 0 : s;
  };

  /**
   * 使うメッシュを決める。歩行の<b>振り幅</b>は連続値なので、
   * 静止フレームと歩行フレームの間を補間して作る (振り幅ごとに焼くとデータが倍々になる)。
   * 補間結果は量子化してキャッシュするので、実際に作られるのは数種類。
   */
  function meshFor(m, id, p, t) {
    const pre = p && p.agg ? 'aggro_' : '';
    const wp = walkPos.get(id);
    const amount = Math.min(1, Math.hypot(p.vx || 0, p.vz || 0) * 4);
    const idle = slotOf(m, pre + 'idle');
    if (amount < 0.02 || !wp) return cachedMesh(m, idle, idle, 0);
    const walk = slotOf(m, pre + 'walk' + (Math.floor(wp[t]) % m.walkFrames));
    const q = Math.round(amount * 4) / 4;      // 0.25 刻み
    return cachedMesh(m, idle, walk, q);
  }

  function cachedMesh(m, a, b, w) {
    const key = a + ':' + b + ':' + w;
    let mesh = m.meshCache.get(key);
    if (mesh) return mesh;
    const A = m.raw[a], B = m.raw[b];
    let data;
    if (w <= 0 || !B || A.length !== B.length) {
      data = A;
    } else {
      data = new Float32Array(A.length);
      for (let i = 0; i < A.length; i++) data[i] = A[i] + (B[i] - A[i]) * w;
    }
    const extra = m.headMask ? [{ loc: LOC.head, n: 1, data: m.headMask }] : null;
    mesh = makeMesh(TEX_ATTRS, data, data.length / VSTRIDE, extra);
    m.meshCache.set(key, mesh);
    return mesh;
  }

  /** 頭を回す行列。書き出し時に割り出した回転中心まわりに、トレースの頭の向きで回す。 */
  function headMatrix(m, p) {
    if (!m.head || !m.head.pivot) return M.ident();
    const hy = (p.hy || 0) * Math.PI / 180;
    const hp = (p.pitch || 0) * Math.PI / 180;
    if (Math.abs(hy) < 1e-4 && Math.abs(hp) < 1e-4) return M.ident();
    const [px, py, pz] = m.head.pivot;
    let mm = M.trans(px, py, pz);
    mm = M.mul(mm, M.rotY(-hy));
    mm = M.mul(mm, M.rotX(-hp));
    return M.mul(mm, M.trans(-px, -py, -pz));
  }

  // ===========================================================================
  // 霊夢: 姿勢トレース (SimPoseTrace が記録した頂点をそのまま貼るだけ — D-01)
  // ===========================================================================
  // ysm.js (下の「霊夢: ボーン階層 + アニメ再生」節) は Bedrock のボーン合成を JS で
  // 再実装したもので、これが実機との食い違いの発生源になる (09-CONTEXT.md D-01)。
  // 姿勢 companion があるトレースでは、そちらを使わず<b>実機が計算し終えた頂点</b>を
  // そのまま描く。companion が無ければ黙って ysm.js のフォールバックへ落ちる
  // (退行させない —— このモジュールは「なければ触らない」を徹底する)。
  const poseTrace = { state: 'idle', header: null, base: 0, frames: null, texId: null, groups: null, meshCache: new Map(), ctrl: null, ctrlByT: null };

  /**
   * アニメライブラリ (`/tlmsim animsweep` の記録)。**run 録画とは別物。**
   * `poseTrace` が「この run のこの tick」を持つのに対し、こちらは「このアニメの第 k フレーム」を
   * 持つので、**どの run でも使える** —— 録画していない run でも実機頂点が出せる。
   * 形は `poseTrace` と揃えてある (`cachedPoseParts` を共有するため)。
   */
  const poseLib = {
    state: 'idle', header: null, byAnim: null, texId: null, groups: null, meshCache: new Map(),
    // frames は配列ではなく **Map(slot → Float32Array)** —— 8.1GB を全部は持てないので、
    // 実際に出てきたアニメの分だけ入る。
    frames: new Map(),
    pending: new Set(), loaded: new Set(), failed: new Set(),
    /**
     * LRU の台帳。**アニメライブラリは戦闘のたびに増えて、返さなかった。**
     *
     * <p>2026-08-25 実測: ゾンビ 8 体との戦闘 1 回で、読み込み済みアニメが 4 -> 15 本、
     * 強制 GC 後の heap が 135MB -> 420MB。**体数が 39 -> 1 に戻っても両方とも戻らない。**
     * ヒープスナップショットの参照元も 24-25MB の Float32Array が配列の要素として
     * 掴まれている形で、1 アニメあたり約 26MB。
     *
     * <p>にーくらの症状「複数の敵を出して戦闘が発生し、**終わったら**発生する。
     * つまり時間は全く関係がない」と形が一致する —— 時間ではなく
     * **初めて出した技の数**で増えるため。
     */
    lastUsed: new Map(),   // anim 名 -> 使った順番 (大きいほど新しい)
    animBytes: new Map(),  // anim 名 -> そのアニメが持っている頂点のバイト数
    bytes: 0,              // 合計
    seq: 0,
    evicted: 0,            // 捨てた本数 (黙って捨てない)
  };

  /**
   * ライブラリのキャッシュ上限 (MB)。`?libmb=` で変えられる。
   * 既定 192MB は実測 (1 アニメ約 26MB) から約 7 本ぶん —— 1 回の戦闘で出る技の数
   * (実測 11 本) より少し少なく、山を越えたら古いものから返す。
   * **0 で無制限** (以前の挙動に戻す)。
   */
  const LIB_CAP_BYTES = (() => {
    // **Number(null) は 0 になる。** 指定が無いときに 0 (= 無制限) へ落ちて既定が
    // 効かなかった —— 2026-08-25 に実測で捕まえた (libMB 269 > 上限 192 なのに捨 0)。
    // 『指定が無い』と『0 を指定した』を混ぜないこと。
    const raw = new URLSearchParams(location.search).get('libmb');
    if (raw == null || raw === '') return 192 * 1048576;
    const v = Number(raw);
    return (Number.isFinite(v) && v >= 0 ? v : 192) * 1048576;
  })();

  /**
   * 上限を超えたぶんを、最後に使ったのが古い順に捨てる。
   *
   * <p><b>いま使っているアニメは捨てない</b> —— 捨てた次のフレームで取り直すことになり、
   * 帯域と体感の両方を悪くする。
   */
  function trimPoseLib() {
    if (LIB_CAP_BYTES <= 0 || poseLib.bytes <= LIB_CAP_BYTES) return;
    const order = [...poseLib.loaded].sort(
      (a, b) => (poseLib.lastUsed.get(a) || 0) - (poseLib.lastUsed.get(b) || 0));
    const newest = order[order.length - 1];
    for (const name of order) {
      if (poseLib.bytes <= LIB_CAP_BYTES) break;
      if (name === newest) continue;             // いま使っているものは残す
      const r = poseLib.byAnim && poseLib.byAnim.get(name);
      if (r) {
        for (let slot = r.from; slot <= r.to; slot++) {
          poseLib.frames.delete(slot);
          const parts = poseLib.meshCache.get(slot);
          if (parts) {
            for (const p of parts) disposeMesh(p.mesh);
            poseLib.meshCache.delete(slot);
          }
        }
      }
      poseLib.bytes -= (poseLib.animBytes.get(name) || 0);
      poseLib.animBytes.delete(name);
      poseLib.loaded.delete(name);
      poseLib.lastUsed.delete(name);
      poseLib.evicted++;
      // **黙って捨てない。** 次にそのアニメが出たら取り直しになるので、
      // 体感が悪ければこの行が手がかりになる。
      console.info('[SimLab] アニメライブラリの上限で捨てた: ' + name
        + '  (残り ' + Math.round(poseLib.bytes / 1048576) + 'MB / '
        + Math.round(LIB_CAP_BYTES / 1048576) + 'MB)');
    }
  }

  /**
   * **今描いた霊夢の姿勢が、何を根拠にしているか** (S1b の信頼度表示の素)。
   *
   * <p>`exact` とは呼ばない —— 録画自体が partialTick=1.0 固定・full-bright 固定・
   * yaw 0/180 の合成で、alpha/lightmap/overlay を持たない
   * (`SimModelDump.java:364` の `renderer.render(entity, 0.0F, 1.0F, …, 0x00F000F0)`)。
   * どう積んでも「実機と同一」にはならないので、名前が嘘をつかないようにする。
   *
   * <ul>
   *   <li>`run` —— <b>この run の録画</b>。その瞬間そのもの (最上位)</li>
   *   <li>`library` —— アニメライブラリの実機頂点。<b>実機のレンダラ出力だが、
   *       sweep はアニメを単体で再生して録っている</b>ので、その run 固有の molang や
   *       他レイヤとの合成は乗っていない。実機由来だが run 固有ではない</li>
   *   <li>`backfilled` —— run 録画の slot が -1 で、直前フレームで埋めた</li>
   *   <li>`reconstructed` —— `ysm.js` の再構成 (`CONTROLLER_WEIGHT_FIT=0.45` 使用中)</li>
   *   <li>`palette` —— YSM が実際に使ったボーンごとの局所 TRS をそのまま流したもの
   *       (`palmask-deflate-v1`、14-01/14-02/14-03)。`CONTROLLER_WEIGHT_FIT` の当て推量を
   *       経由しない。ただし録画時の視線・装備・速度・物理履歴を焼き込んだ結果なので、
   *       未観測の状態は合成できない (14-CONTEXT.md §2 の限定)</li>
   *   <li>`missing` —— 霊夢を描いていない</li>
   * </ul>
   */
  let poseSource = 'missing';

  /** チャンバーの床。アニメブラウザの立ち位置 (buildChamber が入れる)。 */
  let stage = { x: 0, y: 65, z: 0 };

  /**
   * アニメブラウザ (S6)。 を入れると、**トレースが無くても**
   * その 1 コマだけを描く。出どころはアニメライブラリ＝実機頂点なので、
   * ysm.js の再構成も CONTROLLER_WEIGHT_FIT=0.45 も通らない。
   *
   * にーくら 2026-08-24:「YSMモデルのアニメーションも、実機を起動してわざわざ
   * 確認するのが面倒でね。水槽で確認できたら楽かなって思ったんだ」
   */
  let animPreview = null;

  /** 内訳を tick ごとに 1 回だけ数えるための番兵。 */
  let lastCountedTick = -1;
  let lastCountedSource = 'missing';

  /** tick ごとの内訳の累計 (run 全体で「何割が実機か」を出すため)。 */
  const poseSourceCount = {
    run: 0, library: 0, backfilled: 0, reconstructed: 0, palette: 0, livePalette: 0, missing: 0,
  };

  /** ライブラリで出せた tick 数と、出せなかった内訳 (derivedStats から読める)。 */
  let poseLibHits = 0;
  const poseLibMiss = { noAnim: 0, notInLib: 0, pastWindow: 0, notLoaded: 0 };

  /**
   * animation controller ({@code player.pre_hold} 等) が選ぶ層を積むかどうか。
   * **既定 ON。** URL に {@code ?ctl=0} を付けると旧経路 (下記) へ戻る。
   *
   * <p><b>既定を ON にした理由</b> (2026-08-20 実測)。ON のときメインハンドの握りは
   * 実機と同じ状態機械が決め、OFF のときは {@link holdAnimFor} の自作合成が決める。
   * 実機のパックの {@code player.pre_hold} は次のように書かれている:
   *
   * <pre>
   *   [default]   hold_mainhand:empty
   *         -&gt; sword       ctrl.hold('mainhand',':sword') &amp;&amp; v.no_hold != 1
   *   [sword]     hold_mainhand:sword1, sword2
   *         -&gt; sword_end   q.all_animations_finished     &lt;-- 再生し終われば必ず抜ける
   *         -&gt; default     v.no_hold == 1
   *         -&gt; sword_run   ctrl.run
   *   [sword_end] hold_mainhand:sword_end, sword_end2
   * </pre>
   *
   * つまり <b>{@code sword1} は抜刀の一瞬であって、剣を持った定常状態ではない</b>。
   * 定常状態は {@code sword_end}。前腕 {@code RightForeArm} への X 回転を実測すると
   * {@code sword1} = <b>-72.0°</b> / {@code sword_end} = <b>-1.6°</b> / {@code empty} = 0°。
   * 旧既定は抜刀モーションを 900 tick 再生し続けていたのと同じで、これが
   * 夢想封印 (extra95) で前腕が折れて見えた原因だった (にーくら「腕だけ折れてる」)。
   *
   * <p><b>採点</b> ({@code simlab/viewer/score-hold.mjs}、animsweep の記録
   * 20260819-212842 に対して 32 本 x 2 フレーム、比較点 64/64):
   *
   * <pre>
   *   物差し            旧 (合成 sword1)   新 (状態機械)
   *   腕のボーンのみ     0.2011             0.1907      -&gt; 5.2% 改善
   *   全身               0.1568             0.1537      -&gt; 2.0% 改善
   *   extra95 (夢想封印) 0.2232             0.0800      -&gt; <b>64% 改善</b>
   * </pre>
   *
   * <p><b>物差しそのものの訂正</b> (2026-08-20): 当初は「腕 0.4220 -&gt; 0.3540 で 16.1% 改善」
   * と測っていたが、その採点器は<b>同じ UV 矩形を持つ quad を曖昧として捨てて</b>いた。
   * 霊夢のモデルは<b>左右の腕で UV 矩形を共有している</b> (実測: 1 フレームの重複 864 組の
   * うち 815 組が X 対称のペア) ため、腕がまるごと捨てられ、64 通り中 8 通りしか値が
   * 出ていなかった。同じ矩形のものを座標順に並べて順番に組むよう直したところ比較点が
   * 64/64 になり、上の値になった。<b>母数を書かない採点は嘘をつく</b>。
   *
   * <p><b>棄却した仮説</b>: 当初「?ctl=1 が正しく見えるのは重み 0.45 が -72° を -32° に
   * 薄めているからだ」と考えたが誤り。controller が選んでいるのは {@code sword_end}
   * (-1.6°) であって、<b>薄めた同じアニメではなく別のアニメ</b>だった。
   *
   * <p>2026-08-19 に一度 OFF にした経緯があるが、それは当時 {@code scale} の掛け算・
   * キーフレームのキー解決・条件付きボーンの削除といった別のバグが残っていた頃の判定で、
   * それらを直した後の再測定でこの結論になった。
   *
   * <p>ばね積分 (parallel3 の timeline) はこのフラグとは無関係に常に走る ——
   * 揺れものの物理は実機に存在するものであり、層の選択とは別の話なので。
   */
  const CTL_LAYERS = (() => {
    try { return new URLSearchParams(location.search).get('ctl') !== '0'; }
    catch (e) { return true; }
  })();

  /**
   * 実機再現パイプライン (ばね積分 + 実測 ctrl + 手持ちによる武器差し替え) を使うかどうか。
   * **既定 ON。** URL に {@code ?ysm2=0} を付けると従来の経路へ戻る。
   *
   * <p><b>既定を ON にした経緯</b> (2026-08-19、にーくらの実機比較):
   * 最初は「歩きや夢想封印が前より悪い」という報告で既定 OFF にしたが、その後に見つけた
   * 3 つのバグ —— {@code scale} を掛け算していた (御幣が永久に消える) /
   * 記録が尽きた後に最後の 1 枚で固まっていた / <b>キーフレームのキーが引けていなかった</b>
   * ("0.0" のようなキーで {@code String(Number(k))} が元へ戻らず [0,0,0] 扱い) ——
   * を直したところ、にーくらの判定が
   * 「治ってる。おおむねあってる。**2、3 は顔がうまくいってるが、1 は顔がうまくいってない**」
   * に変わったため。
   *
   * <p>顔が ① で崩れるのは、<b>mod が送る 26 個の molang 変数</b>
   * ({@code v.roaming.zui} = 口の形、{@code v.hdx}/{@code v.lmx}/{@code v.rmx} = 頭と腕の角度 …)
   * を ① が捨てているから。下地 {@code parallel} 系がそれを読んで表情と姿勢を決めている。
   *
   * <pre>
   *   (既定)         ばね積分 + 実測 ctrl + 武器差し替え + mod の molang 変数
   *                  + animation controller が選ぶ層 (重み CONTROLLER_WEIGHT_FIT)
   *   ?ctl=0         controller の層を積まず、holdAnimFor で握りを合成する旧経路
   *   ?ysm2=0        従来どおり (mod が名指しした 1 本 + 下地 parallel を変数なしで)
   * </pre>
   */
  /**
   * YSM 側にしか無い「着せ替え/表情」変数の既定値。
   *
   * <p>{@code v.roaming.*} の多くは<b>プレイヤーが YSM の UI で選んだ設定</b>だが、
   * <b>mod が上書きで送るものもある</b>。以前ここには「mod は送らない」と書いてあったが
   * <b>誤り</b>だった —— {@code YsmReimuNaianClientRunner:52,315} が
   * {@code (v.roaming.shangyi = 2)} を 60 tick ごとに撃っている。
   *
   * <p>実測 (2026-08-20、animsweep の記録 20260819-212842):
   * mod が {@code v.roaming.yan} を送っていない区間で、実機に写っている目のボーンは
   * {@code Eyes5} だった —— つまり {@code v.roaming.yan == 4}。Viewer は {@code Eyes}
   * (yan=0) を描いており、**目が実機と違って見える**原因になっていた。
   * (判定は「そのボーンだけが持つ UV 矩形が記録に写っているか」で行った。
   *  表情は小さいので誤差の中央値では検出できない)
   *
   * <p>mod が値を送ってきた tick ではそちらが優先される (この既定は下敷き)。
   * 別の設定で遊んでいる霊夢を見るときは、ここを実測し直して直す。
   */
  //
  // **2026-08-20 訂正: yan の既定は 4 ではなく 0。**
  // にーくら『yanは通常、０にならない？』——その通りだった。トレースを時系列で追うと:
  //   t=18021 → 0   （mod が最初に送ったのが 0 = 通常へ戻す指示）
  //   t=18085 → 6   （技の演出）
  //   t=18150 → 0   （戻す）
  //   t=18151 → 6   （また演出）
  // **mod 自身が 0 を「通常」として送っている。** 4 という値は mod のどの送信にも現れない。
  //
  // 私が 4 と書いた根拠は animsweep の記録で Eyes5 が写っていたことだったが、
  // それは mod が 6 を送った後の区間を見ていたか、UV 矩形での判定が誤っていた。
  // **記録の一部を見て「既定」を決めたのが間違い。既定は mod が何を送るかで決まる。**
  //
  // ysm.js は未定義の変数を 0 として扱う (molang の仕様) ので、空にすれば 0 になる。
  //
  // ---------------------------------------------------------------------------
  // **2026-08-25 追加: shangyi の既定は 2。** 上の教訓 (既定は mod が何を送るかで決まる)
  // を、誰も確かめていなかった変数へ当てはめただけで、原則を覆してはいない。
  //
  // にーくら『霊夢の服装に関する molang が戦闘中に何度も変わる。別の服を着たり脱いだり
  // している』。真因は 2 つ重なっていた:
  //   (1) 服は v.roaming.shangyi / qunzi / shoutao … で切り替わる (下地 parallel 系の
  //       77 ボーンが scale=0 で消える)。ここが空なので Viewer は全部 0 で描いていた。
  //   (2) 値が空だと、下地アニメによる v.roaming.* の書き換えが素通しになる
  //       (同じ形の実測が下の 1970 行あたりに在る —— yan が 4 → 6 に書き換えられていた)。
  //
  // **どの値かは測って決めた** (訊いていない)。palette はボーンごとの TRS を運ぶので
  // scale も持つ。実機が録った palette (20260825-183123、1,118 tick・被覆 100%) で
  // 「常に隠れていた 49 ボーン」を出し、候補ごとに下地の scale 式を評価して突き合わせた:
  //
  //   全部 0 (プリセット未選択)        差分 6
  //   **全部 0 + mod の shangyi=2**    差分 0   <= 完全一致
  //   中裙 (v.aa=4) / 中裙2 (v.aa=5)   差分 3   (食い違いは全部 qunzi)
  //   他の 5 プリセット                差分 6〜61
  //
  // つまり実機は**衣装プリセットを選んでいない**。全部 0 のまま mod が shangyi だけを
  // 上書きしている状態だった。だから既定もそれに揃える —— プリセットの仕組みは要らない。
  //
  // 再測定は `node simlab/costume-match.mjs <xxx.pal.json>` で回せる。にーくらが実機で
  // 衣装を選んだら値が変わるので、**そのときはここを決め打ちで直さず測り直すこと。**
  // ---------------------------------------------------------------------------
  //
  // キーは小文字。トレースの molang を拾う側が m[1].toLowerCase() で入れるので揃える。
  const ROAMING_DEFAULTS = { 'v.roaming.shangyi': 2 };

  /* ===========================================================================
     指示されていない molang は、アニメに動かさせない
     ---------------------------------------------------------------------------
     にーくら 2026-08-25:
       「何もしてないときはすごくいいんだけど、攻撃モーションに入ると服装を維持できなく
        なってる。指示されていない molang の値は動かさないようにすればいい。
        指定していないということは、何もしていないときの molang を維持するという意味」

     v.roaming.* と v.night は**状態/設定**であって、アニメの出力ではない。
     mod (ReimuEntity / spell card / naian runner) が明示的に撃つときだけ変わるべきもの。
     ところが YSM の下地アニメと controller は同じ名前へ代入し直すので、放っておくと
     攻撃モーションのたびに服・目・口が書き換わる。

     **同じ形の不具合は既に一度直っている** —— 2026-08-20 の実測で下地アニメが
     v.roaming.yan を 4 -> 6 へ書き換えており、実機の Eyes5 と違う目が描かれていた。
     ただし当時の手当ては ROAMING_DEFAULTS に載っている鍵だけを載せ直すもので、
     いま載っているのは shangyi 1 つ。残り (qunzi/shoutao/weijin/kouzhao/maozi/naian/
     zui/yan/c ...) は素通しのままだった。**接頭辞で全部押さえる。**

     勝ち負けの順: mod がこの tick に撃った値 > 直前まで保っていた値 > (無ければ) 未定義。
     アニメは**どこにも入らない**。
     =========================================================================== */
  const HELD_PREFIX = 'v.roaming.';
  const HELD_EXTRA = ['v.night'];
  /** 衣装ボーンの集合。モデルが読めてから 1 回だけ作る (以後は使い回す)。 */
  let _costumeBones = null;
  function costumeBones() { return _costumeBones; }

  let lastHidden = [];   // いま消えているボーンの名前 (計測用)
  let heldReverts = 0;   // 実際に押し戻した回数 (効いているかを数字で見るため)
  let heldCalls = 0, heldKeys = 0;   // 経路が走ったか / 何個押さえているか (0 の読み違いを防ぐ)

  function isHeldVar(k) { return k.startsWith(HELD_PREFIX) || HELD_EXTRA.indexOf(k) >= 0; }

  /** いまの状態変数を控える。アニメを回す**前**に呼ぶ。 */
  function holdSnapshot(vars) {
    const h = {};
    for (const k in vars) if (isHeldVar(k)) h[k] = vars[k];
    return h;
  }

  /**
   * 控えた値へ戻す。アニメ/controller を回した**後**に呼ぶ。
   * mod がこの tick に撃った鍵 (sent / cvv) は触らない —— そちらが指示だから。
   */
  function applyHeld(vars, held, sent, cvv) {
    heldCalls++; heldKeys = Object.keys(held).length;
    for (const k in held) {
      if (sent && k in sent) continue;
      if (cvv && k in cvv) continue;
      if (vars[k] !== held[k]) { vars[k] = held[k]; heldReverts++; }
    }
    // アニメが**新しく生やした**状態変数も戻す。指示されていない = 何もしていないときの値。
    for (const k in vars) {
      if (!isHeldVar(k) || (k in held)) continue;
      if (sent && k in sent) continue;
      if (cvv && k in cvv) continue;
      if (k in ROAMING_DEFAULTS) vars[k] = ROAMING_DEFAULTS[k]; else delete vars[k];
      heldReverts++;
    }
  }

  /**
   * 実機の記録 ({@code .pose.bin}) を使うかどうか。**既定 ON。**
   * URL に {@code ?rec=0} を付けると、記録がある tick でも<b>使わずに ysm.js の再構成で描く</b>。
   *
   * <p><b>なぜ要るか</b>: 記録がある区間では 3 モードとも同じ「実機の記録」を描くので、
   * <b>並べても全部同じ絵になり比較にならない</b>。記録の外へ出れば 3 枚とも再構成になるが、
   * 今度は<b>正解が画面に無い</b>ので、どれが実機に近いか目で判定できない。
   *
   * <p>{@code ?rec=0} を付けたペインと付けないペインを並べると、
   * <b>同じ tick の「実機」と「再構成」を横に置いて見比べられる</b>。
   * animsweep で 316 秒ぶんの正解が録れた今、これが一番効く見方になる。
   */
  const USE_RECORDING = (() => {
    try { return new URLSearchParams(location.search).get('rec') !== '0'; }
    catch (e) { return true; }
  })();

  // D.tracePath は水槽ライブだけが持つ実 run パス。記録を開くと index.html の load() が
  // null へ戻すので、表示名や URL パラメータに頼らず二つの表示モードを区別できる。
  // ライブでは過去に採った頂点を混ぜない。通常の記録表示では従来の ?rec=0/1 を尊重する。
  let traceIsLive = false;
  function recordingEnabled() { return USE_RECORDING && !traceIsLive; }

  const SIM_PIPELINE = (() => {
    try { return new URLSearchParams(location.search).get('ysm2') !== '0'; }
    catch (e) { return true; }
  })();

  function resetPoseTrace() {
    poseTrace.state = 'idle';
    poseTrace.header = null;
    poseTrace.base = 0;
    poseTrace.frames = null;
    poseTrace.texId = null;
    poseTrace.groups = null;
    poseTrace.meshCache = new Map();
  }

  /**
   * トレースの path で /api/pose を引き、成功すれば bin (float32 LE) も取りに行く。
   * 404 (=まだ姿勢を録っていない) なら黙って従来経路 (ysm.js) へ落ちる。
   */
  /**
   * `.pose.bin` (float32 LE) を索引に従ってフレームへ切り分ける。
   * run 録画とアニメライブラリで**同じ形式**なので 1 箇所にまとめる。
   *
   * <p>`lens` (フレーム番号→頂点数) があれば可変長、無ければ `verts` 固定幅。
   * <b>索引と実バイト長が食い違えば null を返す</b> —— 壊れた bin をそのまま読ませない
   * (T-09-03)。
   */
  function decodePoseFrames(j, buf) {
    const hasLens = Array.isArray(j.lens) && j.lens.length === j.frames;
    const floats = new Float32Array(buf);
    const frames = [];
    let vertsMin = 0;
    let vertsMax = 0;
    if (hasLens) {
      let sumVerts = 0;
      for (const l of j.lens) sumVerts += l;
      if (buf.byteLength !== sumVerts * j.stride * 4) return null;
      let offset = 0;
      vertsMin = Infinity;
      for (let i = 0; i < j.lens.length; i++) {
        const n = j.lens[i] * j.stride;
        frames.push(floats.subarray(offset, offset + n));
        offset += n;
        vertsMin = Math.min(vertsMin, j.lens[i]);
        vertsMax = Math.max(vertsMax, j.lens[i]);
      }
    } else {
      const floatsPerFrame = j.verts * j.stride;
      if (buf.byteLength !== j.frames * floatsPerFrame * 4) return null;
      for (let i = 0; i < j.frames; i++) {
        frames.push(floats.subarray(i * floatsPerFrame, (i + 1) * floatsPerFrame));
      }
    }
    return { frames, vertsMin, vertsMax, hasLens };
  }

  /**
   * アニメライブラリを読む。**トレースに依らない** ので、トレースを切り替えても読み直さない。
   * 無ければ (404) 黙って従来経路 (run 録画 → ysm.js 再構成) のまま。
   */
  function loadPoseLibrary() {
    if (poseLib.state !== 'idle') return;
    poseLib.state = 'loading';
    fetch('/api/poselibrary')
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error('ライブラリ未取得'))))
      .then((j) => {
        const head = Object.assign({}, j.header, { lens: j.lens });
        poseLib.byAnim = new Map();
        for (const a of j.anims) {
          if (a && a.anim != null && a.from != null && a.to != null) poseLib.byAnim.set(a.anim, a);
        }
        poseLib.header = head;
        poseLib.texId = head.texture || null;
        poseLib.groups = groupsOf(head, Array.isArray(j.lens) && j.lens.length === head.frames);
        // **索引だけで ready。頂点はアニメ単位で後から取る。**
        poseLib.state = 'ready';
      })
      .catch(() => { poseLib.state = 'missing'; });
  }

  /**
   * 1 アニメ分の頂点を取りに行く (`/api/poseanim`)。**まるごと読まない理由**は
   * ライブラリの bin が 8.1GB あるから —— サーバの Buffer 上限にもブラウザのメモリにも
   * 収まらない。run が実際に使うのは十数種なので、出てきたものだけ取る。
   *
   * <p>取得中は null を返し続ける (= その間は再構成で描く)。取れたら次のフレームから
   * 実機頂点に切り替わる。**待たせて止めない。**
   */
  function requestAnimFrames(name) {
    if (poseLib.pending.has(name) || poseLib.loaded.has(name)) return;
    poseLib.pending.add(name);
    fetch('/api/poseanim?anim=' + encodeURIComponent(name))
      .then((r) => (r.ok
        ? r.arrayBuffer().then((buf) => ({ buf, lens: (r.headers.get('X-Sim-Lens') || '').split(',').map(Number) }))
        : Promise.reject(new Error('anim 未取得'))))
      .then(({ buf, lens }) => {
        const r = poseLib.byAnim.get(name);
        const stride = poseLib.header.stride;
        const floats = new Float32Array(buf);
        let off = 0;
        for (let i = 0; i < lens.length && r.from + i <= r.to; i++) {
          const n = lens[i] * stride;
          poseLib.frames.set(r.from + i, floats.subarray(off, off + n));
          off += n;
        }
        poseLib.loaded.add(name);
        poseLib.animBytes.set(name, floats.byteLength);
        poseLib.bytes += floats.byteLength;
        poseLib.lastUsed.set(name, ++poseLib.seq);
        trimPoseLib();
        notifyAssetReady();
      })
      .catch(() => { poseLib.failed.add(name); })
      .finally(() => { poseLib.pending.delete(name); });
  }

  /**
   * グループ表 (glens/gtex/textures) を、不変条件を満たすときだけ取り込む。
   * 満たさなければ null (単一グループとして描く) —— 旧ファイルは「不整合」ではなく素通し。
   */
  function groupsOf(j, hasLens) {
    if (!hasLens || !Array.isArray(j.glens) || !Array.isArray(j.gtex) || !Array.isArray(j.textures)) return null;
    if (j.glens.length !== j.frames || j.gtex.length !== j.frames) return null;
    for (let i = 0; i < j.glens.length; i++) {
      const gi = j.glens[i], ti = j.gtex[i];
      if (!Array.isArray(gi) || !Array.isArray(ti) || gi.length !== ti.length) return null;
      let sum = 0;
      for (const v of gi) sum += v;
      if (sum !== j.lens[i]) return null;
    }
    return { glens: j.glens, gtex: j.gtex, textures: j.textures };
  }

  function loadPoseTrace(tracePath) {
    if (!tracePath) return;
    poseTrace.state = 'loading';
    fetch('/api/pose?path=' + encodeURIComponent(tracePath))
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error('姿勢トレース未取得'))))
      .then((j) => fetch(j.binUrl).then((r) => (r.ok ? r.arrayBuffer() : Promise.reject(new Error('bin 未取得'))))
        .then((buf) => {
          // lens (フレーム番号→頂点数、quick 260818-6cj) の有無で分岐する。
          // slots (tick→フレーム番号) とは別物 —— lens が無ければ旧形式の固定幅経路のまま
          // 読む (既存の .pose.json / .pose.bin を例外なく読めることを保つため、
          // このブロックだけ残して壊さない)。
          const hasLens = Array.isArray(j.lens) && j.lens.length === j.frames;
          const floats = new Float32Array(buf);
          const frames = [];
          let vertsMin = 0;
          let vertsMax = 0;
          if (hasLens) {
            let sumVerts = 0;
            for (const l of j.lens) sumVerts += l;
            const expectedBytes = sumVerts * j.stride * 4;
            if (buf.byteLength !== expectedBytes) {
              poseTrace.state = 'missing';
              return;
            }
            let offset = 0;
            vertsMin = Infinity;
            vertsMax = 0;
            for (let i = 0; i < j.lens.length; i++) {
              const floatsThisFrame = j.lens[i] * j.stride;
              frames.push(floats.subarray(offset, offset + floatsThisFrame));
              offset += floatsThisFrame;
              vertsMin = Math.min(vertsMin, j.lens[i]);
              vertsMax = Math.max(vertsMax, j.lens[i]);
            }
          } else {
            const floatsPerFrame = j.verts * j.stride;
            // 索引の frames × verts × stride と実バイト長が一致しなければ読み込みを捨てる
            // (T-09-03: 壊れた/不整合な bin をそのまま読ませない)。
            const expectedBytes = j.frames * floatsPerFrame * 4;
            if (buf.byteLength !== expectedBytes) {
              poseTrace.state = 'missing';
              return;
            }
            for (let i = 0; i < j.frames; i++) {
              frames.push(floats.subarray(i * floatsPerFrame, (i + 1) * floatsPerFrame));
            }
          }
          poseTrace.header = j;
          poseTrace.ctrl = Array.isArray(j.ctrl) ? j.ctrl : null;
          // ctrl companion の t は**姿勢トレース側の tick 番号** (gt - gt0) であって
          // アリーナトレースの tick ではない。両者は base だけずれているので、
          // 配列の添字ではなく t で引けるように索引を作る
          // (添字で引くと最大 base 分ずれたデータを食わせることになる)。
          poseTrace.ctrlByT = null;
          if (poseTrace.ctrl) {
            poseTrace.ctrlByT = new Map();
            for (const row of poseTrace.ctrl) poseTrace.ctrlByT.set(row.t | 0, row);
          }
          poseTrace.base = j.base || 0;
          poseTrace.frames = frames;
          poseTrace.texId = j.texture || null;
          poseTrace.state = 'ready';

          // グループ表 (glens/gtex/textures、quick 260818-oq4)。hasLens が真で、かつ
          // 3つとも配列として揃い、各種不変条件 (sum(glens[i])===lens[i] 等) を満たす
          // ときだけ取り込む。glens がそもそも無い旧ファイルは「不整合」ではなく素通し
          // (status に警告を出さない、既存の単一グループ経路のまま読む)。
          poseTrace.groups = null;
          let groupWarning = false;
          let maxGroups = 0;
          const hasGroupArrays = hasLens && Array.isArray(j.glens) && Array.isArray(j.gtex) && Array.isArray(j.textures);
          if (hasGroupArrays) {
            let ok = j.glens.length === j.frames && j.gtex.length === j.frames;
            for (let i = 0; ok && i < j.glens.length; i++) {
              const gi = j.glens[i], ti = j.gtex[i];
              if (!Array.isArray(gi) || !Array.isArray(ti) || gi.length !== ti.length) { ok = false; break; }
              let sum = 0;
              for (const v of gi) sum += v;
              if (sum !== j.lens[i]) { ok = false; break; }
              maxGroups = Math.max(maxGroups, gi.length);
            }
            if (ok) {
              poseTrace.groups = { glens: j.glens, gtex: j.gtex, textures: j.textures };
            } else {
              groupWarning = true;
            }
          }

          const ticks = Array.isArray(j.slots) ? j.slots.length : 0;
          let s = hasLens
            ? `姿勢トレース ${j.frames}本 / ${ticks}tick / 頂点 ${vertsMin}-${vertsMax}`
            : `姿勢トレース ${j.frames}本 / ${ticks}tick`;
          if (poseTrace.groups) {
            s += ` / グループ 最大 ${maxGroups}`;
          } else if (groupWarning) {
            s += ' / グループ表が不整合のため単一グループとして描画';
          }
          status = s;
        }))
      .catch(() => { poseTrace.state = 'missing'; });
  }

  /**
   * tick に対応するパーツ配列 ({@code [{ mesh, texId }, …]})。その tick の slot が -1
   * (未記録) なら、描画を欠落させないよう直前の有効 slot まで遡って使う。
   * グループ表が無ければ従来どおり全体で 1 パーツを返す (quick 260818-oq4)。
   */
  function poseTraceParts(tick) {
    if (!recordingEnabled()) return null;   // ライブまたは ?rec=0: 記録を使わない
    if (poseTrace.state !== 'ready' || !poseTrace.header) return null;
    const slots = poseTrace.header.slots || [];
    const idx = tick + poseTrace.base;
    // **記録の外は null を返して ysm.js の再構成へ落とす。**
    // 以前はここで idx を slots.length-1 へ丸めていたため、記録が尽きた後は
    // 「最後のフレーム」を延々と貼り続けていた —— 動いていないのに動いているように
    // 見えないので気づきにくく、実際 2026-08-19 に
    // 「夢想封印が①②③とも実機と違う」の正体がこれだった (tick 428 は記録の外で、
    // 3 枚とも tick 144 の絵を出していた)。
    // 古い1枚を貼り続けるのは「データが無い」ことを隠す嘘なので、再構成へ落とすほうがよい。
    if (idx < 0 || idx >= slots.length) return null;
    let slot = -1;
    let backfilled = false;
    for (let i = idx; i >= 0; i--) {
      if (slots[i] >= 0) { slot = slots[i]; backfilled = i !== idx; break; }
    }
    if (slot < 0 || !poseTrace.frames[slot]) return null;
    // **埋めたことを黙らない。** その tick は記録されていないので、
    // 「録画そのもの」と同じ顔をして出してはいけない (S1b の信頼度で区別する)。
    poseSource = backfilled ? 'backfilled' : 'run';
    return cachedPoseParts(slot);
  }

  /**
   * @param src 頂点の出どころ。`poseTrace` (run 録画) か `poseLib` (アニメライブラリ) の
   *            どちらか —— 形は同じ (`header` / `frames` / `groups` / `meshCache`) なので、
   *            同じ組み立てを 2 度書かない。
   */
  /**
   * アニメライブラリ (`/tlmsim animsweep`) から、その tick の実機頂点を引く。
   *
   * <p><b>run 録画とは引き方が根本的に違う。</b> run 録画は `slots[tick]` ——「この run の
   * この瞬間」しか意味を持たない。ライブラリは<b>アニメ名で引く</b>ので、
   * <b>録画していない run でも実機頂点が出せる</b>。
   * トレースの `anim` チャンネルが再生中のアニメ名を持っているので、
   * `animTrack` (name / elapsed) をそのまま鍵にできる。
   *
   * <p><b>録画窓の外は null を返す。</b> sweep は 1 アニメ 20 tick (=1 秒) しか録らない
   * (`SimAnimSweep.DEFAULT_TICKS_PER_ANIM`)。位相がそれを超えたら「最後のフレームを
   * 貼り続ける」ことはしない —— それは 2026-08-19 の夢想封印の件と同じ嘘になる
   * (`poseTraceParts` の注記参照)。再構成へ落として、落ちた回数を数える。
   *
   * <p>実測 (2026-08-24、tank 1583 tick): ライブラリで出せるのは 44.8%、
   * 位相が窓の外が 35.6%、アニメ未確定 18.6%、ライブラリに無いアニメ 1.0%。
   * 窓の外を減らすには sweep 側の `ticksPerAnim` を伸ばす (全長を録ると 401GB なので、
   * 3 秒で打ち切れば 11.5GB。静止アニメ 76/316 は dedup でさらに減る)。
   */
  function poseLibParts(tick) {
    if (!recordingEnabled()) return null;
    if (poseLib.state !== 'ready') return null;
    const name = animTrack.name[tick];
    if (!name) { poseLibMiss.noAnim++; return null; }
    const r = poseLib.byAnim.get(name);
    if (!r) { poseLibMiss.notInLib++; return null; }
    // elapsed は秒 (animTrack が (t - start) / 20 で入れている)。
    const frameCount = r.to - r.from + 1;
    const k = Math.round((animTrack.elapsed[tick] || 0) * 20);
    if (k < 0 || k >= frameCount) { poseLibMiss.pastWindow++; return null; }
    const slot = r.from + k;
    const verts = poseLib.frames.get(slot);
    if (!verts) {
      // まだ取っていないアニメ。取りに行かせて、この tick は再構成で描く。
      if (!poseLib.failed.has(name)) requestAnimFrames(name);
      poseLibMiss.notLoaded++;
      return null;
    }
    poseLibHits++;
    poseLib.lastUsed.set(name, ++poseLib.seq);   // LRU の順番を更新
    poseSource = 'library';
    return cachedPoseParts(slot, poseLib);
  }

  function cachedPoseParts(slot, src = poseTrace) {
    let parts = src.meshCache.get(slot);
    if (parts) return parts;
    // frames は run 録画では配列、ライブラリでは Map (8.1GB を全部は持てないため)。
    const verts = src.frames instanceof Map ? src.frames.get(slot) : src.frames[slot];
    const totalVerts = verts.length / VSTRIDE;
    // 頭マスク: reimu.json (通常モデルダンプ) 由来。頂点数がフレーム全体と一致するときだけ
    // 流用する (RESEARCH Pitfall 2 の解 — shoot() は頭向きを 0 化して録るので、頭だけは
    // headMatrix() 側で別途回す前提)。一致しなければ null (霊夢では solveHead が破綻を
    // 検出して頭情報を載せないため、この経路は今日すでに不活性)。
    const headModel = model(src.header.type);
    const fullHeadMask = (headModel.headMask && headModel.headMask.length === totalVerts)
      ? headModel.headMask : null;

    if (src.groups) {
      // glens の順序のまま積む (並べ替え禁止 — 半透明の合成は描画順に依存する)。
      const glens = src.groups.glens[slot] || [];
      const gtex = src.groups.gtex[slot] || [];
      const textures = src.groups.textures;
      parts = [];
      let vOff = 0;
      for (let k = 0; k < glens.length; k++) {
        const n = glens[k];
        const sub = verts.subarray(vOff * VSTRIDE, (vOff + n) * VSTRIDE);
        const extra = fullHeadMask
          ? [{ loc: LOC.head, n: 1, data: fullHeadMask.slice(vOff, vOff + n) }] : null;
        const texRaw = textures[gtex[k]];
        const texId = texRaw ? texRaw : null; // 空文字は呼び出し側の既定へ落とす印
        parts.push({ mesh: makeMesh(TEX_ATTRS, sub, n, extra), texId });
        vOff += n;
      }
    } else {
      const extra = fullHeadMask ? [{ loc: LOC.head, n: 1, data: fullHeadMask }] : null;
      parts = [{ mesh: makeMesh(TEX_ATTRS, verts, totalVerts, extra), texId: null }];
    }
    src.meshCache.set(slot, parts);
    return parts;
  }

  // ===========================================================================
  // 霊夢: ボーン階層 + アニメ再生
  // ===========================================================================
  // mod がどのアニメを指定したかはトレース (ch:anim.anim) に毎 tick 残っている。
  // それを実機と同じアニメ定義に当てるので、モーションは実機と同じデータで動く。
  const ysm = { state: 'idle', geo: null, anims: null, base: [], mesh: null,
                boneTex: null, texId: null, lastKey: -1, info: '',
                // --- 実機再現のための追加 (2026-08-19) ---
                baseNames: [],   // 下地 parallel 系の名前 (timeline を毎tick回すため)
                ctlJson: null,   // animation controller の定義
                ctl: null,       // その実行状態 (状態機械)
                vars: {},        // tick を跨いで持ち回す molang 変数。parallel3 のばね
                                 // 積分器がここへ状態を書き続ける (毎tick作り直すと
                                 // 髪/リボン/胸の揺れものが永久に静止したままになる)
                simTick: -1 };   // どの tick まで積分したか。巻き戻したら作り直す

  async function loadYsm() {
    if (ysm.state !== 'idle' || !window.YSM) return;
    ysm.state = 'loading';
    try {
      const manifest = await fetch('/api/ysm?what=manifest').then((r) => r.json());
      const model = await fetch('/api/ysm?what=model&name=main').then((r) => r.json());
      const geoSrc = (model['minecraft:geometry'] || [])[0];
      if (!geoSrc) throw new Error('geometry がない');

      // アニメはマニフェストが挙げているファイルを全部読む
      const names = Object.keys((manifest.files && manifest.files.player && manifest.files.player.animation) || {});
      const anims = {};
      for (const n of names) {
        try {
          const j = await fetch('/api/ysm?what=anim&name=' + encodeURIComponent(n)).then((r) => r.json());
          Object.assign(anims, j.animations || {});
        } catch { /* 読めないファイルは飛ばす */ }
      }

      const props = manifest.properties || {};
      const hidden = window.YSM.collectHidden(anims);
      // **衣装ボーンもここで作る。** anims が生の形で揃っている唯一の場所。
      // 描画中に作ろうとすると、まだ読めていない段階で**空集合を掴んで固定**する
      // (2026-08-25 に実際にそれで 0 本になった。空の Set は truthy なので気づけない)。
      _costumeBones = window.YSM.collectCostumeBones(anims);
      const g = window.YSM.buildGeometry(geoSrc, props.width_scale || 1, props.height_scale || 1, hidden);

      // 頂点 (pos/uv/nrm) は 8 要素。ボーン番号は別バッファ。
      ysm.mesh = makeMesh(
        [{ loc: LOC.pos, n: 3 }, { loc: LOC.uv, n: 2 }, { loc: LOC.nrm, n: 3 }],
        g.verts, g.count, [{ loc: LOC.head, n: 1, data: g.boneIndex }]);

      // ボーン行列テクスチャ: 1 ボーン = 4 テクセル (mat4 の各列)
      ysm.boneTex = gl.createTexture();
      gl.bindTexture(gl.TEXTURE_2D, ysm.boneTex);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA32F, 4, g.bones.length, 0, gl.RGBA, gl.FLOAT, null);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);

      // 常時走る parallel 系は t=0 で下地として敷く (アクセサリの抑制など)
      // **pre_parallel* を先、parallel* を後に積む。**
      // 名前の通り "pre_" は前段。アルファベット順に並べると parallel1 の後ろへ
      // pre_parallel0 が来てしまい、**後勝ちの scale を取り違える**。
      //
      // 実害 (2026-08-20 実測): parallel1 が表情を選ぶ
      //   mad2: scale = "v.roaming.zui==5?1:0"    ← zui≠5 なら 0 (隠す)
      // のに対し pre_parallel0 が口の形を微調整する
      //   mad2: scale = [1, 0.75125, 1]            ← これは可視性ではなく形の調整
      // アルファベット順だと後者が勝ち、**mad2 が常に出っぱなし**になって
      // 正しい口と二重に描かれていた (zui=0 で normal3+mad2、zui=7 で OpenMouth8+mad2)。
      // pre_ を先にすると口はちょうど1つになり、御幣 (pre_parallel0 が隠し hold_* が出し直す)
      // も従来どおり正しく出る —— 両立することを実測で確認済み。
      const baseAll = Object.keys(anims).filter((n) => /^(pre_)?parallel/.test(n));
      ysm.baseNames = baseAll.filter((n) => /^pre_/.test(n)).sort()
        .concat(baseAll.filter((n) => !/^pre_/.test(n)).sort());
      ysm.base = ysm.baseNames.map((n) => window.YSM.sampleAnimation(anims[n], 0, {}));

      // animation controller (取れなくても従来どおり動く)
      try {
        ysm.ctlJson = await fetch('/api/ysm?what=controllers').then((r) => r.json());
        ysm.ctl = window.YSM.initControllers(ysm.ctlJson);
      } catch (e) { ysm.ctlJson = null; ysm.ctl = null; }
      // **無言のフォールバックを潰す。** poseYsm() の握りの判定は
      //   if (!(ysm.ctl && CTL_LAYERS)) wanted.push(holdAnimFor('mainhand', ...))
      // なので、CTL_LAYERS が既定 ON でも ysm.ctl が null なら合成握り経路へ落ちる。
      // 上の fetch は serve.mjs が 404 を返す条件が実在するため本当に失敗しうる。
      // 静的検査 (grep / node --check) では絶対に捕まらないので、実行時に一度だけ言う。
      if (CTL_LAYERS && !ysm.ctl) {
        console.warn('[SimLab] animation controller を読めなかったため、メインハンドの握りは'
          + '旧経路 (holdAnimFor の合成) にフォールバックします。夢想封印などで前腕が'
          + ' 72 度折れて見えるならこれが原因です。/api/ysm?what=controllers を確認してください。');
      }
      ysm.vars = {};
      ysm.simTick = -1;

      ysm.geo = g;
      ysm.anims = anims;
      // YSM の実際の model id は manifest 内ではなく pack directory 名。
      // serve.mjs が付けた値を live palette の購読・decode の両方で照合する。
      ysm.modelId = String((manifest._simlab && manifest._simlab.modelId) || '');
      ysm.texId = 'ysm:textures/' + ((props.default_texture && props.default_texture !== 'default')
        ? props.default_texture : 'texture2') + '.png';
      ysm.state = 'ready';
      // **中を覗ける窓を開けておく。** 見た目の不具合を「描画で確かめる」のは
      // ソフトウェア描画だと潰れて判らないことがある（顔が真っ黒になった、2026-08-20）。
      // molang 変数を直接読めれば、届いているのか効いていないのかを切り分けられる。
      window.SIMLAB_YSM = ysm;
      ysm.info = `YSM ${g.bones.length}ボーン ${(g.count/3)|0}三角形 アニメ${Object.keys(anims).length}`;
      status = ysm.info;
    } catch (e) {
      ysm.state = 'failed';
      ysm.info = 'YSM 失敗: ' + e.message;
      status = ysm.info;
    }
  }

  // ===========================================================================
  // palette (14-01/14-03): 実験的な描画経路。既定 off (?pal 無し = 従来どおり byte-for-byte)。
  // ---------------------------------------------------------------------------
  // `?pal=golden` で committed fixture を (トレースに依らず1度だけ)、`?pal=1` (golden 以外の
  // 任意値) でいま開いているトレースの実 companion を `/api/palette` 経由で読む。
  // decode (fetch + DecompressionStream) は非同期なので、poseYsm() の同期契約を壊さない
  // よう「間に合っていれば使う、間に合っていなければ今回のフレームは黙って従来の再構成へ
  // 落ちる (裏で decode は進めておく)」という形にする —— 一度読めた tick 以降は
  // stream.at() がキャッシュ済み state9 を同期的に (Promise の resolve 待ちなしで見た目上)
  // 返すので、実質毎フレーム再構成し続けることにはならない。
  // ===========================================================================
  const PAL_MODE = (() => {
    try {
      // 2026-08-25 にーくら判定 (adopt): 4ペイン比較を見て「④ palette が一番」。
      // よって **既定で on**。`?pal=0` で切る、`?pal=golden` は fixture。
      // 判定の理由もそのまま残す —— 「録画が一番 ysm の molang が異なっていたから」。
      // 録画は実機の頂点そのものだが、その瞬間の molang 状態が他と食い違っていた。
      const v = new URLSearchParams(location.search).get('pal');
      if (v === '0') return null;
      return v || '1';
    } catch (e) { return null; }
  })();
  const PAL_IS_FIXTURE = PAL_MODE === 'golden';

  // `base` は「トレースの tick 空間」→「palette 自身の tick 空間」のずれ (= gameTime - gt0)。
  // poseTrace.base (gl.js:566/999) と同じ役割で、同じように `tick + base` で引く。
  const palState = { status: 'idle', index: null, stream: null, slotOf: null, loggedMissing: false, base: 0 };
  let ysmLastPoseSource = 'reconstructed';
  let palLastAppliedTick = -1;
  let palPending = false;
  /**
   * いま boneTex に載っている palette の tick。**palLastAppliedTick とは別物**で、
   * あちらは「解凍が済んだ tick」、こちらは「GPU が今持っている tick」。再構成経路が
   * 同じ boneTex を上書きするので、この 2 つはずれる。
   */
  let palBoneTexTick = -1;
  /** 直近に組んだ palette の行列。boneTex を奪われたときに載せ直すために持つ。 */
  let palLastMats = null;
  /**
   * palette 状態の世代。トレースを切り替えると増える。飛んでいる stream.at() の解決を
   * 「前のトレースのものだ」と判って捨てるための札 (これが無いと前トレースの palette を
   * 新トレースの boneTex へ載せる)。
   */
  let palGen = 0;
  /**
   * いま palette を引いている**実トレースのパス**。`D.path` は表示名になりうる
   * (ライブは「水槽（ライブ）」) ので、companion の解決にはこちらを使う。
   */
  let palPath = null;
  /** 索引の版 (サーバが返す mtime)。これが動いたときだけ本体を取り直す。 */
  let palMtime = -1;
  /** 次に頭を突いてよい時刻 (performance.now())。 */
  let palPollAt = 0;
  /** 頭を突く間隔。索引は 5 秒ごと (CHECKPOINT_EVERY=100 tick) に伸びる。 */
  const PAL_POLL_MS = 2500;
  /** 「まだ録っていない」ときの再試行間隔。**騒がない** —— 録り始める前の 404 は正常。 */
  const PAL_RETRY_MS = 5000;
  /** 404 を一度だけ言うための札 (毎回言うとコンソールが埋まる)。 */
  let palSaidMissing = false;

  /** ブラウザの DecompressionStream('deflate') で解凍する。zlib ラップ (RFC 1950) 前提。 */
  async function inflateDeflateStream(bytes) {
    const ds = new DecompressionStream('deflate');
    const stream = new Blob([bytes]).stream().pipeThrough(ds);
    const buf = await new Response(stream).arrayBuffer();
    return new Uint8Array(buf);
  }

  /**
   * `?pal=1` (実 companion) がトレースを跨いで持ち回してはいけない状態をたたむ。
   * `resetPoseTrace` の palette 版 —— 新しいトレースを開いたら、前のトレースの
   * デルタチェーン (state9 / curFrame) を引き継がず作り直す。golden fixture は
   * トレースに依らないので対象外 (setTrace からは呼ばない)。
   */
  function resetPaletteState() {
    palGen++;   // 飛んでいる解凍を無効化する (下の gen チェック)
    palState.status = 'idle';
    palState.index = null;
    palState.stream = null;
    palState.slotOf = null;
    palState.loggedMissing = false;
    palState.base = 0;
    palLastAppliedTick = -1;
    palPending = false;
    palBoneTexTick = -1;
    palLastMats = null;
    palPath = null;
    palMtime = -1;
    palPollAt = 0;
    palSaidMissing = false;
  }

  async function loadPalette(tracePath) {
    if (!PAL_MODE || palState.status !== 'idle') return;
    if (tracePath) palPath = tracePath;
    // `?pal=1` はいま開いているトレースの companion を引く —— まだ path が判らなければ、
    // setTrace が D.path を持って呼び直すまで待つ (golden fixture はここで即ロードする)。
    if (!PAL_IS_FIXTURE && !tracePath) return;
    palState.status = 'loading';
    try {
      const url = PAL_IS_FIXTURE
        ? '/api/palette?fixture=' + encodeURIComponent(PAL_MODE)
        : '/api/palette?path=' + encodeURIComponent(tracePath);
      const idx = await fetch(url).then((r) => {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      });
      const fetchRecord = (from, len) => fetch(idx.binUrl + '&from=' + from + '&len=' + len)
        .then((r) => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.arrayBuffer(); })
        .then((b) => new Uint8Array(b));
      palState.index = idx;
      palState.stream = window.SimPalette.makeStream(idx, fetchRecord, inflateDeflateStream);
      palState.slotOf = new Map(idx.names.map((n, i) => [n, i]));
      // fixture はトレースを持たないので原点合わせは不要 (base=0)。実 companion は
      // サーバが算出した base を必ず使う —— 生の T.tick で引くと別の瞬間の姿勢を描く。
      palState.base = PAL_IS_FIXTURE ? 0 : (idx.base || 0);
      palMtime = idx.mtime == null ? -1 : idx.mtime;
      palSaidMissing = false;
      palState.status = 'ready';
    } catch (e) {
      // **「まだ録っていない」と「壊れている」を混ぜない。**
      // 404 は録り始める前の正常な状態で、ライブでは待っていれば必ず来る ——
      // ここを終端 (failed) にしていたせいで、一度でも早く開くと二度と palette へ
      // 戻れなかった (2026-08-25 の審査で判明)。missing は静かに再試行する。
      const missing = !PAL_IS_FIXTURE && /HTTP 404/.test(String(e && e.message));
      if (missing) {
        if (!palSaidMissing) {
          palSaidMissing = true;
          console.info('[SimLab] palette companion はまだ無い。録り始めたら自動で拾う');
        }
        palState.status = 'missing';
      } else {
        const log = PAL_IS_FIXTURE ? console.error : console.warn;
        log('[SimLab] palette (?pal=' + PAL_MODE + ') の読み込みに失敗しました:', e);
        palState.status = 'failed';
      }
    }
    // **この fetch 自体が「もう1本の非同期」を足している。** 他の資産 (テクスチャ、
    // アニメライブラリの1本) は読み終わるたびに notifyAssetReady() で再描画を起こすのに、
    // palette の読み込み完了/失敗はどちらもそれをしていなかった —— 初回 draw() は
    // load() から同期的に1回呼ばれるだけ (index.html:431) なので、この fetch が他の資産
    // より遅く終わると、後から ysm/palette が ready になっても絵が古いまま固まる
    // (compare.html の4枚並びで palette ペインだけ「未描画」のまま止まって見えた、実測)。
    // 成功・失敗どちらでも「もう状態が変わった」ので、他の資産と同じ経路で1回だけ促す。
    notifyAssetReady();
  }
  /**
   * 索引がライブで伸びるのを追いかける。
   *
   * <p><b>なぜ要るのか (2026-08-25 の審査で判明)</b>: 索引は 5 秒ごとの checkpoint で
   * 伸びるのに、Viewer はこれまで**一度しか読まなかった** —— setTrace は同じ D.key で
   * 早期 return し (13-02 がライブ中に D.key を安定させたので確実に一度)、loadPalette は
   * status !== idle で即 return し、makeStream は offsets を構築時に一度だけ計算する。
   * 結果、**開いた時点より未来の tick は全部再構成へ落ちていた**。30 分見ていれば
   * palette の担当率はゼロへ近づく。
   *
   * <p>記録 (伸びないファイル) に対しても無害 —— mtime が動かないので取り直さない。
   */
  async function palettePoll() {
    if (!PAL_MODE || PAL_IS_FIXTURE || !palPath) return;
    const now = performance.now();
    if (now < palPollAt) return;
    // まだ読めていない状態はゆっくり、読めている状態は checkpoint の刻みで突く。
    const ready = palState.status === 'ready';
    palPollAt = now + (ready ? PAL_POLL_MS : PAL_RETRY_MS);

    if (!ready) {
      // missing / failed から復帰させる。**ライブでは終端にしない。**
      if (palState.status === 'missing' || palState.status === 'failed') {
        palState.status = 'idle';
        await loadPalette(palPath);
      }
      return;
    }

    let head = null;
    try {
      const r = await fetch('/api/palette/head?path=' + encodeURIComponent(palPath));
      if (!r.ok) return;   // 消えた/入れ替わった。次の周期で拾い直す
      head = await r.json();
    } catch (e) { return; }    // 一時的な失敗。騒がない
    if (!head || head.mtime == null) return;
    if (head.mtime === palMtime) return;                     // 伸びていない
    if (palState.stream && head.frames <= palState.stream.frames) {
      palMtime = head.mtime;                                  // 書き直されただけ
      return;
    }

    // 伸びた。本体を取り直して差し替える。
    const gen = palGen;
    let idx = null;
    try {
      const r = await fetch('/api/palette?path=' + encodeURIComponent(palPath));
      if (!r.ok) return;
      idx = await r.json();
    } catch (e) { return; }
    if (gen !== palGen) return;   // トレースが切り替わった。載せない

    if (palState.stream && palState.stream.extend(idx)) {
      palState.index = idx;
      palMtime = idx.mtime == null ? head.mtime : idx.mtime;
      // **差し替えただけでは絵は変わらない。** 他の資産と同じ経路で 1 回だけ促す。
      notifyAssetReady();
      return;
    }
    // extend が拒んだ = 別の run の companion に入れ替わった。作り直す。
    // **黙って古い索引を使い続けない** —— 前の run の姿勢を新しい bin へ差分適用すると
    // 壊れた姿勢を黙って描くことになる (palette-selftest の extend 節)。
    console.info('[SimLab] palette companion が別の run に入れ替わった。読み直す');
    resetPaletteState();
    await loadPalette(palPath);
    notifyAssetReady();
  }
  if (PAL_IS_FIXTURE) loadPalette();
  else setInterval(function () { palettePoll(); }, 1000);

  /**
   * この tick の palette を boneTex へ upload できたら true。
   * 間に合っていなければ (まだ decode 中、またはこの tick に記録が無い) false を返し、
   * 呼び出し側 (poseYsm) を従来の再構成経路へ落とす。
   */
  /**
   * この tick を palette が受け持てるか (索引を見るだけの同期判定)。
   * <p>描画側の優先順を決めるのに使う。実際に解凍が間に合ったかは見ない —— 間に合って
   * いなければ {@link poseYsmPalette} が false を返して 1 フレームだけ再構成へ落ち、
   * 解凍完了時の notifyAssetReady() が描き直す。
   */
  function paletteCanServe(T) {
    if (!PAL_MODE || palState.status !== 'ready' || !palState.index) return false;
    // **受け皿が居ることまで確かめる。** これが真だと呼び出し側は頂点経路を丸ごと飛ばすが、
    // 受け皿の skinned 経路は ysm.state === 'ready' を要求する。ここで見ないと、YSM パックが
    // 読めていないときに「頂点の録画はあるのに霊夢が一枚も描かれない」(poseSource='missing')
    // になる —— 描けないものを描けると答えない。
    if (ysm.state !== 'ready' || !ysm.geo || !ysm.geo.bones) return false;
    const slots = palState.index.slots;
    const pt = T.tick + (palState.base || 0);
    return pt >= 0 && pt < slots.length && slots[pt] !== -1;
  }

  function poseYsmPalette(T) {
    if (palState.status !== 'ready') return false;
    if (palLastAppliedTick === T.tick) {
      // **解凍済みでも、boneTex をまだ持っているとは限らない。** palette を持たない tick
      // (slots[t] === -1) を跨いで往復すると、間の再構成が同じ boneTex を上書きしている。
      // ここで載せ直さないと「別 tick の姿勢を描いて palette と名乗る」ことになる。
      if (palBoneTexTick === T.tick) return true;
      if (!palLastMats) return false;
      gl.bindTexture(gl.TEXTURE_2D, ysm.boneTex);
      gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, 4, ysm.geo.bones.length, gl.RGBA, gl.FLOAT, palLastMats);
      palBoneTexTick = T.tick;
      return true;
    }
    const slots = palState.index.slots;
    // palette の tick 空間へ移してから引く (poseTrace の tick + base と同じ)。
    const pt = T.tick + (palState.base || 0);
    if (pt < 0 || pt >= slots.length || slots[pt] === -1) return false;
    if (palPending) return false;
    palPending = true;
    const gen = palGen;
    palState.stream.at(pt).then((state9) => {
      // 前のトレースの解凍が今ごろ返ってきた場合。**新しい boneTex へ載せない。**
      if (gen !== palGen) return;
      palPending = false;
      if (!state9) return;
      const Y = window.YSM;
      const { mats, missing } = Y.matsFromPalette(ysm.geo.bones, state9, palState.slotOf);
      if (missing > 0) {
        // **半端な remap で描かない。** CLAUDE.md が記録する animation controller fetch の
        // 無言フォールバックと同じ失敗モードをここでも避ける (gl.js:1184-1188 と同じ思想)。
        if (!palState.loggedMissing) {
          palState.loggedMissing = true;
          const names = [];
          for (const b of ysm.geo.bones) {
            if (!palState.slotOf.has(b.name)) { names.push(b.name); if (names.length >= 3) break; }
          }
          console.error('[SimLab] palette remap 失敗: ' + missing + ' 本のボーンが names[] に無い'
            + ' (例: ' + names.join(', ') + ')。以後この fixture は旧経路 (ysm.js 再構成) へフォールバックします。');
        }
        palState.status = 'failed'; // 以後 poseYsmPalette は毎回 false を返す (握り直さない)
        return;
      }
      gl.bindTexture(gl.TEXTURE_2D, ysm.boneTex);
      gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, 4, ysm.geo.bones.length, gl.RGBA, gl.FLOAT, mats);
      palLastAppliedTick = T.tick;
      palBoneTexTick = T.tick;
      palLastMats = mats;
      // **ここで再描画を起こさないと palette は永久に画面へ出ない。** この tick の 1 回目の
      // draw は必ず false を返して再構成へ落ちており、解凍が終わるのはその後だから、
      // 誰かが描き直さない限り「間に合った結果」が使われることが無い。読み込み側は
      // 14-03 が同じ理由で notifyAssetReady() を足した (gl.js:1303) が、レコード単位の
      // 解凍側には無く、静止中は 100% ここで落ちていた (2026-08-25 実測)。
      notifyAssetReady();
    }).catch((e) => {
      if (gen !== palGen) return;   // 切り替え中の中断を「失敗」として騒がない
      palPending = false;
      console.error('[SimLab] palette decode に失敗しました (tick ' + T.tick + '):', e);
    });
    return palLastAppliedTick === T.tick;
  }

  // ===========================================================================
  // live palette: 実クライアントの post-geoRender palette を唯一のライブ姿勢源にする。
  // ===========================================================================
  const LIVE_PALETTE_STALE_MS = 1500;
  const livePal = {
    source: null, uuid: null, modelId: null, state: 'off', sourceConnected: false, identity: null,
    frame: null, pending: null, mats: null, mappedToken: 0, uploadedToken: 0,
    nextToken: 0, received: 0, rejected: 0, identityError: null,
  };

  function closeLivePalette(nextState) {
    if (livePal.source) livePal.source.close();
    livePal.source = null;
    livePal.uuid = null;
    livePal.modelId = null;
    livePal.state = nextState || 'off';
    livePal.sourceConnected = false;
    livePal.identity = null;
    livePal.frame = null;
    livePal.pending = null;
    livePal.mats = null;
    livePal.mappedToken = 0;
    livePal.uploadedToken = 0;
    livePal.identityError = null;
  }

  function liveReimuUuid(D) {
    if (!D || !D.entities) return null;
    const direct = D.reimuId == null ? null : D.entities.get(D.reimuId);
    if (direct && direct.uuid) return String(direct.uuid).toLowerCase();
    for (const entity of D.entities.values()) {
      if (entity && entity.role === 'reimu' && entity.uuid) return String(entity.uuid).toLowerCase();
    }
    return null;
  }

  function ensureLivePalette(D) {
    if (!traceIsLive) return;
    const uuid = liveReimuUuid(D);
    const modelId = String(ysm.modelId || '');
    if (!uuid) {
      if (livePal.source) closeLivePalette('target-wait');
      else livePal.state = 'target-wait';
      return;
    }
    if (livePal.source && livePal.uuid === uuid && livePal.modelId === modelId) return;
    closeLivePalette('connecting');
    livePal.uuid = uuid;
    livePal.modelId = modelId;
    if (typeof EventSource === 'undefined' || !window.SimLivePalette) {
      livePal.state = 'unsupported';
      return;
    }
    const source = new EventSource('/api/live-palette?uuid=' + encodeURIComponent(uuid)
      + (modelId ? '&model=' + encodeURIComponent(modelId) : ''));
    livePal.source = source;
    source.onopen = () => { livePal.state = 'waiting'; notifyAssetReady(); };
    source.addEventListener('status', (event) => {
      try {
        const value = JSON.parse(event.data);
        livePal.sourceConnected = value.sourceConnected === true;
        livePal.identity = value.identity || null;
        if (!livePal.sourceConnected) livePal.state = livePal.mats ? 'disconnected-hold' : 'disconnected';
        else if (value.identity && value.identityMatches === false) livePal.state = 'identity-mismatch';
        else if (!livePal.frame) livePal.state = 'waiting';
      } catch (e) {
        livePal.rejected++;
      }
      notifyAssetReady();
    });
    source.addEventListener('frame', (event) => {
      try {
        const decoded = window.SimLivePalette.decode(JSON.parse(event.data), uuid, modelId);
        decoded.token = ++livePal.nextToken;
        livePal.pending = decoded;          // decode が追いつかないときも最新1枚だけ
        livePal.frame = decoded;
        livePal.received++;
        livePal.identityError = null;
        livePal.state = 'ready';
      } catch (e) {
        livePal.rejected++;
        livePal.identityError = String(e && e.message || e);
        livePal.state = 'identity-mismatch';
      }
      notifyAssetReady();
    });
    source.onerror = () => {
      livePal.sourceConnected = false;
      livePal.state = livePal.mats ? 'disconnected-hold' : 'disconnected';
      notifyAssetReady();
    };
  }

  /** 最新 frame を Viewer の bone 順へ fail-closed remap して upload する。 */
  function poseYsmLivePalette() {
    if (livePal.pending) {
      const frame = livePal.pending;
      livePal.pending = null;
      const result = window.YSM.matsFromPalette(ysm.geo.bones, frame.state9, frame.slotOf);
      if (result.missing > 0) {
        livePal.identityError = result.missing + '本のboneが実機layoutに無い';
        livePal.state = 'identity-mismatch';
        livePal.mats = null;               // 古い別layoutも描かない。自動fallbackもしない。
        return false;
      }
      livePal.mats = result.mats;
      livePal.mappedToken = frame.token;
      livePal.identityError = null;
    }
    if (!livePal.mats || livePal.identityError) return false;
    if (livePal.uploadedToken !== livePal.mappedToken) {
      gl.bindTexture(gl.TEXTURE_2D, ysm.boneTex);
      gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, 4, ysm.geo.bones.length,
        gl.RGBA, gl.FLOAT, livePal.mats);
      livePal.uploadedToken = livePal.mappedToken;
      palBoneTexTick = -1;
    }
    return true;
  }

  function livePaletteState() {
    if (!traceIsLive) return 'off';
    if (livePal.identityError || livePal.state === 'identity-mismatch') return 'identity-mismatch';
    if (!livePal.frame) return livePal.state;
    if (!livePal.sourceConnected) return 'disconnected-hold';
    if (Date.now() - livePal.frame.receivedAt > LIVE_PALETTE_STALE_MS) return 'stale-hold';
    return 'ready';
  }

  function livePaletteStatusText() {
    const s = livePaletteState();
    if (s === 'off') return '';
    if (s === 'ready') return 'live palette 受信中';
    if (s === 'stale-hold') return '⚠ live palette stale（最終姿勢を保持）';
    if (s === 'disconnected-hold') return '⚠ live palette 切断（最終姿勢を保持）';
    if (s === 'identity-mismatch') return '⚠ live palette identity不一致（代替姿勢は使わない）';
    if (s === 'target-wait') return 'live palette 対象UUID待ち';
    if (s === 'unsupported') return '⚠ live palette を受信できない';
    if (!livePal.sourceConnected) return '⚠ YSMクライアント未接続（代替姿勢は使わない）';
    return 'live palette frame待ち（代替姿勢は使わない）';
  }

  /**
   * トレースからアニメの経過時間を作る。
   * mod は「今このアニメ」しか送らないので、名前が変わった tick を開始点とみなす。
   *
   * 13-02: 「作り直す」から「伸ばす」へ。animTrack.name[t]/.elapsed[t]/.vars[t] を
   * 絶対tickで直接読む消費側(poseYsm 等)は変えない —— elapsed の裏の Float32Array
   * だけ容量/長さを分けて伸ばし、name/vars は素の配列(index代入で自動的に伸びる)の
   * ままにする。cur/start/vars(=このアニメ区間の状態)は growWalk と同じく境界の
   * 外側(モジュールクロージャ)に持ち回る。
   */
  const animTrack = { name: [], elapsed: new Float32Array(0), vars: [] };
  let animLen = 0, animCur = null, animStart = 0, animVars = {};
  let animBoundary = -1;

  function growAnimTrack(D) {
    const to = D.maxTick;
    if (to < animLen - 1) return; // 既に処理済み
    if (animTrack.elapsed.length < to + 1) {
      let cap = animTrack.elapsed.length || 64;
      while (cap < to + 1) cap *= 2;
      const ne = new Float32Array(cap);
      ne.set(animTrack.elapsed.subarray(0, animLen));
      animTrack.elapsed = ne;
    }
    for (let t = animLen; t <= to; t++) {
      const a = D.frameAt(t, 0).anim;
      if (a) {
        const nm = a.anim && a.anim !== '-' ? a.anim : null;
        if (nm !== animCur) { animCur = nm; animStart = t; }
        // mod が送った molang は「変数への代入」なので、拾って評価器へ渡す。
        // **face も同じ経路に乗せる** —— 表情 (眼サイズ/睫毛/口) の式で、
        // 実際に撃つのは client なので molang フィールドには現れないが、
        // 何を撃つべきかは server が知っていてトレースに書いてくれる。
        // これが無いと目と口が未設定のままになり、顔が実機と違って見える
        // (2026-08-20 にーくら指摘 → jar 側に face を足して解決)。
        for (const src of [a.molang, a.face]) {
          if (!src || src === '-') continue;
          for (const m of src.matchAll(/([A-Za-z_][A-Za-z0-9_.]*)\s*=\s*(-?[0-9.]+)/g)) {
            animVars = Object.assign({}, animVars);
            animVars[m[1].toLowerCase()] = parseFloat(m[2]);
          }
        }
      }
      animTrack.name[t] = animCur;
      animTrack.elapsed[t] = (t - animStart) / 20;
      animTrack.vars[t] = animVars;
    }
    animLen = to + 1;
    animBoundary = to;
  }
  function resetAnimTrack() {
    animTrack.name = []; animTrack.elapsed = new Float32Array(0); animTrack.vars = [];
    animLen = 0; animCur = null; animStart = 0; animVars = {};
    animBoundary = -1;
  }

  // ---------------------------------------------------------------------
  // 13-02: growWalk/growAnimTrack を1つの入口にまとめる。世代(D.key)が変わったとき
  // だけ作り直し(=境界を-1へ戻してから伸ばす。「1回目の伸ばし」は結局フルビルドと
  // 同じ)、同じ世代なら前回の境界から先だけ処理する。巻き戻り(世代は同じなのに
  // maxTickが後退)も同じ扱いにする(poseYsmのysm.simTick巻き戻り検出と同型の
  // 防御——世代キー判定をすり抜けても二重に安全)。index.htmlのload()がD.store.append()
  // の直後にこれを呼ぶ(呼び出し側は「新しいtickぶんだけ処理してほしい」以外を
  // 意識しなくてよい)。
  // ---------------------------------------------------------------------
  let derivedKey = null;
  function growDerived(D) {
    if (D.key !== derivedKey || D.maxTick < walkBoundary || D.maxTick < animBoundary) {
      derivedKey = D.key;
      resetWalk();
      resetAnimTrack();
    }
    growWalk(D);
    growAnimTrack(D);
  }

  /** T-13-08(threat register)のmitigation: 派生物(walk/animTrack)の常駐サイズを
   *  隠さない。288,000 tick(4時間)でFloat32Array1本あたり1.1MBになる計算で、
   *  entity数ぶん積み上がる——bench.mjsの出力に含めることで、伸びっぱなしの
   *  Float32Arrayが実際にどれだけ大きくなっているかを毎回の計測で見える形にする。
   *  walkPos(Map<id,Float32Array>)は各バッファのbyteLength合計、animTrack.elapsedも
   *  同様。name/varsは可変長オブジェクトを含む素の配列なので正確なバイト数は出せない
   *  ——エンティティ数(=概算の上限)だけ添える。 */
  let ysmSteps = 0, ysmCatchups = 0, ysmWorstStep = 0, ysmSkipped = 0;
  function derivedStats() {
    let walkBytes = 0;
    for (const buf of walkPos.values()) walkBytes += buf.byteLength;
    return {
      walkBytes: walkBytes, walkEntities: walkPos.size,
      animBytes: animTrack.elapsed.byteLength, animTicks: animLen,
      // 押し戻しが実際に起きた回数。0 のままなら保持は**効いていない**(配線を疑う)。
      heldReverts: heldReverts, heldCalls: heldCalls, heldKeys: heldKeys,
      // 衣装ボーンを何本押さえているか。0 なら pinScale は**効いていない**。
      costumeBones: (() => { const c = costumeBones(); return c ? c.size : 0; })(),
      hiddenNow: lastHidden.length, hiddenList: lastHidden.slice(),
      costumeList: (() => { const c = costumeBones(); return c ? [...c] : []; })(),
      // いま実際に持っている状態変数の中身 (何が欠けているかを目で見るため)
      roaming: (() => { const o = {}; for (const k in ysm.vars) if (isHeldVar(k)) o[k] = ysm.vars[k]; return o; })(),
      // YSM のばね積分の追いつき歩数。**1 フレームで何 tick ぶん積分し直したか。**
      // ここが大きいと 1 フレームが丸ごと止まる —— しかも費用はセッションの長さに
      // 比例して伸びる(tick 0 から積分し直す経路があるため)。
      ysmSteps: ysmSteps, ysmCatchups: ysmCatchups, ysmWorstStep: ysmWorstStep,
      ysmSkipped: ysmSkipped,
      // アニメライブラリで実機頂点を出せた回数と、出せなかった内訳。
      // **「何割が実機で、何割が再構成か」を隠さないための数字。**
      // pastWindow が大きければ sweep の ticksPerAnim を伸ばすのが効く
      // (notInLib が大きければ、そのアニメが sweep の対象に入っていない)。
      poseLibState: poseLib.state,
      poseLibBytes: poseLib.bytes,
      poseLibEvicted: poseLib.evicted,
      poseLibCapMB: Math.round(LIB_CAP_BYTES / 1048576),
      poseLibAnims: poseLib.byAnim ? poseLib.byAnim.size : 0,
      poseLibHits: poseLibHits,
      poseLibMissNoAnim: poseLibMiss.noAnim,
      poseLibMissNotInLib: poseLibMiss.notInLib,
      poseLibMissPastWindow: poseLibMiss.pastWindow,
      poseLibMissNotLoaded: poseLibMiss.notLoaded,
      poseLibLoadedAnims: poseLib.loaded.size,
      // ライブで false、通常の記録では ?rec=0/1 に従う。smoke test から配線を確認する。
      recordedPoseEnabled: recordingEnabled(),
      liveTrace: traceIsLive,
      livePaletteState: livePaletteState(),
      livePaletteUuid: livePal.uuid,
      livePaletteModelId: livePal.modelId,
      livePaletteFrames: livePal.received,
      livePaletteRejected: livePal.rejected,
      livePaletteAgeMs: livePal.frame ? Math.max(0, Date.now() - livePal.frame.receivedAt) : null,
      livePaletteIdentityError: livePal.identityError,
      // S1b: 今の tick の姿勢の根拠と、run 全体の内訳。
      poseSource: poseSource,
      poseSourceCount: Object.assign({}, poseSourceCount),
    };
  }

  /**
   * 実測 ctrl companion (.ctrl.jsonl) の 1 tick 分から、YSM の animation controller が
   * 読む値を作る。
   *
   * <p><b>onGround はクライアント側の実測でなければならない</b> —— 霊夢は仕様上わずかに浮き、
   * サーバ側トレース (arena-*.jsonl の phys.onG) とは食い違う (CLAUDE.md の判例)。
   * ここを推測すると層が当たらないことを 2026-08-19 に実測で確認した。
   */
  /**
   * その tick の状態を取る。**実測 companion があればそれを、無ければアリーナトレースから補う。**
   *
   * <p>ctrl companion は姿勢の記録と同じ長さ (既定 96 tick ≒ 5 秒) しか無いのに対し、
   * アリーナトレースは全長 (900 tick) ある。窓の外で速度も向きも 0 のままにすると、
   * <b>ばね物理 (髪 / リボン / 胸の揺れ) が止まって「小さな浮遊」が消える</b>。
   * アリーナトレースの {@code pos} / {@code phys} / {@code anim} から同じ値を作れるので、
   * 精度は落ちるが動きは続く。
   *
   * <p><b>onGround だけは意味が違う</b>: companion はクライアント側の実測、
   * アリーナトレースの {@code phys.onG} はサーバ側。霊夢は client では常に浮くので
   * 両者は食い違う。窓の外は近似だと承知して使う。
   */
  function rawStateAt(D, tick) {
    const pi = tick + (poseTrace.base || 0);
    if (poseTrace.ctrlByT) {
      const c = poseTrace.ctrlByT.get(pi);
      if (c) return c;
    }
    // フォールバック: アリーナトレース (D.frameAt は pos だけ疎ストア経由・他は従来どおり)
    const f = D && D.frameAt ? D.frameAt(tick, 0) : null;
    if (!f) return null;
    const p = f.pos && D.reimuId != null ? f.pos.get(D.reimuId) : null;
    if (!p) return null;
    const a = f.anim || {};
    return {
      t: pi, onG: f.phys ? !!f.phys.onG : true,
      x: p.x, y: p.y, z: p.z, yaw: p.yaw || 0, pitch: p.pitch || 0,
      bodyYaw: p.yaw || 0, headYaw: (p.hy != null ? p.hy : p.yaw) || 0,
      sprint: false, crouch: false, shift: false, riding: false, fly: false, sleep: false,
      main: a.main || 'empty', off: a.off || 'empty',
      approx: true,
    };
  }

  function ctrlVarsAt(tick, D) {
    const c = rawStateAt(D, tick);
    const pr = rawStateAt(D, Math.max(tick - 1, 0)) || c;
    if (!c) return null;
    const dx = (c.x || 0) - (pr.x || 0), dy = (c.y || 0) - (pr.y || 0), dz = (c.z || 0) - (pr.z || 0);
    let dyaw = (c.yaw || 0) - (pr.yaw || 0);
    while (dyaw > 180) dyaw -= 360;
    while (dyaw < -180) dyaw += 360;
    const sp = Math.hypot(dx, dz) * 20;
    const jump = c.onG ? 0 : 1;
    const main = String(c.main || "empty");
    const v = {};
    v['ctrl.jump'] = jump;
    v['ctrl.run'] = (!jump && sp > 4.5) ? 1 : 0;
    v['ctrl.walk'] = (!jump && sp > 0.15 && sp <= 4.5) ? 1 : 0;
    v['ctrl.idle'] = (!jump && sp <= 0.15) ? 1 : 0;
    v['ctrl.fly'] = c.fly ? 1 : 0;
    v['ctrl.sneak'] = c.crouch ? 1 : 0;
    v['ctrl.sneaking'] = c.shift ? 1 : 0;
    v['ctrl.sit'] = 0;
    v['ctrl.sleep'] = c.sleep ? 1 : 0;
    v['query.is_riding'] = c.riding ? 1 : 0;
    v['q.all_animations_finished'] = 1;
    v['query.any_animation_finished'] = 1;
    v['v.jumped'] = jump;
    v['ctrl.hold(mainhand,:sword)'] = main.indexOf('sword') >= 0 ? 1 : 0;
    v['ctrl.hold(mainhand,:bow)'] = main.indexOf('bow') >= 0 ? 1 : 0;
    // ばね積分器 (parallel3) の駆動入力
    v['q.ground_speed'] = sp;
    v['q.vertical_speed'] = dy * 20;
    v['q.yaw_speed'] = dyaw * 20;
    v['ysm.head_yaw'] = (c.headYaw || 0) - (c.bodyYaw || 0);
    v['ysm.head_pitch'] = c.pitch || 0;
    const subs = {};
    subs['query.position_delta(0)'] = dx;
    subs['query.position_delta(1)'] = dy;
    subs['query.position_delta(2)'] = dz;
    return { v: v, subs: subs };
  }

  /**
   * 手に持っている物から {@code hold_<slot>:<種類>} のアニメ名を決める。
   *
   * <p><b>YSM の要の機能</b>: 霊夢が {@code netherite_sword} を持つと、YSM は
   * 剣そのものではなく<b>御幣 (Gohei / Gohei3) を代わりに描く</b>
   * (にーくら「こういう、武器を別のものに表示するものがあるのが ysm の特徴だ」)。
   *
   * <p>その差し替えは scale で行われる —— {@code pre_parallel0} が Gohei / Gohei3 を
   * {@code scale = 0} で<b>既定で隠し</b>、{@code hold_mainhand:sword1} /
   * {@code hold_offhand:sword} が {@code scale = 1-v.roaming.jian} で<b>出し直す</b>。
   * だから hold 系を積まないと霊夢の御幣は永久に出ない。
   * (2026-08-19 実測: 記録には Gohei3 の固有 UV 矩形が 126/126 写っているのに
   *  Viewer は出していなかった)
   *
   * <p>これは「姿勢のブレンド」ではなく<b>どの武器モデルを表示するか</b>の話なので、
   * オフハンドについては animation controller と独立に効かせる。
   *
   * <p><b>2026-08-20 以降、メインハンドについては既定でこの関数は呼ばれない。</b>
   * 実機のパックには {@code player.pre_hold} という状態機械があり、そちらが正解を持っている
   * ({@link CTL_LAYERS} の javadoc に実測値つきで書いた)。この関数のメインハンド分岐は
   * {@code ?ctl=0} の退避経路のためだけに残してある。
   *
   * <p><b>オフハンドはこの関数のままでよい。</b> パックの controller は 4 本
   * ({@code player.parallel_7} / {@code post_main} / {@code pre_hold} / {@code pre_main}) で、
   * <b>{@code pre_hold} はメインハンド専用</b>。オフハンド用の状態機械は存在しない。
   *
   * <p><b>次の人へ</b>: この関数でメインハンドの握りを組み立て直そうとしないこと。
   * 2026-08-20 に条件を 2 回足して 2 回とも外している (下の分岐のコメント参照)。
   * 状態機械は {@code v.no_hold} / {@code ctrl.run} / 弓 / 抜刀→構えの時間遷移を
   * すべて持っており、手で書き写すと必ずどれかを取りこぼす。
   */
  function holdAnimFor(slot, item, vars) {
    const s = String(item || 'empty');
    if (s === 'empty') return 'hold_' + slot + ':empty';
    if (s.indexOf('slashblade') >= 0) return 'hold_' + slot + ':slashblade';
    if (s.indexOf('crossbow') >= 0) return 'hold_' + slot + ':crossbow';
    if (s.indexOf('bow') >= 0) return 'hold_' + slot + ':bow';
    if (s.indexOf('sword') >= 0) {
      // **v.no_hold==1 なら握らない。** パックの pre_hold コントローラは
      //   default -> sword :  ctrl.hold('mainhand', ':sword') && v.no_hold != 1
      //   sword/sword_end/sword_run -> default :  v.no_hold == 1
      // と書かれており、mod は構え技の間これを 1 にする (CLAUDE.md の判例:
      // 「剣を持つと出る hold_mainhand アニメは v.no_hold=1 で抑止」)。
      //
      // 実害 (2026-08-20、にーくら): 夢想封印中に**左腕だけ折れる**。
      // 実測すると 900 tick 中 689 tick が v.no_hold=1 で、その間ずっと
      // 剣の握りポーズを腕に当てていた —— 構えのアニメと衝突して腕が壊れる。
      if (slot === 'mainhand' && vars && vars['v.no_hold'] === 1) {
        return 'hold_mainhand:empty';
      }
      // **この分岐は誤っている。** 既定 (?ctl=1 相当) では呼ばれないので残してあるが、
      // ?ctl=0 の退避経路で使うときは次の 2 点を承知して使うこと:
      //
      //   (a) sword1 は<b>抜刀の一瞬</b>で、前腕を -72° 曲げる。剣を持って立っている
      //       定常状態は sword_end (-1.6°)。ここは常に sword1 を返すので、
      //       抜刀モーションを再生し続けることになる。
      //   (b) v.wuqi による sword1 / sword2 の選び分けも誤り。実機の状態機械は
      //       [sword] 状態で <b>sword1 と sword2 を同時に</b>再生しており、
      //       どちらか一方を選んではいない。
      //
      // 正しくは pre_hold 状態機械に委ねる (既定)。ここを直すのではなく、
      // CTL_LAYERS を ON のままにするのが正解。
      if (slot === 'mainhand') {
        const w = vars && typeof vars['v.wuqi'] === 'number' ? vars['v.wuqi'] : 0;
        return w === 1 ? 'hold_mainhand:sword2' : 'hold_mainhand:sword1';
      }
      return 'hold_' + slot + ':sword';
    }
    if (s.indexOf('axe') >= 0) return 'hold_' + slot + ':axe';
    if (s.indexOf('pickaxe') >= 0) return 'hold_' + slot + ':pickaxe';
    if (s.indexOf('shovel') >= 0) return 'hold_' + slot + ':shovel';
    if (s.indexOf('hoe') >= 0) return 'hold_' + slot + ':hoe';
    if (s.indexOf('shield') >= 0) return 'hold_' + slot + ':shield';
    if (s.indexOf('trident') >= 0) return 'hold_' + slot + ':spear';
    return 'hold_' + slot + ':empty';
  }

  /**
   * その tick のボーン行列を作ってテクスチャへ送る。tick が変わったときだけ計算する。
   *
   * <p>実機に寄せるため、素の「1 本のアニメを当てる」から次の 3 つを足してある:
   * <ol>
   *   <li><b>ばね積分器</b> —— parallel3 の timeline を毎 tick 実行する。
   *       ysm.vars を<b>tick を跨いで持ち回す</b>のが要点 (毎 tick 作り直すと
   *       髪 / リボン / 胸の揺れものが永久に静止したままになる)</li>
   *   <li><b>animation controller</b> —— 実測 ctrl.* で状態機械を回し、選ばれた層を積む</li>
   *   <li><b>ブレンド重み</b> —— コントローラ層に CONTROLLER_WEIGHT_FIT を掛ける。
   *       全重みで足すと混ぜすぎになる (94tick の実測で 0.45 が最良、全体 8.3% 改善)</li>
   * </ol>
   * タイムラインを巻き戻したときは積分をやり直す (ばねは経路に依存するため)。
   * ctrl companion を持たない古いトレースでは従来どおりの経路へ落ちる。
   */
  function poseYsm(D, T, p) {
    if (ysm.state !== 'ready') return false;

    // 水槽ライブはこの1経路だけ。未着・stale・切断・identity不一致のどれでも、録画頂点や
    // ysm.js 再構成へフレーム単位で切り替えない。正常frameを一度得た後は最終姿勢を保持する。
    if (traceIsLive) {
      if (!poseYsmLivePalette()) {
        ysmLastPoseSource = 'missing';
        return false;
      }
      ysmLastPoseSource = 'livePalette';
      ysm.lastKey = T.tick;
      return true;
    }

    // --- palette (14-01): 間に合っていれば最優先。間に合っていなければ黙って下へ落ちる。 ---
    if (PAL_MODE && poseYsmPalette(T)) {
      ysmLastPoseSource = 'palette';
      ysm.lastKey = T.tick;
      return true;
    }
    ysmLastPoseSource = 'reconstructed';

    if (ysm.lastKey === T.tick) return true;
    const Y = window.YSM;

    // --- 既定: 従来どおりの経路 (2026-08-19 以前と同一) ---
    if (!SIM_PIPELINE) {
      const v0 = Object.assign({}, animTrack.vars[T.tick] || {});
      v0['ysm.head_yaw'] = (p && p.hy) || 0;
      v0['ysm.head_pitch'] = (p && p.pitch) || 0;
      const ls = ysm.base.slice();
      const n0 = animTrack.name[T.tick];
      const a0 = n0 && ysm.anims[n0];
      if (a0) {
        // 生の Map は下地扱いで衣装 scale を通す。直接アクションは必ずラップする。
        ls.push({ map: Y.sampleAnimation(a0, animTrack.elapsed[T.tick], v0), weight: 1, scaleWeight: 1 });
      }
      const B0 = Y.poseBones(ysm.geo.bones, ls, { pinScale: costumeBones() });
      gl.bindTexture(gl.TEXTURE_2D, ysm.boneTex);
      gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, 4, ysm.geo.bones.length, gl.RGBA, gl.FLOAT, B0);
      palBoneTexTick = -1;   // boneTex を奪った。palette は載せ直しが要る
      ysm.lastKey = T.tick;
      return true;
    }

    // 巻き戻し / 初回は作り直してから積分し直す
    if (T.tick < ysm.simTick || ysm.simTick < 0) {
      ysm.vars = {};
      ysm.ctl = ysm.ctlJson ? Y.initControllers(ysm.ctlJson) : null;
      ysm.simTick = -1;
      // ばね定数を敷く (parallel2 等の timeline を 1 回)
      Object.assign(ysm.vars, ROAMING_DEFAULTS);
      for (const n of ysm.baseNames) Y.runTimeline(ysm.anims[n], ysm.vars, {});
    }

    /* **追いつきに上限を掛ける。**
     *
     * ここは ysm.simTick から T.tick まで 1 tick ずつ、ばねの積分と状態機械を回す。
     * 上限が無いと歩数は「霊夢が描かれていなかった間」そのもので、巻き戻せば tick 0
     * からやり直す。**費用がセッションの長さに比例して伸びる。**
     * 実測(2026-08-23、にーくら「多くのモブと戦った後に 60fps へ落ちる」):
     * 1 フレームで **938 tick** ぶんを積分していた —— その 1 フレームは丸ごと止まる。
     *
     * ばねは収束するので、遠い過去まで遡って積分しても**見た目には何も足さない**。
     * 2 秒(40 tick)も回せば髪もリボンも落ち着く。それ以上は捨てる ——
     * 捨てた事実は ysmSkipped に数え、derivedStats から読めるようにする
     * (黙って端折らない)。40 は「揺れものの収束時間」の見積もりであって測定値ではない。
     * 揺れが飛んで見えるなら、まずここを上げる。 */
    const CATCHUP_MAX = 40;
    if (T.tick - ysm.simTick > CATCHUP_MAX) {
      ysmSkipped += (T.tick - ysm.simTick) - CATCHUP_MAX;
      ysm.simTick = T.tick - CATCHUP_MAX;
    }
    let active = [];
    const steps0 = T.tick - ysm.simTick;
    if (steps0 > 0) { ysmSteps += steps0; ysmCatchups++; if (steps0 > ysmWorstStep) ysmWorstStep = steps0; }
    for (let t = ysm.simTick + 1; t <= T.tick; t++) {
      const cv = ctrlVarsAt(t, D);
      // 既定 → mod が送った値 の順で重ねる (mod が送ってきたらそちらが勝つ)。
      for (const k in ROAMING_DEFAULTS) if (!(k in ysm.vars)) ysm.vars[k] = ROAMING_DEFAULTS[k];
      Object.assign(ysm.vars, animTrack.vars[t] || {});
      if (cv) Object.assign(ysm.vars, cv.v);
      // **アニメを回す前に控える。** ここまでが「指示された状態」。
      const _held = holdSnapshot(ysm.vars);
      const _sent = animTrack.vars[t] || null;
      const _cvv = cv ? cv.v : null;
      // ばね積分 (timeline を持つ下地だけが実際に動く)
      for (const n of ysm.baseNames) Y.runTimeline(ysm.anims[n], ysm.vars, cv ? cv.subs : {});
      applyHeld(ysm.vars, _held, _sent, _cvv);
      // **mod が送った値を、下地アニメの後に載せ直す。**
      // YSM の parallel 系アニメは同じ変数へ代入し直すので、先に置くと消される。
      // 実測 (2026-08-20): トレースは v.Ryanxs=1.2 を送っているのに、この行が無いと
      // ysm.vars 上では 1 に戻っていた（眼サイズが実機と違う原因）。
      // v.roaming.yan も同様に 4 → 6 へ書き換えられていた。
      // mod が明示的に送った値は「霊夢がこうあるべき」という指示なので、下地より強い。
      // 設定値 (v.roaming.*) も載せ直す。**これはプレイヤーが YSM の UI で選んだ設定**で、
      // アニメが書き換えてよいものではない。実測 (2026-08-20): 下地アニメが
      // v.roaming.yan を 4 → 6 に書き換えており、実機で写っていた Eyes5 (yan=4) と
      // 違う目が描かれていた。mod が明示的に送った tick ではそちらを優先する。
      for (const k in ROAMING_DEFAULTS) {
        if (!animTrack.vars[t] || !(k in animTrack.vars[t])) ysm.vars[k] = ROAMING_DEFAULTS[k];
      }
      if (animTrack.vars[t]) Object.assign(ysm.vars, animTrack.vars[t]);
      if (ysm.ctl && CTL_LAYERS) {
        active = Y.stepControllers(ysm.ctl, ysm.vars, 0.05, { weightScale: Y.CONTROLLER_WEIGHT_FIT });
        // **controller の後にも押し戻す。** 状態機械も同じ名前へ代入し直すので、
        // 下地の後だけでは攻撃モーションで崩れる (にーくら 2026-08-25 の症状)。
        applyHeld(ysm.vars, _held, _sent, _cvv);
      }
    }
    ysm.simTick = T.tick;

    // 描画用の変数。ctrl companion があるときは頭の相対回転もそこから来ている。
    const vars = Object.assign({}, ysm.vars);
    if (!poseTrace.ctrlByT) {
      vars['ysm.head_yaw'] = (p && p.hy) || 0;
      vars['ysm.head_pitch'] = (p && p.pitch) || 0;
    }

    const layers = ysm.baseNames.map((n) => Y.sampleAnimation(ysm.anims[n], 0, vars));
    const nm = animTrack.name[T.tick];
    const a = nm && ysm.anims[nm];
    if (a) {
      // 下地の衣装選択は残し、このアクションから来た衣装 scale だけを pinScale で止める。
      layers.push({ map: Y.sampleAnimation(a, animTrack.elapsed[T.tick], vars), weight: 1, scaleWeight: 1 });
    }
    // 手持ちによる武器差し替え。controller を回しているときは pre_hold がメインハンドを
    // 担当するので、こちらは重複しないようオフハンドだけにする。
    const cRow = rawStateAt(D, T.tick);
    if (cRow) {
      const wanted = [];
      if (!(ysm.ctl && CTL_LAYERS)) wanted.push(holdAnimFor('mainhand', cRow.main, vars));
      wanted.push(holdAnimFor('offhand', cRow.off, vars));
      for (const nm2 of wanted) {
        const an2 = ysm.anims[nm2];
        if (an2) layers.push({ map: Y.sampleAnimation(an2, 0, vars), weight: 1, scaleWeight: 1 });
      }
    }

    for (const e of active) {
      const an = ysm.anims[e.anim];
      if (!an) continue;
      layers.push({
        map: Y.sampleAnimation(an, e.elapsed, vars),
        weight: e.weight === undefined ? 1 : e.weight,
        // scale (表示の ON/OFF) には当てはめ定数を掛けない。上の ysm.js の注記を参照
        scaleWeight: e.scaleWeight === undefined ? (e.weight === undefined ? 1 : e.weight) : e.scaleWeight,
      });
    }

    const B = Y.poseBones(ysm.geo.bones, layers, { pinScale: costumeBones() });
    // **いま消えているボーンを記録する。** 「技に入ると服が変わる」を、目ではなく
    // 名前の集合で見るため (2026-08-25)。行列の基底ベクトルの長さが 0 なら消えている。
    try {
      const bs = ysm.geo.bones; const cur = [];
      for (let i = 0; i < bs.length; i++) {
        const o = i * 16;
        const n0 = Math.hypot(B[o], B[o+1], B[o+2]);
        if (n0 < 1e-3) cur.push(bs[i].name);
      }
      lastHidden = cur;
    } catch (e) { /* 測れなくても描画は続ける */ }
    gl.bindTexture(gl.TEXTURE_2D, ysm.boneTex);
    gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, 4, ysm.geo.bones.length, gl.RGBA, gl.FLOAT, B);
    palBoneTexTick = -1;   // boneTex を奪った。palette は載せ直しが要る
    ysm.lastKey = T.tick;
    return true;
  }

  // ===========================================================================
  // 部屋とブロック (ここだけは自前。単純な立方体なので取り違えようがない)
  // ===========================================================================
  const CORNERS = [[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0,0,1],[1,0,1],[1,1,1],[0,1,1]];
  const VERTEX_ORDER = [[5,4,0,1],[2,3,7,6],[1,0,3,2],[4,5,6,7],[0,4,7,3],[5,1,2,6]];

  function pushCube(out, x, y, z, w, h, d) {
    const P = CORNERS.map((c) => [x + c[0]*w, y + c[1]*h, z + c[2]*d]);
    const uv = [1,0, 0,0, 0,1, 1,1];
    for (let i = 0; i < 6; i++) {
      const vo = VERTEX_ORDER[i];
      const p = [P[vo[0]], P[vo[1]], P[vo[2]], P[vo[3]]];
      const n = norm(cross(sub(p[1], p[0]), sub(p[2], p[1])));
      for (const tri of [[0,1,2], [0,2,3]]) {
        for (const k of tri) {
          out.push(p[k][0], p[k][1], p[k][2], uv[k*2], uv[k*2+1], n[0], n[1], n[2], 1, 1, 1);
        }
      }
    }
  }

  // ---------------------------------------------------------------------------
  // ブロックも MC が吐いたものを使う。
  // renderSingleBlock の出力なので、草ブロックの面ごとテクスチャ / 階段やハーフの形 /
  // 草・葉のバイオーム着色 (頂点色) が全部そのまま入っている。UV はブロックアトラスを指す。
  // ---------------------------------------------------------------------------
  let blockDump = null;          // { "minecraft:stone": {verts:[...]}, ... }
  let blockDumpState = 'idle';
  let rebuildBlocks = null;      // 読み込み後に呼ぶ再構築

  function loadBlockDump() {
    if (blockDumpState !== 'idle') return;
    blockDumpState = 'loading';
    fetch('/api/blocks')
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error('未書き出し'))))
      .then((j) => {
        blockDump = j;
        blockDumpState = 'ready';
        if (rebuildBlocks) rebuildBlocks();
      })
      .catch(() => { blockDumpState = 'missing'; });
  }

  function buildChamber(meta) {
    // 格子は床ブロックの**上面**に敷く。floorY は床ブロックの座標なので、そこへ線を引くと
    // 1 マス床に埋まり、モブが線の上に浮いて見える（2026-08-20 実測: 床 y=64 の占有は
    // 64..65、エンティティの足元は y=65。線だけ 64 にあった）。
    // Minecraft の 1 ブロック = 1m 格子と目で一致させるための +1。
    // 水平は元から整数座標の 1 マス間隔で正しい —— ずれていたのは高さだけ。
    // **壁の高さは世界に合わせる。** 2026-08-20 からここは H=16 の枠を描いていたが、
    // 世界の側には壁が 1 個も無かった (2026-08-25 実測: SimArena の setBlock は床と
    // シナリオの blocks だけで、壁を置く経路が存在しなかった)。floorWallHeight は
    // SimArena が「実際に置いた壁の高さ」として出すもので、0 は「枠は描くが当たり判定は
    // 無い」を意味する。無い壁を在るように描かない —— 監視カメラは嘘をつかない。
    const wallH = meta.floorWallHeight || 0;
    const solid = wallH > 0;
    const R = meta.floorRadius || 24, H = solid ? wallH : 16, y = (meta.floorY || 64) + 1;
    const ox = meta.originX || 0, oz = meta.originZ || 0;
    // アニメブラウザ (S6) が霊夢を立たせる場所。チャンバーと同じ床を使う。
    stage = { x: ox, y: y, z: oz };
    const v = [];
    const seg = (a, b, c) => v.push(a[0],a[1],a[2],c[0],c[1],c[2],c[3], b[0],b[1],b[2],c[0],c[1],c[2],c[3]);
    const fine = [0.16,0.16,0.19,1], big = [0.26,0.26,0.31,1], edge = [0.78,0.78,0.83,1];
    // 当たり判定のある壁は床の格子と同じ明るさで、絵だけの枠は暗く落とす。
    const wfine = solid ? fine : [0.09,0.09,0.11,1];
    const wbig  = solid ? big  : [0.14,0.14,0.17,1];
    const walls = [[0, oz-R], [0, oz+R], [1, ox-R], [1, ox+R]];
    for (let i = -R; i <= R; i++) {
      const c = i % 8 === 0 ? big : fine;
      seg([ox+i, y, oz-R], [ox+i, y, oz+R], c);
      seg([ox-R, y, oz+i], [ox+R, y, oz+i], c);
      const wc = i % 8 === 0 ? wbig : wfine;
      for (const w of walls) {
        if (w[0] === 0) seg([ox+i, y, w[1]], [ox+i, y+H, w[1]], wc);
        else seg([w[1], y, oz+i], [w[1], y+H, oz+i], wc);
      }
    }
    for (let h = 0; h <= H; h++) {
      const c = h % 8 === 0 ? wbig : wfine;
      for (const w of walls) {
        if (w[0] === 0) seg([ox-R, y+h, w[1]], [ox+R, y+h, w[1]], c);
        else seg([w[1], y+h, oz-R], [w[1], y+h, oz+R], c);
      }
    }
    const cor = [[ox-R,oz-R],[ox+R,oz-R],[ox+R,oz+R],[ox-R,oz+R]];
    for (let i = 0; i < 4; i++) {
      const a = cor[i], b = cor[(i+1)%4];
      seg([a[0],y,a[1]], [b[0],y,b[1]], edge);
      seg([a[0],y,a[1]], [a[0],y+H,a[1]], edge);
      seg([a[0],y+H,a[1]], [b[0],y+H,b[1]], [0.4,0.4,0.45,1]);
    }
    const data = new Float32Array(v);
    return makeMesh([{ loc: LOC.pos, n: 3 }, { loc: LOC.col, n: 4 }], data, data.length / 7);
  }

  function buildBlocks(meta) {
    const ox = meta.originX || 0, oz = meta.originZ || 0;
    const list = meta.blocks || [];

    // 吸い出し済みなら、それを各座標へ複製する (1 ブロック分の頂点は 0..1 の空間に入っている)
    if (blockDump) {
      const verts = [];
      let missing = 0;
      for (const b of list) {
        const src = blockDump[b.block];
        if (!src || !src.verts) {
          if (b.block !== 'minecraft:barrier') missing++;
          continue;
        }
        const v = src.verts;
        for (let x = b.x0; x <= b.x1; x++) {
          for (let y = b.y0; y <= b.y1; y++) {
            for (let z = b.z0; z <= b.z1; z++) {
              const dx = ox + x, dy = y, dz = oz + z;
              for (let i = 0; i < v.length; i += VSTRIDE) {
                verts.push(v[i] + dx, v[i+1] + dy, v[i+2] + dz);
                for (let k = 3; k < VSTRIDE; k++) verts.push(v[i+k]);
              }
            }
          }
        }
      }
      if (missing) status = `${missing} 種のブロックが未書き出し`;
      if (!verts.length) return [];
      const data = new Float32Array(verts);
      return [{ texId: '@blockatlas', mesh: makeMesh(TEX_ATTRS, data, data.length / VSTRIDE) }];
    }

    // 未書き出しのときの代替: 1 枚のテクスチャを 6 面に貼る (草ブロック等は正しくならない)
    const groups = new Map();
    for (const b of list) {
      const texId = BLOCK_TEX[b.block] !== undefined ? BLOCK_TEX[b.block]
        : `minecraft:textures/block/${b.block.split(':').pop()}.png`;
      if (!texId) continue;
      if (!groups.has(texId)) groups.set(texId, []);
      const out = groups.get(texId);
      for (let x = b.x0; x <= b.x1; x++)
        for (let y = b.y0; y <= b.y1; y++)
          for (let z = b.z0; z <= b.z1; z++) pushCube(out, ox + x, y, oz + z, 1, 1, 1);
    }
    const out = [];
    for (const [texId, verts] of groups) {
      const data = new Float32Array(verts);
      out.push({ texId, mesh: makeMesh(TEX_ATTRS, data, data.length / VSTRIDE) });
    }
    return out;
  }

  let bbMesh = null;
  function billboardMesh() {
    if (bbMesh) return bbMesh;
    bbMesh = makeMesh([{ loc: LOC.corner, n: 2 }, { loc: LOC.uv, n: 2 }], new Float32Array([
      -1,-1, 0,1,   1,-1, 1,1,   1,1, 1,0,
      -1,-1, 0,1,   1,1, 1,0,   -1,1, 0,0,
    ]), 6);
    return bbMesh;
  }

  // ===========================================================================
  // 描画
  // ===========================================================================
  function setTrace(D) {
    // 早期 return より先に更新する。同じ run の再接続でもライブ判定だけは常に最新にする。
    const nextTraceIsLive = !!D.tracePath;
    if (nextTraceIsLive !== traceIsLive) closeLivePalette(nextTraceIsLive ? 'target-wait' : 'off');
    traceIsLive = nextTraceIsLive;
    if (currentKey === D.key) return;
    currentKey = D.key;
    // 別の記録に変わったら「死んだ印」を捨てる —— entity id は記録をまたいで
    // 使い回されるので、残すと新しい水槽の生きているモブが倒れて出る。
    DEATH_AT.clear(); SOMER_AT.clear();
    const meta = D.meta || {};
    meshes.chamber = buildChamber(meta);
    meshes.blocks = buildBlocks(meta);
    // ブロックの吸い出しは非同期。届いたら組み直す。
    rebuildBlocks = () => { meshes.blocks = buildBlocks(meta); };
    loadBlockDump();
    // 13-02: walk/animTrackはもうここで作らない。D.gen導入によりD.keyがライブ中
    // 安定するようになったので、この早期returnが実際に効くようになった(以前は
    // D.key=name+'#'+D.maxTickがライブで毎秒変わっていたためすり抜けていた)——
    // つまりsetTrace自体が「新しいトレースが開かれたときにだけ動く」ようになった。
    // walk/animTrackは行が増えるたびに growDerived(D) が(load()からD.store.append()の
    // 直後に)個別に伸ばす。setTraceがここで呼ぶと「毎秒作り直す」に逆戻りするので
    // 呼ばない。
    ysm.lastKey = -1;
    // **新しいトレースを開いたときだけ**ここへ来る (setTrace は毎フレーム呼ばれるが
    // 上で世代を見て早期に返っている)。アニメブラウザの1コマ表示はここで畳む ——
    // 二つの絵が混ざらないように。毎フレーム消すと選んだ瞬間に消える (2026-08-24 に踏んだ)。
    animPreview = null;
    loadYsm();
    // **表示名ではなく実パスで引く。** ライブは D.path に「水槽（ライブ）」という
    // 表示名を入れる (index.html の resetLiveState) ので、これを companion の解決へ
    // そのまま渡すと /api/pose も /api/palette も必ず 404 になる —— ライブでは
    // palette が一度も起動しない原因だった (2026-08-25 の審査で判明)。
    const tracePath = D.tracePath || D.path;
    resetPoseTrace();
    if (recordingEnabled()) loadPoseTrace(tracePath);
    // palette (14-03): `?pal=1` (実 companion) はトレースごとに読み直す。golden fixture は
    // トレースに依らないので対象外 (loadPalette 冒頭で1度だけロード済み、ここでは触らない)。
    if (PAL_MODE && !PAL_IS_FIXTURE) {
      resetPaletteState();
      if (!traceIsLive) loadPalette(tracePath);
    }
    // ライブラリは**トレースに依らない** (アニメ名で引くので、どの run でも同じものを使う)。
    // だから resetPoseTrace の対象外で、1 回読んだら読み直さない。
    // ヒット統計だけはトレースごとに測りたいので、ここで戻す。
    poseLibHits = 0;
    poseLibMiss.noAnim = 0;
    poseLibMiss.notInLib = 0;
    poseLibMiss.pastWindow = 0;
    poseLibMiss.notLoaded = 0;
    for (const k of Object.keys(poseSourceCount)) poseSourceCount[k] = 0;
    poseSource = 'missing';
    lastCountedTick = -1;
    lastCountedSource = 'missing';
    loadPoseLibrary();
  }

  // lookAt はもうここには無い —— カメラの唯一の定義元は pick.js の SimPick。
  // 「一つの定義」を守るため、使われなくなったコピーをここに残さない。

  /**
   * アニメブラウザ (S6) の 1 コマを描く。**要求されたコマだけを描き、無ければ何も描かない。**
   * 取得中に「近いコマ」で代用すると、動いていないのに動いて見える嘘になる
   * (`poseTraceParts` の注記と同じ理由)。
   */
  function drawAnimPreview(uModel, uHead, uFlash) {
    animPreview.status = 'ライブラリ未取得';
    if (poseLib.state !== 'ready') return;
    const r = poseLib.byAnim.get(animPreview.name);
    if (!r) { animPreview.status = 'そのアニメはライブラリに無い'; return; }
    const n = r.to - r.from + 1;
    const k = Math.max(0, Math.min(n - 1, animPreview.frame | 0));
    animPreview.frames = n;
    const slot = r.from + k;
    if (!poseLib.frames.get(slot)) {
      if (!poseLib.failed.has(animPreview.name)) requestAnimFrames(animPreview.name);
      animPreview.status = '取得中…';
      return;
    }
    const parts = cachedPoseParts(slot, poseLib);
    const headModel = model(poseLib.header.type);
    gl.uniform1f(uFlash, 0);
    gl.uniformMatrix4fv(uModel, false, M.trans(stage.x, stage.y, stage.z));
    gl.uniformMatrix4fv(uHead, false, M.ident());
    for (const part of parts) {
      gl.bindTexture(gl.TEXTURE_2D, tex(part.texId || poseLib.texId || headModel.texId).tex);
      gl.bindVertexArray(part.mesh.vao);
      gl.drawArrays(gl.TRIANGLES, 0, part.mesh.count);
    }
    animPreview.status = '実機頂点';
    poseSource = 'library';
  }

  function render(D, T, cam, W, H) {
    if (!gl) return;
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    if (canvas.width !== Math.round(W*dpr) || canvas.height !== Math.round(H*dpr)) {
      canvas.width = Math.round(W*dpr); canvas.height = Math.round(H*dpr);
    }
    gl.viewport(0, 0, canvas.width, canvas.height);
    gl.clearColor(0.043, 0.043, 0.047, 1);
    gl.depthMask(true);
    gl.disable(gl.BLEND);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

    // カメラは SimPick が唯一の定義元 (pick.js)。ここで組み立て直さない ——
    // 床クリックの逆写像が「絵と違う行列」を invert する事故を、実行時に
    // 比較できるようにするのが lastVP() の役目 (must_haves: SimGL.lastVP() ===
    // SimPick.viewProjection(cam,W,H))。
    const VP = SimPick.viewProjection(cam, W, H);
    lastVP = VP;
    // 弾のビルボード基底 (uRight/uUp) も同じ SimPick から取る。ローカルの lookAt は
    // commit b044f129 で削除済みだが、drawBullets への受け渡しが更新されておらず
    // `view is not defined` で落ちていた(2026-08-21、quick 260821-7d4 で発覚。
    // フレームが1つでも在ると必ず落ちるため、水槽が空でない限り毎回描画が例外で止まっていた)。
    const camB = SimPick.camBasis(cam);

    // チャンバー(グリッド/床/壁)とブロックは D.store にエンティティが1体も
    // いなくても描く —— トレース未読込・水槽が空でも「水槽そのもの」は常に
    // 見えている必要がある(HANDOFF §1: 「誰もいない」と「壊れている」を同じ絵にしない)。
    // setTrace(D) は meta==null でも既定値(floorY=64 等)で meshes.chamber を作るので、
    // ここでエンティティの有無を条件にする必要が無い(13-02で密フレームD.framesは
    // 撤去済み。この節はその後もチャンバー描画自体には手を入れていない)。
    gl.useProgram(progLine);
    gl.uniformMatrix4fv(gl.getUniformLocation(progLine, 'uVP'), false, VP);
    if (meshes.chamber) { gl.bindVertexArray(meshes.chamber.vao); gl.drawArrays(gl.LINES, 0, meshes.chamber.count); }

    gl.useProgram(progTex);
    const uModel = gl.getUniformLocation(progTex, 'uModel');
    const uHead = gl.getUniformLocation(progTex, 'uHead');
    const uFlash = gl.getUniformLocation(progTex, 'uFlash');
    gl.uniformMatrix4fv(gl.getUniformLocation(progTex, 'uVP'), false, VP);
    gl.uniform1i(gl.getUniformLocation(progTex, 'uTex'), 0);
    gl.uniform1f(uFlash, 0);   // 既定は素の色。赤くするのは entity ごとに明示したときだけ
    gl.activeTexture(gl.TEXTURE0);

    for (const b of (meshes.blocks || [])) {
      gl.bindTexture(gl.TEXTURE_2D, tex(b.texId).tex);
      gl.uniformMatrix4fv(uModel, false, M.ident());
      gl.uniformMatrix4fv(uHead, false, M.ident());
      gl.bindVertexArray(b.mesh.vao);
      gl.drawArrays(gl.TRIANGLES, 0, b.mesh.count);
    }

    // --- アニメブラウザ (S6): トレースより先に判定する ---
    // **トレースも水槽も要らない。** ライブラリの実機頂点を 1 コマ貼るだけ。
    // 「実機を起動せずに YSM アニメを確認する」がここで満たされる。
    if (animPreview) {
      drawAnimPreview(uModel, uHead, uFlash);
      gl.bindVertexArray(null);
      return;
    }

    // spawn 行が後着するライブでは setTrace の時点に UUID がまだ無い。毎フレーム確認するが、
    // 同じ UUID の EventSource は使い回すので接続を増やさない。
    if (traceIsLive) ensureLivePalette(D);

    // ここから先はフレームデータ(記録された tick)が要る。無ければチャンバーだけの
    // 空の水槽で終わる —— それが正しい絵 (トレース未読込 / 召喚前)。
    const f = D.frameAt(T.tick, T.partial);
    if (!f) { gl.bindVertexArray(null); return; }
    // 被弾中の者たちを 1 フレームに 1 回だけ引く (entityFx の説明を参照)。
    const hurt = hurtMapAt(D, T.tick);

    // --- 霊夢 (優先): 姿勢トレースがあれば記録済み頂点をそのまま貼る (D-01)。
    //     ysm.js の再合成 (skinned 経路) より先に判定する。
    //     グループ表があれば複数パーツを描画順どおりに描く (quick 260818-oq4)。 ---
    let reimuHandled = false;
    // S1b: この tick の姿勢の根拠。下の経路が上書きし、どこも通らなければ missing のまま。
    poseSource = 'missing';
    // **優先順: palette → この run の録画 → アニメライブラリ → ysm.js 再構成。**
    // palette が先頭なのは 2026-08-25 のにーくら判定 (adopt)。4ペインを実際に見た上での
    // 「④ palette が一番。録画が一番 ysm の molang が異なっていたから」という理由で、
    // 録画は実機の頂点そのものではあるが、その瞬間の molang 状態が他と食い違っていた。
    // palette がこの tick を持っているときは頂点経路へ入らず、skinned 側へ通す。
    if (recordingEnabled() && !paletteCanServe(T) &&
        (poseTrace.state === 'ready' || poseLib.state === 'ready')) {
      for (const [id, p] of f.pos) {
        const e = D.entities.get(id);
        if (!e || e.role !== 'reimu') continue;
        // run 録画はその run そのものなので頂点経路の中では最優先。無ければライブラリを
        // アニメ名で引く (録画していない run でも実機頂点が出せる)。
        // どちらも出せなければ null を返して再構成へ落ちる —— 古い1枚を貼り続けない。
        let src = poseTrace;
        let parts = poseTraceParts(T.tick);
        if (!parts) {
          parts = poseLibParts(T.tick);
          src = poseLib;
        }
        if (!parts) break;
        const headModel = model(src.header.type);
        // uModel/uHead/行列計算はループの外で1回だけ (グループが増えても再計算しない)。
        const fxR = entityFx(e, p, T.tick, T.partial, hurt);
        const somR = somersaultRad(e.id, f.phys && f.phys.somer, T.tick, T.partial);
        let mm = M.mul(M.trans(p.x, p.y, p.z), M.rotY(-p.yaw * Math.PI / 180));
        if (fxR.tilt > 0) mm = M.mul(mm, M.rotZ(MIRRORED * fxR.tilt));
        if (somR > 0) mm = M.mul(mm, M.rotX(MIRRORED * somR));   // 宙返り(縦回転)
        gl.uniform1f(uFlash, fxR.flash);
        const hm = headMatrix(headModel, p);
        gl.uniformMatrix4fv(uModel, false, mm);
        gl.uniformMatrix4fv(uHead, false, hm);
        for (const part of parts) {
          gl.bindTexture(gl.TEXTURE_2D, tex(part.texId || src.texId || headModel.texId).tex);
          gl.bindVertexArray(part.mesh.vao);
          gl.drawArrays(gl.TRIANGLES, 0, part.mesh.count);
        }
        reimuHandled = true;
        break;
      }
    }

    // --- 霊夢 (フォールバック): 姿勢トレースが無ければ従来どおり ysm.js の再合成で描く ---
    let skinned = null;
    if (!reimuHandled && ysm.state === 'ready') {
      for (const [id, p] of f.pos) {
        const e = D.entities.get(id);
        if (!e || e.role !== 'reimu') continue;
        if (!poseYsm(D, T, p)) break;
        skinned = { p, e };
        break;
      }
    }
    if (skinned) {
      reimuHandled = true;
      // 実機頂点ではなく ysm.js の再構成 or palette (14-01)。**同じ顔で出さない** (S1b)。
      poseSource = ysmLastPoseSource;
      const p = skinned.p;
      gl.useProgram(progSkin);
      gl.uniformMatrix4fv(gl.getUniformLocation(progSkin, 'uVP'), false, VP);
      // **前回ここに『倒れは掛けない、軸がずれるから』と書いたのは誤りだった。**
      // 実機の setupRotations(死亡の ZP も宙返りの XP もこの中)は scale(-1,-1,1) と
      // translate(0,-1.501,0) の**前**に走る。つまり rotY の直後が正しい合成点で、
      // 実機とまったく同じ点(足元)を軸に回る。倒れも宙返りもここへ入れる。
      const fxS = entityFx(skinned.e, p, T.tick, T.partial, hurt);
      const somS = somersaultRad(skinned.e.id, f.phys && f.phys.somer, T.tick, T.partial);
      gl.uniform1f(gl.getUniformLocation(progSkin, 'uFlash'), fxS.flash);
      // vanilla LivingEntityRenderer と同じ最終変換。ジオメトリは素のモデル空間のまま。
      let mm = M.mul(M.trans(p.x, p.y, p.z), M.rotY((180 - p.yaw) * Math.PI / 180));
      if (fxS.tilt > 0) mm = M.mul(mm, M.rotZ(fxS.tilt));
      if (somS > 0) mm = M.mul(mm, M.rotX(somS));
      mm = M.mul(mm, M.scale(-1, -1, 1));
      mm = M.mul(mm, M.trans(0, -1.501, 0));
      gl.uniformMatrix4fv(gl.getUniformLocation(progSkin, 'uModel'), false, mm);
      gl.uniform1i(gl.getUniformLocation(progSkin, 'uTex'), 0);
      gl.uniform1i(gl.getUniformLocation(progSkin, 'uBones'), 1);
      gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, ysm.boneTex);
      gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, tex(ysm.texId).tex);
      gl.bindVertexArray(ysm.mesh.vao);
      gl.drawArrays(gl.TRIANGLES, 0, ysm.mesh.count);
      gl.useProgram(progTex);
    }

    // S1b: run 全体の内訳は **tick ごとに 1 回だけ**数える。1 tick を何フレーム描いても
    // 割合が動かないようにする (描画回数ではなく tick 数の割合が知りたい)。
    if (T.tick !== lastCountedTick) {
      lastCountedTick = T.tick;
      lastCountedSource = poseSource;
      if (poseSourceCount[poseSource] !== undefined) poseSourceCount[poseSource]++;
    } else if (poseSource !== lastCountedSource) {
      // **同じ tick の結論が後から変わる。** palette の解凍は必ず非同期で、その tick の
      // 1 回目の draw は必ず再構成に落ちている (poseYsmPalette の注記)。1 回目だけ数えると
      // palette で描いた tick が軒並み reconstructed に計上され、「実機 N%」が実態とずれる。
      // 数え直しではなく**置き換え**なので、1 tick は最後まで 1 票のまま。
      if (poseSourceCount[lastCountedSource] !== undefined) poseSourceCount[lastCountedSource]--;
      if (poseSourceCount[poseSource] !== undefined) poseSourceCount[poseSource]++;
      lastCountedSource = poseSource;
    }

    // **描けなかったものを覚えておく。** 黙って continue すると、居るのに見えない
    // (= 透明な) entity ができる。にーくら 2026-08-23「霊夢が透明だったりね」。
    const missed = [];
    for (const [id, p] of f.pos) {
      const e = D.entities.get(id);
      if (!e || e.role === 'projectile') continue;
      if (reimuHandled && e.role === 'reimu') continue;   // 上 (姿勢トレース or ボーン付き) で描いた
      // 水槽ライブの霊夢は live palette だけで描く。poseYsm() が未着/identity不一致で
      // false を返した後に汎用モデルへ落とすと、実機姿勢ではない静止メッシュが表示される。
      // さらにそのモデルの texture が未解決なら 1x1 白 tex になり、今回の「白い人形」を
      // 作っていた。描けないことを赤い当たり箱と理由で明示し、別の姿勢を混ぜない。
      if (traceIsLive && e.role === 'reimu') {
        missed.push({ e, p, why: 'live palette=' + livePaletteState() });
        continue;
      }
      const m = model(e.type);
      if (m.state !== 'ready' || !m.raw || !m.raw.length) {
        missed.push({ e, p, why: m.state || 'モデル未取得' });
        continue;
      }
      // そのとき送られた姿勢 molang に対応するフレームがあればそれを使う。
      // 無ければ歩行位相からの通常選択へ落ちる。
      let mesh = null, texId = m.texId;
      if (m.byMolang && f.anim && f.anim.molang) {
        const slot = m.byMolang.get(f.anim.molang);
        if (slot != null && m.poseFrames && m.poseFrames[slot]) {
          mesh = m.poseFrames[slot];
          texId = m.poseTexId || texId;
        }
      }
      if (!mesh) mesh = meshFor(m, id, p, T.tick);
      // 記録時は yaw=0 (=レンダラが 180° を掛けた状態)。ここで rotY(-yaw) を足して実際の向きにする。
      // 倒れ(rotZ)は yaw の**後ろ**に掛ける —— 実機 setupRotations が
      // mulPose(YP) → mulPose(ZP) の順で、局所 Z 軸まわりに倒すのと同じ。
      const fx = entityFx(e, p, T.tick, T.partial, hurt);
      // 宙返りは霊夢(= phys を持つ者)だけ。phys は霊夢 1 体ぶんの単一レーンなので、
      // 他のモブへ掛けないよう role で絞る。
      const somG = (e.role === 'reimu') ? somersaultRad(e.id, f.phys && f.phys.somer, T.tick, T.partial) : 0;
      let mm = M.mul(M.trans(p.x, p.y, p.z), M.rotY(-p.yaw * Math.PI / 180));
      if (fx.tilt > 0) mm = M.mul(mm, M.rotZ(MIRRORED * fx.tilt));
      if (somG > 0) mm = M.mul(mm, M.rotX(MIRRORED * somG));
      gl.uniform1f(uFlash, fx.flash);
      gl.bindTexture(gl.TEXTURE_2D, tex(texId).tex);
      gl.uniformMatrix4fv(uModel, false, mm);
      gl.uniformMatrix4fv(uHead, false, headMatrix(m, p));
      gl.bindVertexArray(mesh.vao);
      gl.drawArrays(gl.TRIANGLES, 0, mesh.count);
    }

    drawMissBoxes(missed, VP);
    // 理由を 1 行にする。霊夢だけは 3 段のどこで落ちたかまで出す —— 段によって
    // 手当てが違う (姿勢記録の外なら記録範囲、ysm 未読込なら読み込みの問題)。
    if (!missed.length) {
      missStatus = '';
    } else {
      const r = missed.find((x) => x.e.role === 'reimu');
      missStatus = '描けていない ' + missed.length + '体'
        + (r ? '（霊夢: ' + (traceIsLive
            ? r.why + ' / YSMクライアントの描画待ち'
            : '姿勢記録=' + (poseTrace.state === 'ready' ? (USE_RECORDING ? 'この tick は範囲外' : '不使用') : poseTrace.state)
              + ' / ysm=' + ysm.state + ' / モデル=' + r.why) + '）'
            : '（' + missed[0].e.type + ': ' + missed[0].why + '）');
    }
    drawBullets(D, T, VP, camB);
    gl.bindVertexArray(null);
  }

  /**
   * 描けなかった entity を当たり判定の箱 (ワイヤ) で出す。
   *
   * <b>これが無いと「透明」と「そこに居ない」が同じ絵になる。</b>
   * 霊夢は ①姿勢トレース → ②ysm.js の再合成 → ③汎用モデル の 3 段で描かれるが、
   * 3 段とも外れると 1 ポリゴンも描かれず、エラーも出なかった
   * (にーくら 2026-08-23「霊夢が透明だったりね」)。箱が出ていれば
   * 「居るのに描けていない」と一目で判り、hint に理由も出る。
   */
  function drawMissBoxes(list, VP) {
    if (!list.length) return;
    const v = [];
    const col = [0.95, 0.45, 0.45, 1];
    for (const it of list) {
      const w = (it.e.w || 0.6) / 2, h = it.e.h || 1.8;
      const x = it.p.x, y = it.p.y, z = it.p.z;
      const c = [[x-w,y,z-w],[x+w,y,z-w],[x+w,y,z+w],[x-w,y,z+w],
                 [x-w,y+h,z-w],[x+w,y+h,z-w],[x+w,y+h,z+w],[x-w,y+h,z+w]];
      const E = [[0,1],[1,2],[2,3],[3,0],[4,5],[5,6],[6,7],[7,4],[0,4],[1,5],[2,6],[3,7]];
      for (const [a, b] of E) {
        v.push(c[a][0], c[a][1], c[a][2], col[0], col[1], col[2], col[3]);
        v.push(c[b][0], c[b][1], c[b][2], col[0], col[1], col[2], col[3]);
      }
    }
    const data = new Float32Array(v);
    if (!missMesh) {
      // VAO/VBO は 1 度だけ作って使い回す (毎フレーム作ると GPU 資源が漏れる)。
      missMesh = gl.createVertexArray(); missBuf = gl.createBuffer();
      gl.bindVertexArray(missMesh);
      gl.bindBuffer(gl.ARRAY_BUFFER, missBuf);
      gl.enableVertexAttribArray(LOC.pos); gl.vertexAttribPointer(LOC.pos, 3, gl.FLOAT, false, 28, 0);
      gl.enableVertexAttribArray(LOC.col); gl.vertexAttribPointer(LOC.col, 4, gl.FLOAT, false, 28, 12);
    } else {
      gl.bindVertexArray(missMesh);
      gl.bindBuffer(gl.ARRAY_BUFFER, missBuf);
    }
    gl.bufferData(gl.ARRAY_BUFFER, data, gl.DYNAMIC_DRAW);
    gl.useProgram(progLine);
    gl.uniformMatrix4fv(gl.getUniformLocation(progLine, 'uVP'), false, VP);
    gl.drawArrays(gl.LINES, 0, data.length / 7);
    gl.useProgram(progTex);
  }

  /** camB = SimPick.camBasis(cam) の {x,y,z,eye} —— x=右, y=上 (すでに正規直交)。 */
  function drawBullets(D, T, VP, camB) {
    const f = D.frameAt(T.tick, T.partial);
    if (!f) return;
    gl.useProgram(progBB);
    gl.uniformMatrix4fv(gl.getUniformLocation(progBB, 'uVP'), false, VP);
    gl.uniform1i(gl.getUniformLocation(progBB, 'uTex'), 0);
    gl.uniform3f(gl.getUniformLocation(progBB, 'uRight'), camB.x[0], camB.x[1], camB.x[2]);
    gl.uniform3f(gl.getUniformLocation(progBB, 'uUp'), camB.y[0], camB.y[1], camB.y[2]);
    const uC = gl.getUniformLocation(progBB, 'uCenter');
    const uHalf = gl.getUniformLocation(progBB, 'uHalf');
    const uSpin = gl.getUniformLocation(progBB, 'uSpin');
    const uAlpha = gl.getUniformLocation(progBB, 'uAlpha');
    const uFrame = gl.getUniformLocation(progBB, 'uFrame');

    gl.enable(gl.BLEND);
    gl.blendFunc(gl.ONE, gl.ONE);
    gl.depthMask(false);
    gl.bindVertexArray(billboardMesh().vao);
    gl.activeTexture(gl.TEXTURE0);

    for (const [id, p] of f.pos) {
      const e = D.entities.get(id);
      if (!e || e.role !== 'projectile') continue;
      const spec = BULLETS[e.type];
      const vis = f.vis && f.vis.get(id);
      const cxx = p.x, cyy = p.y + e.h / 2, czz = p.z;
      if (!spec) {
        gl.bindTexture(gl.TEXTURE_2D, tex('touhou_little_maid:textures/entity/reimu/myouju/red.png').tex);
        gl.uniform3f(uC, cxx, cyy, czz);
        gl.uniform1f(uHalf, Math.max(0.14, e.w * 0.7));
        gl.uniform1f(uSpin, 0); gl.uniform1f(uAlpha, 0.5);
        gl.uniform4f(uFrame, 0, 0, 1, 1/7);
        gl.drawArrays(gl.TRIANGLES, 0, 6);
        continue;
      }
      const n = spec.textures.length;
      const ci = vis && vis.color != null ? ((vis.color % n) + n) % n : 0;
      const frames = spec.frames || 1;
      const age = vis && vis.age != null ? vis.age : T.tick;
      const fr = frames > 1 ? Math.floor(age / (spec.frameTicks || 1)) % frames : 0;
      gl.bindTexture(gl.TEXTURE_2D, tex(spec.textures[ci]).tex);
      gl.uniform3f(uC, cxx, cyy, czz);
      gl.uniform1f(uHalf, spec.halfSize * (vis && vis.scale != null ? Math.max(0.05, vis.scale) : 1));
      gl.uniform1f(uSpin, (vis && vis.spin != null ? vis.spin : 0) * Math.PI / 180);
      gl.uniform1f(uAlpha, vis && vis.alpha != null ? vis.alpha : 1);
      gl.uniform4f(uFrame, 0, fr / frames, 1, 1 / frames);
      gl.drawArrays(gl.TRIANGLES, 0, 6);
    }
    gl.depthMask(true);
    gl.disable(gl.BLEND);
  }

  return { init, available, setTrace, render, growDerived, derivedStats, forgetEntities,
           ysmStatus: () => status + (traceIsLive ? ' · ' + livePaletteStatusText() : ''),
           missStatus: () => missStatus, lastVP: () => lastVP,
           // --- アニメブラウザ (S6) ---
           /** 316 本のアニメ一覧。`[{ name, frames, length }]`。未読込なら空配列。 */
           animList: () => (poseLib.state === 'ready' && poseLib.byAnim
             ? [...poseLib.byAnim.values()].map((a) => ({
                 name: a.anim, frames: a.to - a.from + 1, length: a.length || 0 }))
             : []),
           /** `name` を null にすると通常表示へ戻る。 */
           setAnimPreview: (name, frame) => {
             animPreview = name ? { name, frame: frame | 0, status: '', frames: 0 } : null;
           },
           animPreview: () => (animPreview ? Object.assign({}, animPreview) : null),
           poseLibState: () => poseLib.state,
           /** 資産が後から届いたときに呼ばれる。静止画面を描き直すために使う。 */
           setAssetReadyHook: (fn) => { assetReady = fn; } };
})();
