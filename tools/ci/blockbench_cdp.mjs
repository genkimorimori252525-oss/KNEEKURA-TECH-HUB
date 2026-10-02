import fs from 'node:fs';
import {pathToFileURL} from 'node:url';

export function parseArguments(argv) {
  function arg(name) {
    const i = argv.indexOf(name);
    if (i < 0 || i + 1 >= argv.length) throw new Error('Missing argument ' + name);
    return argv[i + 1];
  }
  const snapshotOnly = argv.includes('--snapshot-only');
  const port = Number(arg('--port'));
  if (!Number.isInteger(port) || port < 1 || port > 65535) throw new Error('Invalid debugging port');
  return {port, snapshotOnly, pluginPath: snapshotOnly ? null : arg('--plugin'), evidencePath: arg('--evidence')};
}

// Blockbench's pinned desktop entry point is index.html. A WebGL failure can
// open a second chrome://gpu page, which must never be mistaken for the editor.
export function selectEditorTarget(targets) {
  if (!Array.isArray(targets)) return undefined;
  const matches = targets.filter(target => {
    if (target.type !== 'page' || !target.webSocketDebuggerUrl) return false;
    try {
      const url = new URL(target.url);
      return url.protocol === 'file:' && url.pathname.endsWith('/index.html');
    } catch (_) { return false; }
  });
  return matches.length === 1 ? matches[0] : undefined;
}

export function rendererReady() {
  if (!(typeof Plugin === 'function' && typeof Plugins === 'object') ||
      typeof Blockbench === 'undefined' || Blockbench.setup_successful !== true ||
      typeof Preview === 'undefined' || !Preview.selected || !Preview.selected.renderer) return false;
  const context = Preview.selected.renderer.getContext();
  return !!context && typeof context.isContextLost === 'function' && !context.isContextLost();
}

// This fixed read-only function runs in the renderer. Do not include project
// names, paths, plugin configuration, private guard state, or document text.
export function snapshotState() {
  const bridge = globalThis.__BLOCKBENCH_MCP__;
  const identifier = value => typeof value === 'string' && /^[a-zA-Z0-9_.-]{1,80}$/.test(value) ? value : null;
  return {
    blockbench_version: typeof Blockbench === 'undefined' ? null : identifier(Blockbench.version),
    setup_successful: typeof Blockbench !== 'undefined' && Blockbench.setup_successful === true,
    bridge_port: bridge && Number.isInteger(bridge.port) ? bridge.port : null,
    server_running: !!(bridge && bridge.server),
    project_open: typeof Project !== 'undefined' && !!Project,
    project_count: typeof ModelProject === 'undefined' || !Array.isArray(ModelProject.all) ? null : ModelProject.all.length,
    format_id: typeof Format === 'undefined' || !Format ? null : identifier(Format.id),
    cube_count: typeof Cube === 'undefined' || !Array.isArray(Cube.all) ? null : Cube.all.length,
    texture_count: typeof Texture === 'undefined' || !Array.isArray(Texture.all) ? null : Texture.all.length,
    dialog_id: typeof open_dialog === 'undefined' ? null : identifier(open_dialog),
    installed_plugins: typeof Plugins === 'undefined' || !Array.isArray(Plugins.all) ? null :
      Plugins.all.filter(p => p.installed && !p.disabled).slice(0, 32).map(p => identifier(p.id))
  };
}

async function main() {
  const {port, snapshotOnly, pluginPath, evidencePath} = parseArguments(process.argv.slice(2));
  if (!snapshotOnly && !fs.statSync(pluginPath).isFile()) throw new Error('Plugin path is not a file');
  let target;
  for (let attempt = 0; attempt < 180; attempt++) {
    try {
      const response = await fetch(`http://127.0.0.1:${port}/json`, {signal: AbortSignal.timeout(2000)});
      if (!response.ok) throw new Error('Debugger target query failed');
      const all = await response.json();
      target = selectEditorTarget(all);
      if (target) break;
    } catch (_) {}
    await new Promise(r => setTimeout(r, 500));
  }
  if (!target) throw new Error('Blockbench renderer debugger did not become ready');
  const endpoint = new URL(target.webSocketDebuggerUrl);
  if (endpoint.protocol !== 'ws:' || endpoint.hostname !== '127.0.0.1' || Number(endpoint.port) !== port) {
    throw new Error('Unexpected debugger endpoint');
  }
  const socket = new WebSocket(endpoint);
  const pending = new Map();
  try {
    await new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error('Debugger websocket timeout')), 15000);
      socket.addEventListener('open', () => { clearTimeout(timer); resolve(); }, {once:true});
      socket.addEventListener('error', () => { clearTimeout(timer); reject(new Error('Debugger websocket failed')); }, {once:true});
    });
    let seq = 0;
    socket.addEventListener('message', event => {
      let message;
      try { message = JSON.parse(String(event.data)); } catch (_) { return; }
      if (!message.id || !pending.has(message.id)) return;
      const {resolve, reject, timer} = pending.get(message.id);
      pending.delete(message.id);
      clearTimeout(timer);
      if (message.error) reject(new Error('Debugger command failed'));
      else resolve(message.result);
    });
    function send(method, params={}) {
      return new Promise((resolve, reject) => {
        const id = ++seq;
        const timer = setTimeout(() => {
          pending.delete(id);
          reject(new Error('Debugger command timeout: ' + method));
        }, 30000);
        pending.set(id, {resolve, reject, timer});
        socket.send(JSON.stringify({id, method, params}));
      });
    }
    await send('Runtime.enable');
    async function waitForPluginApi() {
      for (let attempt = 0; attempt < 180; attempt++) {
        const state = await send('Runtime.evaluate', {
          expression: `(${rendererReady.toString()})()`,
          returnByValue: true
        });
        if (state.result && state.result.value === true) return;
        await new Promise(r => setTimeout(r, 250));
      }
      throw new Error('Plugin API did not become ready');
    }
    let expression;
    if (snapshotOnly) {
      expression = `(${snapshotState.toString()})()`;
    } else {
      await waitForPluginApi();
      const literal = JSON.stringify(pluginPath);
      expression = `(async () => {
        const filePath = ${literal};
        const local = new Plugin();
        await local.loadFromFile({path:filePath, name:'blockbench_mcp.js', content:''}, false);
        const loaded = Plugins.registered && Plugins.registered.blockbench_mcp;
        if (!loaded || loaded.installed !== true || loaded.path !== filePath) throw new Error('Guarded plugin identity/load mismatch');
        const action = typeof BarItems === 'object' && BarItems.blockbench_mcp_toggle;
        if (!action || typeof action.trigger !== 'function') throw new Error('Manual bridge action unavailable');
        action.trigger();
        await new Promise(r => setTimeout(r, 500));
        return {...(${snapshotState.toString()})(), plugin_id:String(loaded.id || '')};
      })()`;
    }
    const result = await send('Runtime.evaluate', {expression, awaitPromise:true, returnByValue:true, userGesture:false});
    if (result.exceptionDetails) throw new Error('Renderer evaluation failed');
    const value = result.result && result.result.value;
    if (!value || (!snapshotOnly && (value.plugin_id !== 'blockbench_mcp' || value.bridge_port !== 8787 || value.server_running !== true))) {
      throw new Error('Unexpected guarded plugin live state');
    }
    fs.writeFileSync(evidencePath, JSON.stringify(value, null, 2), {flag:'wx'});
    console.log(JSON.stringify(value));
  } finally {
    for (const {timer} of pending.values()) clearTimeout(timer);
    socket.close();
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch(error => { console.error(error.message); process.exitCode = 1; });
}
