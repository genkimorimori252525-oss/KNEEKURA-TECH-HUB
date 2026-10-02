/* =============================================================================
   SimLab — 3D カメラの単一定義と、そこからの床への逆写像 (§7-2 のクリック放ち用)
   -----------------------------------------------------------------------------
   実機 (`gl.js`) が GPU へ上げているのと**同じ 1 個の行列**をここで作る。
   viewProjection() は gl.js:1301-1304 の eye/view/VP 組み立てを verbatim に写した
   もので、gl.js 側はここを呼ぶだけになる (lastVP() で一致を実行時に確認できる)。

   projectPoint (順方向, 4x4 行列を通す) と unprojectToPlane (逆方向, カメラ基底 +
   fov を通す) は独立した実装。両者の往復一致がそのまま「ピックが見ている絵の
   とおりの場所に落ちる」ことの測定になる (pick-selftest.mjs)。

   classic script として書く (IIFE, 依存ゼロ, ビルド無し) —— gl.js と同じ流儀。
   node:vm がブラウザと同じこのファイルをそのまま読めるよう、`const` ではなく
   globalThis.SimPick へ代入する。
   ============================================================================= */
'use strict';

globalThis.SimPick = (function () {

  // gl.js:1304 の literal を移しただけ。gl.js 側はこの定数をもう持たない。
  const FOV_Y = 60 * Math.PI / 180;
  const NEAR = 0.05;
  const FAR = 900;

  // ===========================================================================
  // mat4 (列優先) / ベクトル ヘルパー。
  // gl.js の M / lookAt は private (そのファイルのモデル行列にも要る) なので
  // 共有せず、ここに小さく複製する。
  // ===========================================================================
  const M = {
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
  };
  const sub = (a, b) => [a[0]-b[0], a[1]-b[1], a[2]-b[2]];
  const add = (a, b) => [a[0]+b[0], a[1]+b[1], a[2]+b[2]];
  const scl = (a, k) => [a[0]*k, a[1]*k, a[2]*k];
  const cross = (a, b) => [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
  const dot = (a, b) => a[0]*b[0] + a[1]*b[1] + a[2]*b[2];
  const norm = (a) => { const l = Math.sqrt(dot(a, a)) || 1; return [a[0]/l, a[1]/l, a[2]/l]; };

  function lookAt(eye, at, up) {
    const z = norm(sub(eye, at)), x = norm(cross(up, z)), y = cross(z, x);
    return new Float32Array([
      x[0],y[0],z[0],0, x[1],y[1],z[1],0, x[2],y[2],z[2],0,
      -dot(x,eye), -dot(y,eye), -dot(z,eye), 1,
    ]);
  }

  /** SimGL.render の eye 式 (gl.js:1302) を verbatim に写したもの。カメラの原点。 */
  function camEye(cam) {
    const cp = Math.cos(cam.pitch), sp = Math.sin(cam.pitch);
    const cy = Math.cos(cam.yaw), sy = Math.sin(cam.yaw);
    return [cam.tx + cam.dist*cp*sy, cam.ty + cam.dist*sp, cam.tz + cam.dist*cp*cy];
  }

  /** lookAt (gl.js:1281) が組む正規直交基底。カメラは -z を向く。 */
  function camBasis(cam) {
    const eye = camEye(cam);
    const z = norm(sub(eye, [cam.tx, cam.ty, cam.tz]));
    const x = norm(cross([0, 1, 0], z));
    const y = cross(z, x);
    return { eye, x, y, z };
  }

  /** SimGL.render が uVP としてアップロードするのと同じ 1 個の view-projection 行列。 */
  function viewProjection(cam, W, H) {
    const eye = camEye(cam);
    const view = lookAt(eye, [cam.tx, cam.ty, cam.tz], [0, 1, 0]);
    return M.mul(M.persp(FOV_Y, W / Math.max(1, H), NEAR, FAR), view);
  }

  /**
   * 順方向 (4x4 を通す)。CSS px、画面下向き y。
   * 地平線上/カメラの背後 (w<=1e-6) は null。
   */
  function projectPoint(cam, x, y, z, W, H) {
    const VP = viewProjection(cam, W, H);
    const cx = VP[0]*x + VP[4]*y + VP[8]*z + VP[12];
    const cy = VP[1]*x + VP[5]*y + VP[9]*z + VP[13];
    const cw = VP[3]*x + VP[7]*y + VP[11]*z + VP[15];
    if (cw <= 1e-6) return null;
    const ndcX = cx / cw, ndcY = cy / cw;
    return { x: (ndcX+1)/2*W, y: (1-ndcY)/2*H, d: cw };
  }

  /**
   * 逆方向 (カメラ基底 + fov を通す。**行列の逆行列ではない**——意図的に別経路)。
   * 地平線に平行 (dir.y≈0) か、平面がカメラの背後 (t<=0) なら null。
   */
  function unprojectToPlane(cam, sx, sy, W, H, planeY) {
    const { eye, x, y, z } = camBasis(cam);
    const asp = W / Math.max(1, H), td = Math.tan(FOV_Y / 2);
    const ndcX = 2*sx/W - 1, ndcY = 1 - 2*sy/H;
    const dir = norm(sub(add(scl(x, ndcX*asp*td), scl(y, ndcY*td)), z));
    if (Math.abs(dir[1]) < 1e-9) return null;
    const t = (planeY - eye[1]) / dir[1];
    if (t <= 0) return null;
    return { x: eye[0] + dir[0]*t, y: eye[1] + dir[1]*t, z: eye[2] + dir[2]*t };
  }

  /**
   * 床の表面 Y。scenario.floor.y は床**ブロック**の Y (tank.json では 64) で、
   * SimArena.java:253 はアクターを floorY+1 に立たせる。frameCam (index.html)
   * も既に cam.ty=floorY+1 を使っている。3D グリッドは commit 1029da3a
   * (buildChamber, HANDOFF-2026-08-20-tank.md §4-6) で既にこの +1 を持つ ——
   * ここで再び +1 したら二重になって壊れる。「直っていない」と早合点して
   * 触らないこと (この quick の revision_note が踏んだ罠そのもの)。
   */
  function floorSurfaceY(meta) {
    return (meta && typeof meta.floorY === 'number' ? meta.floorY : 64) + 1;
  }

  return { camEye, camBasis, viewProjection, projectPoint, unprojectToPlane, floorSurfaceY };
})();
