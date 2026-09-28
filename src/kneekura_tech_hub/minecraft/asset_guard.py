"""Offline, opt-in preparation of a restricted sosadly editor plugin.

Never installs/loads a plugin, contacts the bridge, or writes model resources.
The generated plugin and client-private.json contain a secret: keep them local,
outside Git and CAS. This is an application guard, NOT an OS/plugin sandbox.
The original M1 bridge remains strictly read-only. Live acceptance is outstanding.
"""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import re
import secrets
import stat
import sys
import uuid

from .asset_contract import (
    PLUGIN_GIT_BLOB, _profile, _resource_id, decode_json, provider_pin, validate_spec,
)
from .storage import ContractError, IntegrityError, Store, canonical, digest, valid_hash


# Exact reviewed seam at upstream 028cdd765... lines 6721 onward. Preserve the
# upstream copyright/license in the locally supplied source; distribute only
# this modification recipe, not a second copy of the third-party implementation.
UPSTREAM_DISPATCH = """async function dispatch(action, params) {
\tconst handler = commands[action];
\tif (!handler) throw new Error('Unknown command: ' + action);
\tconst start = Date.now();
\ttry {
\t\tconst result = await handler(params || {});
\t\tlogActivity(action, true, Date.now() - start);
\t\treturn result;
\t} catch (err) {
\t\tlogActivity(action, false, Date.now() - start);
\t\tthrow err;
\t}
}"""
UPSTREAM_BODY_LIMIT = 'const MAX_BODY = 96 * 1024 * 1024; // 96 MB guard (textures/screenshots can be large)'

UPSTREAM_AUTOSTART = """	if (autostartSetting.value && isApp) {
		try {
			startServer(getPort());
		} catch (e) {
			console.error('[BlockbenchMCP] autostart failed:', e);
		}
	}"""

# Trusted implementation, never template code supplied by an asset spec. Kept
# here so Python wheels need no additional data-file or npm packaging surface.
GUARD_FACTORY = r'''(function createKneekuraAssetGuard(input, host) {
  'use strict';
  const config = JSON.parse(JSON.stringify(input));
  const own = (v, k) => Object.prototype.hasOwnProperty.call(v, k);
  function fail(code) { const e = new Error('KNEEKURA asset guard: ' + code); e.code = code; throw e; }
  function keys(v, expected) {
    if (!v || typeof v !== 'object' || Array.isArray(v) ||
        Object.keys(v).length !== expected.length || expected.some(k => !own(v, k))) fail('INVALID_FIELDS');
  }
  keys(config, ['schema_version','request_hash','token','asset_name','texture_size','palette','allow_write']);
  if (config.schema_version !== 1 || typeof config.allow_write !== 'boolean' ||
      !/^[a-f0-9]{64}$/.test(config.token) || !/^[a-f0-9]{64}$/.test(config.request_hash) ||
      !/^[a-z0-9_.-]{1,64}$/.test(config.asset_name) ||
      !Array.isArray(config.texture_size) || config.texture_size.length !== 2 ||
      config.texture_size.some(n => !Number.isInteger(n) || n < 16 || n > 256 || (n & (n-1))) ||
      !Array.isArray(config.palette) || !config.palette.length || config.palette.length > 32 ||
      config.palette.some(c => typeof c !== 'string' || !/^#[a-f0-9]{6}$/.test(c))) fail('INVALID_CONFIG');
  const started = host.now();
  let phase = 'READY', project = null, projectUUID = null, textureUUID = null;
  let next = 0, cubeCount = 0, busy = false, last = null;
  const names = new Set();
  const gates = () => ({structural:'NOT_RUN', visual:'NOT_RUN', runtime:'NOT_RUN'});
  const detached = v => JSON.parse(JSON.stringify(v));
  function auth(p) {
    if (!p || typeof p.token !== 'string' || p.token.length !== 64) fail('UNAUTHORIZED');
    // Length is public; do not echo credentials into provider error/stack text.
    let diff = 0;
    for (let i=0; i<64; i++) diff |= p.token.charCodeAt(i) ^ config.token.charCodeAt(i);
    if (diff || p.request_hash !== config.request_hash) fail('UNAUTHORIZED');
  }
  function poison() { phase = 'UNKNOWN'; fail('UNKNOWN'); }
  function stateCheck(empty=false, expectedCubes=cubeCount, expectedTexture=textureUUID) {
    const s = host.state();
    if (!s || !Array.isArray(s.projects) || !Array.isArray(s.plugins) || !Array.isArray(s.textures) ||
        !Number.isInteger(s.cubes) || s.plugins.length !== 1 || s.plugins[0] !== 'blockbench_mcp' ||
        s.serverAlreadyRunning) fail('EDITOR_NOT_ISOLATED');
    if (empty) {
      if (s.active || s.projects.length || s.format || s.cubes || s.textures.length) fail('EDITOR_NOT_EMPTY');
    } else {
      if (!project || s.active !== project || s.projects.length !== 1 || s.projects[0] !== project ||
          s.active.uuid !== projectUUID || s.format !== 'java_block' || s.cubes !== expectedCubes ||
          s.textures.length !== (expectedTexture ? 1 : 0)) poison();
      if (expectedTexture) {
        const t = s.textures[0];
        if (t.uuid !== expectedTexture || t.ready !== true || t.width !== config.texture_size[0] ||
            t.height !== config.texture_size[1]) poison();
      }
    }
    return s;
  }
  function numberVector(v, n, lo, hi) {
    if (!Array.isArray(v) || v.length !== n ||
        v.some(x => typeof x !== 'number' || !Number.isFinite(x) || x < lo || x > hi)) fail('INVALID_VECTOR');
    return v.slice();
  }
  function argumentsFor(operation, args) {
    if (operation === 'begin') {
      keys(args, []);
      if (phase !== 'READY') fail('ALREADY_BEGUN');
      return ['new_project', {format:'java_block', name:config.asset_name,
        texture_width:config.texture_size[0], texture_height:config.texture_size[1]}];
    }
    if (phase !== 'OPEN') fail('SESSION_NOT_OPEN');
    if (operation === 'texture') {
      keys(args, ['fill']);
      if (textureUUID || cubeCount || !config.palette.includes(args.fill)) fail('INVALID_TEXTURE');
      return ['create_texture', {name:config.asset_name, width:config.texture_size[0],
        height:config.texture_size[1], fill:args.fill}];
    }
    if (operation === 'cube') {
      keys(args, ['name','from','to','uv']);
      if (!textureUUID || cubeCount >= 128 || typeof args.name !== 'string' ||
          !/^[a-z][a-z0-9_]{0,63}$/.test(args.name) || names.has(args.name)) fail('INVALID_CUBE');
      const from = numberVector(args.from,3,-16,32), to = numberVector(args.to,3,-16,32);
      if (from.some((x,i) => x >= to[i])) fail('DEGENERATE_CUBE');
      const uv = numberVector(args.uv,4,0,256);
      if (uv[0] >= uv[2] || uv[1] >= uv[3] || uv[2] > config.texture_size[0] ||
          uv[3] > config.texture_size[1]) fail('INVALID_UV');
      const faces = {};
      for (const side of ['north','south','east','west','up','down']) faces[side] = {uv:uv.slice(), texture:textureUUID};
      return ['add_cube',{name:args.name,from,to,autouv:0,box_uv:false,faces}];
    }
    if (operation === 'capture') {
      keys(args, ['kind','view']);
      if (!textureUUID || cubeCount < 1) fail('CAPTURE_NOT_READY');
      if (args.kind === 'model' || args.kind === 'texture') {
        if (args.view !== null) fail('INVALID_CAPTURE');
      } else if (args.kind === 'view') {
        if (!['front','left','right','back','top','bottom','front_right'].includes(args.view)) fail('INVALID_CAPTURE');
      } else fail('INVALID_CAPTURE');
      return ['__capture', {kind:args.kind, view:args.view}];
    }
    if (operation === 'inspect') { keys(args, []); return ['check_model', {}]; }
    fail('OPERATION_NOT_ALLOWED');
  }
  function captureResult(expected, value) {
    const bad = () => fail('INVALID_CAPTURE_RESULT');
    if (!value || typeof value !== 'object' || Array.isArray(value)) bad();
    if (expected.kind === 'model') {
      keys(value, ['kind','mime','encoding','content']);
      if (value.kind !== 'model' || value.mime !== 'application/json' || value.encoding !== 'utf8' ||
          typeof value.content !== 'string' || value.content.length < 2 || value.content.length > 524288) bad();
      let parsed;
      try { parsed = JSON.parse(value.content); } catch(e) { bad(); }
      if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) bad();
    } else if (expected.kind === 'texture') {
      keys(value, ['kind','mime','encoding','content']);
      if (value.kind !== 'texture' || value.mime !== 'image/png' || value.encoding !== 'base64') bad();
      boundedBase64(value.content);
    } else if (expected.kind === 'view') {
      keys(value, ['kind','mime','encoding','view','looking_at','model_right_on','note','content']);
      if (value.kind !== 'view' || value.mime !== 'image/png' || value.encoding !== 'base64' ||
          value.view !== expected.view) bad();
      for (const k of ['looking_at','model_right_on','note'])
        if (typeof value[k] !== 'string' || value[k].length > 512) bad();
      boundedBase64(value.content);
    } else bad();
    return value;
    function boundedBase64(content) {
      if (typeof content !== 'string' || !content.length || content.length > 700000 ||
          content.length % 4 !== 0 || !/^[A-Za-z0-9+/]*={0,2}$/.test(content)) bad();
    }
  }
  async function dispatch(action, p) {
    // No fallback to commands[action]: *all* original routes are closed here,
    // including raw lifecycle, file, texture-import, plugin and script actions.
    if (action !== 'kneekura_asset' && action !== 'kneekura_asset_status') fail('ACTION_NOT_ALLOWED');
    auth(p);
    if (action === 'kneekura_asset_status') {
      keys(p, ['token','request_hash']);
      return detached({guard_protocol:1, state:phase, next_sequence:next, project_uuid:projectUUID,
        busy, request_hash:config.request_hash, loaded_revision:'UNATTESTED', last_receipt:last});
    }
    keys(p, ['token','request_hash','seq','project_uuid','operation','arguments']);
    if (!config.allow_write) fail('WRITES_DISABLED');
    if (busy) fail('BUSY');
    if (phase === 'UNKNOWN') fail('UNKNOWN');
    if (!Number.isInteger(p.seq) || p.seq !== next || next >= 512) fail('SEQUENCE_REJECTED');
    if (p.project_uuid !== projectUUID) fail('PROJECT_ID_MISMATCH');
    const now = host.now();
    if (!Number.isFinite(started) || !Number.isFinite(now) || now - started > 900000 || now < started) poison();
    const [upstreamAction, args] = argumentsFor(p.operation, p.arguments);
    try { stateCheck(p.operation === 'begin'); }
    catch(e) { if (phase === 'OPEN') phase = 'UNKNOWN'; throw e; }
    const seq = next++;
    const operation = p.operation;
    busy = true; // Synchronous before awaiting: a second socket cannot enter.
    last = {seq,operation,completion:'UNKNOWN',verification:gates()};
    let timer;
    try {
      // A deadline cannot cancel editor-side side effects. Expiration poisons
      // this whole session; it never unlocks another write or triggers retry.
      const result = await Promise.race([
        Promise.resolve(operation === 'capture'
          ? host.capture(args.kind, {view:args.view})
          : host.invoke(upstreamAction,args)),
        new Promise((_,reject) => { timer=setTimeout(() => reject(new Error('deadline')),10000); })
      ]);
      if (operation === 'begin') {
        const s=host.state();
        project=s.active; projectUUID=project && project.uuid;
        // The pinned new_project returns get_status().project WITHOUT uuid.
        // Bind the actual freshly created object, not an invented response field.
        if (typeof projectUUID !== 'string' || !projectUUID || !result || typeof result !== 'object') poison();
        phase='OPEN';
      }
      const nextTexture = operation === 'texture' ? result && result.uuid : textureUUID;
      if (operation === 'texture' && (typeof nextTexture !== 'string' || !nextTexture)) poison();
      stateCheck(false, cubeCount+(operation==='cube'?1:0), nextTexture);
      if (operation === 'capture') captureResult(args, result);
      const raw = JSON.stringify(result);
      const responseLimit = operation === 'capture' ? 786432 : 262144;
      if (typeof raw !== 'string' || raw.length > responseLimit) poison();
      if (operation === 'texture') textureUUID=nextTexture;
      if (operation === 'cube') { cubeCount++; names.add(args.name); }
      last = {seq,operation,completion:'CONFIRMED',project_uuid:projectUUID,request_hash:config.request_hash,
        assertion_domain:'asset_editor_operation',verification:gates(),result:JSON.parse(raw)};
      return detached(last);
    } catch(e) {
      phase='UNKNOWN';
      last={seq,operation,completion:'UNKNOWN',project_uuid:projectUUID,request_hash:config.request_hash,
        assertion_domain:'asset_editor_operation',verification:gates()};
      fail('UNKNOWN');
    } finally { clearTimeout(timer); busy=false; }
  }
  return Object.freeze({dispatch});
})'''

# Access only the APIs already used by the pinned provider, plus read-only
# project/plugin inventory. Missing inventory APIs fail closed at runtime.
HOST_ADAPTER = r'''{
  now: () => performance.now(),
  state: () => ({
    active: typeof Project === 'undefined' ? null : Project,
    projects: typeof ModelProject === 'undefined' ? null : ModelProject.all,
    format: typeof Format === 'undefined' || !Format ? null : Format.id,
    plugins: typeof Plugins === 'undefined' ? null : (Plugins.all || []).filter(p => p.installed && !p.disabled).map(p => p.id),
    cubes: typeof Cube === 'undefined' ? 0 : Cube.all.length,
    textures: typeof Texture === 'undefined' ? [] : Texture.all.map(t => ({
      uuid:t.uuid,width:t.width,height:t.height,
      ready:!!(t.img && t.img.complete && t.img.naturalWidth===t.width && t.img.naturalHeight===t.height)
    })),
    serverAlreadyRunning: kneekuraPreviousServer
  }),
  invoke: (action, args) => {
    if (!Object.prototype.hasOwnProperty.call(commands, action)) throw new Error('Missing reviewed action');
    return commands[action](args);
  },
  capture: async (kind, args) => {
    if (kind === 'model') {
      if (typeof Format === 'undefined' || !Format || !Format.codec || typeof Format.codec.compile !== 'function')
        throw new Error('Current format has no reviewed compile path');
      const data = await Promise.resolve(Format.codec.compile());
      const content = typeof data === 'string' ? data : JSON.stringify(data);
      return {kind:'model', mime:'application/json', encoding:'utf8', content};
    }
    if (kind === 'texture') {
      if (typeof Texture === 'undefined' || Texture.all.length !== 1 || typeof Texture.all[0].getDataURL !== 'function')
        throw new Error('Expected exactly one capturable texture');
      const data = Texture.all[0].getDataURL();
      if (typeof data !== 'string' || !data.startsWith('data:image/png;base64,'))
        throw new Error('Texture capture is not PNG');
      return {kind:'texture', mime:'image/png', encoding:'base64',
        content:data.slice('data:image/png;base64,'.length)};
    }
    if (kind === 'view') {
      const shot = await commands.screenshot({view:args.view,width:320,height:320,annotate:true,stamp:'KNEEKURA evidence'});
      if (!shot || typeof shot.base64 !== 'string') throw new Error('Screenshot capture failed');
      return {kind:'view', mime:'image/png', encoding:'base64', view:shot.view,
        looking_at:String(shot.looking_at || ''), model_right_on:String(shot.model_right_on || ''),
        note:String(shot.note || ''), content:shot.base64};
    }
    throw new Error('Unsupported reviewed capture kind');
  }
}'''


def load_request(store: Store, request_hash: str) -> tuple[dict, dict]:
    """Revalidate the entire M1 chain without writing or repairing CAS records."""
    r = decode_json(store.read(valid_hash(request_hash)))
    required = {'schema_version','record_type','asset_id','asset_kind','profile_id','profile_record_hash',
                'spec_hash','style_hash','reference_hashes','provider','target','exports','required_views'}
    if not isinstance(r, dict) or set(r) not in (required, required | {'index_snapshot_id'}):
        raise ContractError('Expected an exact M1 asset request')
    s = validate_spec(decode_json(store.read(r['spec_hash'])))
    p = _profile(decode_json(store.read(r['profile_record_hash']), max_bytes=16*1024*1024))
    style = decode_json(store.read(r['style_hash']))
    ns, path = _resource_id(s['asset_id'])
    expected = dict(schema_version=1, record_type='asset_request', asset_id=s['asset_id'],
                    asset_kind=s['asset_kind'],profile_id=p['profile_id'],profile_record_hash=r['profile_record_hash'],
                    spec_hash=r['spec_hash'],style_hash=r['style_hash'], reference_hashes=s['reference_hashes'],
                    provider=provider_pin(),target={k:p['manifest'][k] for k in
                        ('minecraft','loader','loader_version','java_major','track')},
                    exports={'native':f'source/{ns}/{path}.bbmodel',
                             'model':f'assets/{ns}/models/item/{path}.json',
                             'texture':f'assets/{ns}/textures/item/{path}.png'},
                    required_views=s['required_views'])
    if 'index_snapshot_id' in r:
        index = decode_json(store.read(r['index_snapshot_id']),max_bytes=16*1024*1024)
        if (not isinstance(index,dict) or type(index.get('schema_version')) is not int
                or index['schema_version'] != 1 or 'bytecode' not in index or index.get('profile') != p):
            raise IntegrityError('Index is not the M1 profile snapshot')
        expected['index_snapshot_id'] = r['index_snapshot_id']
    if canonical(r) != canonical(expected) or style != s['style']:
        raise IntegrityError('M1 asset request chain is inconsistent')
    for h in s['reference_hashes']:
        store.read(h)
    return r, s


def validate_config(value: dict) -> dict:
    try:
        c = decode_json(canonical(value))
    except (TypeError, ValueError, RecursionError, UnicodeError) as exc:
        raise ContractError('Guard configuration must be finite JSON') from exc
    fields = {'schema_version','request_hash','token','asset_name','texture_size','palette','allow_write'}
    if not isinstance(c,dict) or set(c)!=fields or type(c['schema_version']) is not int or c['schema_version']!=1:
        raise ContractError('Invalid guard configuration')
    valid_hash(c['request_hash']); valid_hash(c['token'])
    if (type(c['allow_write']) is not bool or not isinstance(c['asset_name'],str)
            or not re.fullmatch(r'[a-z0-9_.-]{1,64}',c['asset_name'])):
        raise ContractError('Invalid guard name or write permission')
    size=c['texture_size']; colors=c['palette']
    if (not isinstance(size,list) or len(size)!=2 or
            any(type(n) is not int or not 16<=n<=256 or n&(n-1) for n in size)):
        raise ContractError('Invalid guard texture size')
    if (not isinstance(colors,list) or not 1<=len(colors)<=32 or
            any(not isinstance(v,str) or not re.fullmatch(r'#[a-f0-9]{6}',v) for v in colors)):
        raise ContractError('Invalid guard palette')
    return c


def guard_config(store: Store, request_hash: str, *, allow_write: bool = False) -> dict:
    if type(allow_write) is not bool:
        raise ContractError('Explicit boolean write permission required')
    r,s=load_request(store,request_hash)
    # Names are presentation data, not native paths. Keep within the guard cap.
    name=r['asset_id'].split(':')[1].split('/')[-1]
    if len(name)>64:
        raise ContractError('M2 pilot supports asset basenames of at most 64 characters')
    return validate_config(dict(schema_version=1, request_hash=request_hash, token=secrets.token_hex(32),
        asset_name=name,texture_size=s['style']['texture_size'],
        palette=sorted({c.lower() for c in s['style']['palette'].values()}), allow_write=allow_write))


def verify_upstream(raw: bytes) -> str:
    if not isinstance(raw,bytes) or not 1<=len(raw)<=1048576:
        raise ContractError('Expected at most one MiB of pinned plugin source bytes')
    blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    if blob!=PLUGIN_GIT_BLOB:
        raise IntegrityError('Upstream plugin bytes do not match the selected Git blob')
    try:
        return raw.decode('utf-8')
    except UnicodeError as exc:
        raise ContractError('Plugin source is not UTF-8') from exc


def assemble_reviewed_source(source: str, config: dict) -> str:
    """Pure patch recipe. Call prepare_guarded_package to enforce the source pin.

    Kept separate so a small source-seam fixture can test patch mechanics without
    falsely pretending that the complete third-party plugin ran in Blockbench.
    """
    anchor='(function () {'
    if (not isinstance(source,str) or 'kneekuraGuard' in source or
            any(source.count(s)!=1 for s in (anchor,UPSTREAM_DISPATCH,UPSTREAM_BODY_LIMIT,UPSTREAM_AUTOSTART))):
        raise ContractError('Reviewed upstream patch seam changed or is ambiguous')
    c=validate_config(config)
    prefix = '\nconst kneekuraPreviousServer = !!(globalThis.__BLOCKBENCH_MCP__ && globalThis.__BLOCKBENCH_MCP__.server);\n'
    prefix += 'const kneekuraGuard = '+GUARD_FACTORY+'('+canonical(c).decode()+', '+HOST_ADAPTER+');\n'
    source=source.replace(anchor,anchor+prefix,1)
    source=source.replace(UPSTREAM_DISPATCH,
        'async function dispatch(action, params) {\n\treturn kneekuraGuard.dispatch(action, params);\n}',1)
    source=source.replace(UPSTREAM_AUTOSTART, '\t// KNEEKURA: explicit manual server start only; ignore stored autostart.',1)
    return source.replace(UPSTREAM_BODY_LIMIT,'const MAX_BODY = 1024 * 1024; // KNEEKURA bounded request',1)


def _safe_directory_chain(path: Path) -> None:
    for part in [path,*path.parents]:
        st=part.lstat()
        if not stat.S_ISDIR(st.st_mode) or stat.S_ISLNK(st.st_mode) or getattr(st,'st_file_attributes',0)&0x400:
            raise ContractError('Package parent must be real directories, not links/reparse points')


def write_private_bundle(destination: Path, files: dict[str,bytes]) -> None:
    """Create a NEW private local package. No replacement, merge, or cleanup of old files.

    On POSIX use a held directory descriptor and exclusive no-follow creation.
    Windows uses exclusive files in a fresh private user-controlled directory;
    ACL setup and real Windows acceptance are separate operational prerequisites.
    This does not protect against a malicious same-user process controlling parents.
    """
    allowed={'guarded-plugin.js','client-private.json','manifest.json'}
    if (not isinstance(files,dict) or not {'guarded-plugin.js','client-private.json'}<=set(files)
            or not set(files)<=allowed or any(not isinstance(v,bytes) or len(v)>2*1024*1024 for v in files.values())):
        raise ContractError('Invalid private package file inventory')
    dest=Path(destination).absolute()
    if dest.name in ('','.','..'):
        raise ContractError('A new package directory is required')
    _safe_directory_chain(dest.parent)
    if dest.exists() or dest.is_symlink():
        raise ContractError('Package destination already exists; overwrite prohibited')
    dest.mkdir(mode=0o700,exist_ok=False)
    fd=None
    try:
        if os.name=='posix':
            fd=os.open(dest,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        for name,data in files.items():
            flags=os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,'O_NOFOLLOW',0)
            file_fd=os.open(name,flags,0o600,dir_fd=fd) if fd is not None else os.open(dest/name,flags,0o600)
            with os.fdopen(file_fd,'wb') as stream:
                stream.write(data); stream.flush(); os.fsync(stream.fileno())
        if fd is not None: os.fsync(fd)
    finally:
        if fd is not None: os.close(fd)
    # A mid-write failure leaves a partial, non-reusable package for inspection;
    # it is never silently reused, retried or recursively removed.


def validate_package_parent(store: Store, parent: Path) -> Path:
    """Do not generate credential-bearing source inside a checkout or evidence CAS."""
    target = Path(parent).absolute()
    _safe_directory_chain(target)
    if target.resolve().is_relative_to(store.root):
        raise ContractError('Private plugin packages must stay outside the evidence CAS')
    for ancestor in [target, *target.parents]:
        marker = ancestor / '.git'
        if marker.exists() or marker.is_symlink():
            raise ContractError('Private plugin packages must stay outside Git checkouts/worktrees')
    return target


def prepare_guarded_package(store: Store, request_hash: str, *, upstream: bytes,
                            parent: Path, allow_write: bool = False) -> dict:
    """Prepare local guarded source only. Secret-bearing bytes never enter CAS."""
    source=verify_upstream(upstream)
    parent=validate_package_parent(store,parent)
    c=guard_config(store,request_hash,allow_write=allow_write)
    plugin=assemble_reviewed_source(source,c).encode('utf-8')
    manifest=dict(schema_version=1,record_type='asset_guard_package',request_hash=request_hash,
                  provider=provider_pin(),upstream_sha256=digest(upstream),guard_sha256=digest(GUARD_FACTORY.encode()),
                  plugin_sha256=digest(plugin),guard_protocol=1,
                  verification=dict(structural='NOT_RUN',visual='NOT_RUN',runtime='NOT_RUN'),
                  live_acceptance='NOT_RUN',source_binding='LOCAL_BUILD_NOT_LOADED_ATTESTATION')
    destination=Path(parent)/('blockbench-asset-'+str(uuid.uuid4()))
    files={'guarded-plugin.js':plugin,'client-private.json':canonical(c),'manifest.json':canonical(manifest)}
    write_private_bundle(destination,files)
    h=store.put_json(manifest)
    store.pin(h,'asset-guard:'+request_hash); store.pin(request_hash,'asset-guard:'+h)
    return dict(schema_version=1,status='OK',outcome='NOT_RUN',assertion_domain='asset_guard_package_preparation',
                package_directory=str(destination.absolute()),manifest_hash=h,
                verification=manifest['verification'],requires_live_acceptance=True)


def main(argv: list[str] | None=None) -> int:
    parser=argparse.ArgumentParser(description='Prepare a NEW local guarded plugin package; never install or launch it.')
    parser.add_argument('--store',required=True); parser.add_argument('--request',required=True)
    parser.add_argument('--upstream',required=True); parser.add_argument('--parent',required=True)
    parser.add_argument('--enable-writes',action='store_true',help='Explicit local opt-in; no live verification is implied')
    args=parser.parse_args(argv)
    try:
        path=Path(args.upstream)
        if path.is_symlink() or not path.is_file(): raise ContractError('Source must be a regular local file')
        with path.open('rb') as stream: raw=stream.read(1048577)
        result=prepare_guarded_package(Store(args.store),args.request,upstream=raw,parent=Path(args.parent),allow_write=args.enable_writes)
        print(canonical(result).decode()); return 0
    except (ContractError,OSError) as exc:
        print(canonical(dict(schema_version=1,status='ERROR',outcome='NOT_RUN',error=str(exc))).decode()); return 2


if __name__=='__main__':
    sys.exit(main())
