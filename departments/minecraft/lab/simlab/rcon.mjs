// 走っている水槽へ命令を送る口 —— Source RCON クライアント。
//
// にーくらの設計思想（2026-08-20）— 水槽には2種類の関わり方がある:
//   カメラ = 見るだけ。中を変えない。   → SimTrace（mod 側・無改変）
//   手     = 放つ。ノブを回す。         → **これ**
// 混ぜないこと。このファイルは「手」の側で、呼ばれない限り水槽は1ビットも変わらない。
//
// **ここに霊夢の知識を置かない。** 送るのは呼び出し側が組み立てた文字列で、
// このモジュールは中身を解釈しない。`/summon` がどう働くかは Minecraft が知っていることで、
// サイトが知っていることではない。
//
// 依存を足さない理由: RCON は 14 バイトのヘッダと null 終端文字列だけの単純な protocol で、
// 実装は 100 行に満たない。npm 依存を1つ増やすほうが高くつく。
//
// protocol (Valve Source RCON):
//   [int32 LE size][int32 LE id][int32 LE type][body の UTF-8][0x00][0x00]
//   size は自分自身を含まない = 4(id) + 4(type) + body + 2
//   type 3 = 認証、2 = コマンド実行、0 = 応答。認証失敗は応答 id = -1。
import net from 'node:net';

const TYPE_AUTH = 3;
const TYPE_EXEC = 2;
const AUTH_FAIL_ID = -1;

/** 1 パケットを組み立てる。 */
function frame(id, type, body) {
  const b = Buffer.from(body, 'utf8');
  const buf = Buffer.alloc(14 + b.length);
  buf.writeInt32LE(10 + b.length, 0);
  buf.writeInt32LE(id, 4);
  buf.writeInt32LE(type, 8);
  b.copy(buf, 12);
  buf.writeInt16LE(0, 12 + b.length);
  return buf;
}

/**
 * 受信バッファから完全なパケットを取り出す。
 * TCP なので 1 回の data で 2 つ届くことも、半分しか届かないこともある。
 */
function drain(buf) {
  const out = [];
  let off = 0;
  while (buf.length - off >= 4) {
    const size = buf.readInt32LE(off);
    if (buf.length - off < 4 + size) break;          // まだ全部届いていない
    const id = buf.readInt32LE(off + 4);
    const type = buf.readInt32LE(off + 8);
    const body = buf.toString('utf8', off + 12, off + 4 + size - 2);
    out.push({ id, type, body });
    off += 4 + size;
  }
  return { packets: out, rest: buf.subarray(off) };
}

/**
 * 接続 → 認証 → コマンド → 切断。1 コマンドにつき 1 接続。
 *
 * 召喚もノブも人が押したときだけ起きる低頻度の操作なので、接続を保って
 * 生死を管理する複雑さを持つ価値がない。**繋がらなければ即座に判る**ほうが大事。
 *
 * @returns {Promise<string>} サーバの応答本文（`/summon` なら "Summoned ..." など）
 */
export function rcon(command, opts = {}) {
  const host = opts.host || '127.0.0.1';
  const port = opts.port || 25575;
  const password = opts.password || 'simlab';
  const timeoutMs = opts.timeoutMs || 5000;

  return new Promise((resolve, reject) => {
    const sock = new net.Socket();
    let buf = Buffer.alloc(0);
    let authed = false;
    let done = false;

    const finish = (err, value) => {
      if (done) return;
      done = true;
      try { sock.destroy(); } catch { /* 既に閉じているかもしれない */ }
      if (err) reject(err); else resolve(value);
    };

    sock.setTimeout(timeoutMs, () => finish(new Error('RCON が ' + timeoutMs + 'ms 応答しなかった')));
    sock.on('error', (e) => finish(new Error('RCON に繋がらない (' + host + ':' + port + '): ' + e.message)));
    // 応答を受け切る前に閉じられた場合。**黙って成功にしない。**
    sock.on('close', () => finish(new Error('RCON が応答前に切断された')));

    sock.connect(port, host, () => {
      sock.write(frame(1, TYPE_AUTH, password));
    });

    sock.on('data', (chunk) => {
      buf = Buffer.concat([buf, chunk]);
      const { packets, rest } = drain(buf);
      buf = rest;
      for (const p of packets) {
        if (!authed) {
          // 認証応答。Minecraft は空の RESPONSE_VALUE を先に返すことがあるので、
          // AUTH_RESPONSE (type 2) だけを見る。
          if (p.type !== 2) continue;
          if (p.id === AUTH_FAIL_ID) {
            return finish(new Error('RCON のパスワードが違う'));
          }
          authed = true;
          sock.write(frame(2, TYPE_EXEC, command));
          continue;
        }
        // コマンドの応答。
        return finish(null, p.body);
      }
    });
  });
}
