import fs from 'node:fs';

function arg(name) {
  const i = process.argv.indexOf(name);
  if (i < 0 || i + 1 >= process.argv.length) throw new Error('Missing argument ' + name);
  return process.argv[i + 1];
}

const port = Number(arg('--port'));
const pluginPath = arg('--plugin');
const evidencePath = arg('--evidence');
if (!Number.isInteger(port) || port < 1 || port > 65535) throw new Error('Invalid debugging port');
if (!fs.statSync(pluginPath).isFile()) throw new Error('Plugin path is not a file');

async function targets() {
  const response = await fetch(`http://127.0.0.1:${port}/json`);
  if (!response.ok) throw new Error('Debugger target query failed');
  return response.json();
}

let target;
for (let attempt = 0; attempt < 180; attempt++) {
  try {
    const all = await targets();
    target = all.find(x => x.type === 'page' && x.webSocketDebuggerUrl);
    if (target) break;
  } catch (_) {}
  await new Promise(r => setTimeout(r, 500));
}
if (!target) throw new Error('Blockbench renderer debugger did not become ready');

const socket = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve, reject) => {
  const timer = setTimeout(() => reject(new Error('Debugger websocket timeout')), 15000);
  socket.addEventListener('open', () => { clearTimeout(timer); resolve(); }, {once:true});
  socket.addEventListener('error', () => { clearTimeout(timer); reject(new Error('Debugger websocket failed')); }, {once:true});
});

let seq = 0;
const pending = new Map();
socket.addEventListener('message', event => {
  const message = JSON.parse(String(event.data));
  if (!message.id || !pending.has(message.id)) return;
  const {resolve, reject} = pending.get(message.id);
  pending.delete(message.id);
  if (message.error) reject(new Error(JSON.stringify(message.error)));
  else resolve(message.result);
});
function send(method, params={}) {
  return new Promise((resolve, reject) => {
    const id = ++seq;
    pending.set(id, {resolve, reject});
    socket.send(JSON.stringify({id, method, params}));
    setTimeout(() => {
      if (pending.delete(id)) reject(new Error('Debugger command timeout: ' + method));
    }, 30000);
  });
}

await send('Runtime.enable');
const literal = JSON.stringify(pluginPath);
const expression = `(async () => {
  if (typeof Plugin !== 'function' || typeof Plugins !== 'object') throw new Error('Plugin API unavailable');
  const filePath = ${literal};
  const local = new Plugin();
  await local.loadFromFile({path:filePath, name:'blockbench_mcp.js', content:''}, false);
  const loaded = Plugins.registered && Plugins.registered.blockbench_mcp;
  if (!loaded || loaded.installed !== true || loaded.path !== filePath) throw new Error('Guarded plugin identity/load mismatch');
  const action = typeof BarItems === 'object' && BarItems.blockbench_mcp_toggle;
  if (!action || typeof action.trigger !== 'function') throw new Error('Manual bridge action unavailable');
  action.trigger();
  await new Promise(r => setTimeout(r, 500));
  const bridge = globalThis.__BLOCKBENCH_MCP__;
  if (!bridge || !bridge.server || bridge.port !== 8787) throw new Error('Guarded bridge did not start');
  return {
    blockbench_version: String(Blockbench.version || ''),
    plugin_id: String(loaded.id || ''),
    plugin_path: String(loaded.path || ''),
    bridge_port: bridge.port,
    server_running: !!bridge.server,
    project_open: !!Project
  };
})()`;
const result = await send('Runtime.evaluate', {
  expression,
  awaitPromise: true,
  returnByValue: true,
  userGesture: false
});
if (result.exceptionDetails) throw new Error('Renderer evaluation failed: ' + JSON.stringify(result.exceptionDetails));
const value = result.result && result.result.value;
if (!value || value.plugin_id !== 'blockbench_mcp' || value.bridge_port !== 8787 || value.server_running !== true) {
  throw new Error('Unexpected guarded plugin live state');
}
fs.writeFileSync(evidencePath, JSON.stringify(value, null, 2));
socket.close();
console.log(JSON.stringify(value));
