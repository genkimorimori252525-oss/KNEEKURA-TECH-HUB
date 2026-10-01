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


# Blockbench 5.2.1 project.ts maps 1.9.0 to Minecraft 1.9 through 1.21.5.
# This M2 pilot accepts only Minecraft 1.20.1; never inherit the editor's latest.
JAVA_BLOCK_VERSION = '1.9.0'
# Fixed item transforms, serialized identically by Java and native codecs.
# Default-valued fields are omitted just as pinned DisplaySlot.export() does.
# These are explicit pilot settings, not a runtime/in-game visual verdict.
ITEM_DISPLAY = {
    'gui': {'rotation': [20, -30, 0], 'translation': [0, -4, 0], 'scale': [0.5, 0.5, 0.5]},
    'ground': {'translation': [0, 2, 0], 'scale': [0.4, 0.4, 0.4]},
    'fixed': {'rotation': [0, -180, 0], 'translation': [0, -4, 0], 'scale': [0.5, 0.5, 0.5]},
    'thirdperson_righthand': {'rotation': [0, 90, 0], 'translation': [0, 4, 1], 'scale': [0.7, 0.7, 0.7]},
    'thirdperson_lefthand': {'rotation': [0, 90, 0], 'translation': [0, 4, 1], 'scale': [0.7, 0.7, 0.7]},
    'firstperson_righthand': {'rotation': [0, -90, 25], 'translation': [1.13, 3.2, 1.13], 'scale': [0.68, 0.68, 0.68]},
    'firstperson_lefthand': {'rotation': [0, -90, 25], 'translation': [1.13, 3.2, 1.13], 'scale': [0.68, 0.68, 0.68]},
}


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
  const projectPolicy = {java_block_version:__JAVA_BLOCK_VERSION__,display:__ITEM_DISPLAY__};
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
  let next = 0, cubeCount = 0, regionCount = 0, busy = false, last = null;
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
  function sameJSON(a,b) {
    if (a === b) return true;
    if (!a || !b || typeof a !== 'object' || typeof b !== 'object' || Array.isArray(a) !== Array.isArray(b)) return false;
    const ak=Object.keys(a), bk=Object.keys(b);
    return ak.length===bk.length && ak.every(k=>own(b,k) && sameJSON(a[k],b[k]));
  }
  function stateCheck(empty=false, expectedCubes=cubeCount, expectedTexture=textureUUID, configured=true, expectedDisplay=projectPolicy.display) {
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
      if (configured && (s.java_block_version !== projectPolicy.java_block_version ||
          !sameJSON(s.display,expectedDisplay))) poison();
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
  const repairOps = ['part_edit','uv_edit','texture_edit','display_edit'];
  let sealedSnapshot=null, sealedHash=null, generation=0, ownedTexture=null;
  const ownedParts=[];
  const stable = v => v === null || typeof v !== 'object' ? JSON.stringify(v) :
    Array.isArray(v) ? '['+v.map(stable).join(',')+']' :
    '{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+stable(v[k])).join(',')+'}';
  const decodePixels = v => Uint8Array.from(atob(v), c=>c.charCodeAt(0));
  function encodePixels(v) { let raw=''; for (const n of v) raw+=String.fromCharCode(n); return btoa(raw); }
  function ownedCheck() {
    if (typeof host.elementIdentity !== 'function' || typeof host.textureIdentity !== 'function' ||
        !ownedTexture || host.textureIdentity(textureUUID) !== ownedTexture ||
        ownedParts.length !== cubeCount) poison();
    for (const p of ownedParts) {
      if (!p.object || host.elementIdentity(p.native_uuid) !== p.object ||
          p.object.uuid !== p.native_uuid || p.object.name !== p.part_id) poison();
    }
  }
  function snapshotValue(expectedDisplay=projectPolicy.display, version=generation) {
    stateCheck(false,cubeCount,textureUUID,true,expectedDisplay); ownedCheck();
    if (typeof host.snapshot !== 'function') poison();
    const value=host.snapshot();
    if (!value || typeof value !== 'object' || value.then || !value.native || !value.model ||
        typeof value.rgba !== 'string') poison();
    const snapshot=detached({schema_version:1,request_hash:config.request_hash,project_uuid:projectUUID,
      generation:version,parts:ownedParts.map(p=>({part_id:p.part_id,native_uuid:p.native_uuid})),
      texture:{texture_id:'atlas',native_uuid:textureUUID,width:config.texture_size[0],
        height:config.texture_size[1],rgba:value.rgba},native:value.native,model:value.model});
    if (decodePixels(snapshot.texture.rgba).length !== config.texture_size[0]*config.texture_size[1]*4 ||
        !Array.isArray(snapshot.native.elements) || !Array.isArray(snapshot.model.elements) ||
        snapshot.native.elements.length !== cubeCount || snapshot.model.elements.length !== cubeCount ||
        !sameJSON(snapshot.native.outliner,ownedParts.map(p=>p.native_uuid))) poison();
    for (let i=0;i<ownedParts.length;i++) {
      const p=ownedParts[i],n=snapshot.native.elements[i],m=snapshot.model.elements[i];
      if (!n || !m || n.uuid!==p.native_uuid || n.name!==p.part_id || m.name!==p.part_id || n.type!=='cube') poison();
    }
    if (!Array.isArray(snapshot.native.textures) || snapshot.native.textures.length!==1 ||
        snapshot.native.textures[0].uuid!==textureUUID) poison();
    if (stable(snapshot).length>524288) fail('SNAPSHOT_TOO_LARGE');
    return snapshot;
  }
  function assertSealed() {
    if (sealedSnapshot && !sameJSON(snapshotValue(),sealedSnapshot)) poison();
  }
  async function sealSnapshot(active=()=>{}) {
    active();
    assertSealed();
    const value=snapshotValue(),content=stable(value);
    if (typeof host.hash !== 'function') poison();
    const hash=await host.hash(content);
    active();
    if (typeof hash!=='string' || !/^[a-f0-9]{64}$/.test(hash) || !sameJSON(snapshotValue(),value)) poison();
    if (sealedHash && hash!==sealedHash) poison();
    active();
    sealedSnapshot=value;sealedHash=hash;
    return {kind:'snapshot',generation,snapshot_hash:hash,encoding:'utf8',content};
  }
  function repairArguments(operation,args) {
    keys(args,['schema_version','request_hash','project_uuid','expected_generation','expected_snapshot_hash',
      'operation','target','expected','value']);
    if (!sealedSnapshot || generation>=32 || args.schema_version!==1 || args.operation!==operation ||
        args.request_hash!==config.request_hash || args.project_uuid!==projectUUID ||
        !Number.isInteger(args.expected_generation) || args.expected_generation!==generation ||
        args.expected_snapshot_hash!==sealedHash) fail('STALE_MUTATION');
    assertSealed();
    const expected=detached(sealedSnapshot);expected.generation=generation+1;
    const target=args.target,value=args.value;let old,action,params,region=null;
    const partIndex=id=>{const found=ownedParts.map((p,i)=>p.part_id===id?i:-1).filter(i=>i>=0);
      if(found.length!==1)fail('PART_NOT_OWNED');return found[0];};
    const scalar=(v,lo,hi)=>numberVector([v],1,lo,hi)[0];
    if(operation==='part_edit') {
      keys(target,['part_id','property','axis']);
      if(!['from','to'].includes(target.property)||!Number.isInteger(target.axis)||target.axis<0||target.axis>2)fail('INVALID_PART_EDIT');
      const i=partIndex(target.part_id),p=target.property,a=target.axis;scalar(value,-16,32);
      old=expected.native.elements[i][p][a];
      expected.native.elements[i][p][a]=value;expected.model.elements[i][p][a]=value;
      if(expected.native.elements[i].from.some((v,j)=>v>=expected.native.elements[i].to[j]))fail('DEGENERATE_CUBE');
      action='edit_element';params={element:ownedParts[i].native_uuid,[p]:expected.native.elements[i][p].slice()};
    } else if(operation==='uv_edit') {
      keys(target,['part_id','face','texture_id']);
      if(target.texture_id!=='atlas'||!['north','south','east','west','up','down'].includes(target.face))fail('INVALID_FACE_EDIT');
      const i=partIndex(target.part_id),f=target.face,uv=numberVector(value,4,0,256);
      if(uv[0]>=uv[2]||uv[1]>=uv[3]||uv[2]>config.texture_size[0]||uv[3]>config.texture_size[1])fail('INVALID_UV');
      old=expected.native.elements[i].faces[f].uv.slice();
      expected.native.elements[i].faces[f].uv=uv;
      expected.model.elements[i].faces[f].uv=uv.map((n,j)=>n*16/config.texture_size[j%2]);
      action='set_cube_uv';params={cube:ownedParts[i].native_uuid,faces:{[f]:{uv}}};
    } else if(operation==='texture_edit') {
      keys(target,['texture_id','rect']);
      const rect=numberVector(target.rect,4,0,256);
      if(target.texture_id!=='atlas'||rect.some(n=>!Number.isInteger(n))||rect[0]>=rect[2]||rect[1]>=rect[3]||
        rect[2]>config.texture_size[0]||rect[3]>config.texture_size[1]||!config.palette.includes(value)||
        typeof args.expected!=='string'||!/^[a-f0-9]{64}$/.test(args.expected))fail('INVALID_TEXTURE_EDIT');
      const pixels=decodePixels(expected.texture.rgba),w=config.texture_size[0],oldBytes=[];
      const color=[parseInt(value.slice(1,3),16),parseInt(value.slice(3,5),16),parseInt(value.slice(5,7),16),255];
      let changed=false;
      for(let y=rect[1];y<rect[3];y++)for(let x=rect[0];x<rect[2];x++)for(let c=0;c<4;c++){
        const i=(y*w+x)*4+c;oldBytes.push(pixels[i]);changed=changed||pixels[i]!==color[c];pixels[i]=color[c];
      }
      if(!changed)fail('NO_OP_MUTATION');
      expected.texture.rgba=encodePixels(pixels);region=new Uint8Array(oldBytes);
      action='paint_texture';params={texture:textureUUID,ops:[{type:'rect',x:rect[0],y:rect[1],
        width:rect[2]-rect[0],height:rect[3]-rect[1],color:value,fill:true}]};
    } else {
      keys(target,['slot','property','axis']);
      if(!own(expected.native.display,target.slot)||!['rotation','translation','scale'].includes(target.property)||
        !Number.isInteger(target.axis)||target.axis<0||target.axis>2)fail('INVALID_DISPLAY_EDIT');
      const p=target.property,limit=p==='scale'?4:p==='rotation'?180:80;
      scalar(value,-limit,limit);if(p==='scale'&&value<=0)fail('INVALID_DISPLAY_EDIT');
      const defaults=p==='scale'?[1,1,1]:[0,0,0];
      const vector=(expected.native.display[target.slot][p]||defaults).slice();old=vector[target.axis];
      vector[target.axis]=p==='rotation'?(value+180*15)%360-180:value;
      for(const kind of ['native','model']){
        if(sameJSON(vector,defaults))delete expected[kind].display[target.slot][p];
        else expected[kind].display[target.slot][p]=vector.slice();
      }
      action='__display';params={slot:target.slot,property:p,value:vector};
    }
    if(region===null && (!sameJSON(args.expected,old)||sameJSON(value,old)))fail('EXPECTED_VALUE_MISMATCH');
    return [action,params,{expected,region,oldHash:args.expected}];
  }

  function argumentsFor(operation, args) {
    if (operation === 'begin') {
      keys(args, []);
      if (phase !== 'READY') fail('ALREADY_BEGUN');
      return ['new_project', {format:'java_block', name:config.asset_name,
        texture_width:config.texture_size[0], texture_height:config.texture_size[1]}];
    }
    if (phase !== 'OPEN') fail('SESSION_NOT_OPEN');
    if (operation === 'snapshot') { keys(args,[]); if (!textureUUID || cubeCount<1) fail('CAPTURE_NOT_READY'); return ['__snapshot',{}]; }
    if (repairOps.includes(operation)) return repairArguments(operation,args);
    if (sealedSnapshot && ['texture','texture_region','cube'].includes(operation)) fail('GENERATION_SEALED');
    if (operation === 'texture') {
      keys(args, ['fill']);
      if (textureUUID || cubeCount || !config.palette.includes(args.fill)) fail('INVALID_TEXTURE');
      return ['create_texture', {name:config.asset_name, width:config.texture_size[0],
        height:config.texture_size[1], fill:args.fill}];
    }
    if (operation === 'texture_region') {
      keys(args, ['rect','color']);
      if (!textureUUID || cubeCount || regionCount >= 32 || !config.palette.includes(args.color)) fail('INVALID_TEXTURE_REGION');
      const rect = numberVector(args.rect,4,0,256);
      if (rect.some(n=>!Number.isInteger(n)) || rect[0]>=rect[2] || rect[1]>=rect[3] ||
          rect[2]>config.texture_size[0] || rect[3]>config.texture_size[1]) fail('INVALID_TEXTURE_REGION');
      // Pinned paint_texture -> applyPaintOps receives only this filled rect.
      // The caller cannot choose a texture, brush type, URL, code or file path.
      return ['paint_texture',{texture:textureUUID,ops:[{type:'rect',x:rect[0],y:rect[1],
        width:rect[2]-rect[0],height:rect[3]-rect[1],color:args.color,fill:true}]}];
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
      if (args.kind === 'model' || args.kind === 'native' || args.kind === 'texture') {
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
    if (expected.kind === 'model' || expected.kind === 'native') {
      keys(value, ['kind','mime','encoding','content']);
      if (value.kind !== expected.kind || value.mime !== 'application/json' || value.encoding !== 'utf8' ||
          typeof value.content !== 'string' || value.content.length < 2 || value.content.length > 524288) bad();
      let parsed;
      try { parsed = JSON.parse(value.content); } catch(e) { bad(); }
      if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) bad();
    } else if (expected.kind === 'texture') {
      keys(value, ['kind','mime','encoding','content']);
      if (value.kind !== 'texture' || value.mime !== 'image/png' || value.encoding !== 'base64') bad();
      boundedBase64(value.content);
    } else if (expected.kind === 'view') {
      keys(value, ['kind','mime','encoding','view','looking_at','model_right_on','note','content',...(sealedSnapshot?['frame','generation']:[])]);
      if(sealedSnapshot&&(!value.frame||typeof value.frame!=='object'||value.generation!==generation))bad();
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
      if (phase === 'OPEN' && !busy) {
        try { stateCheck(); assertSealed(); } catch(e) { phase='UNKNOWN'; }
      }
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
    const [upstreamAction, args, repair] = argumentsFor(p.operation, p.arguments);
    try { stateCheck(p.operation === 'begin'); assertSealed(); }
    catch(e) { if (phase === 'OPEN') phase = 'UNKNOWN'; throw e; }
    const seq = next++;
    const operation = p.operation;
    busy = true; // Synchronous before awaiting: a second socket cannot enter.
    last = {seq,operation,completion:'UNKNOWN',verification:gates()};
    let timer;
    try {
      // One deadline owns every accepted async step, including hashing. A
      // timeout cannot cancel a provider; late continuations must not invoke
      // another mutator, commit a generation or turn UNKNOWN into CONFIRMED.
      let expired=false;
      const operationStarted=host.now();
      const deadline=new Promise((_,reject)=>{
        timer=setTimeout(()=>{expired=true;phase='UNKNOWN';reject(new Error('deadline'));},10000);
      });
      const active=()=>{
        const current=host.now();
        if(expired||phase==='UNKNOWN'||!Number.isFinite(current)||current<operationStarted||
          current-operationStarted>=10000)poison();
      };
      const bounded=value=>Promise.race([Promise.resolve(value),deadline]);
      active();
      if (repair && repair.region !== null) {
        const regionHash=await bounded(host.hash(repair.region));
        active();
        if (regionHash!==repair.oldHash) fail('EXPECTED_REGION_MISMATCH');
        assertSealed();
      }
      active();
      const result = await bounded(operation === 'snapshot' ? sealSnapshot(active) : operation === 'capture'
        ? host.capture(args.kind, sealedSnapshot ? {view:args.view,freeze:true,generation} : {view:args.view})
        : upstreamAction === '__display' ? host.editDisplay(args.slot,args.property,args.value)
        : host.invoke(upstreamAction,args));
      active();
      if (operation === 'begin') {
        const s=host.state();
        project=s.active; projectUUID=project && project.uuid;
        // The pinned new_project returns get_status().project WITHOUT uuid.
        // Bind the actual freshly created object, not an invented response field.
        if (typeof projectUUID !== 'string' || !projectUUID || !result || typeof result !== 'object') poison();
        stateCheck(false,0,null,false);
        host.configureProject(project,detached(projectPolicy));
        phase='OPEN';
      }
      const nextTexture = operation === 'texture' ? result && result.uuid : textureUUID;
      if (operation === 'texture' && (typeof nextTexture !== 'string' || !nextTexture)) poison();
      stateCheck(false, cubeCount+(operation==='cube'?1:0), nextTexture,true,repair?repair.expected.native.display:projectPolicy.display);
      if (repair) {
        const after=snapshotValue(repair.expected.native.display,generation+1);
        if(operation==='texture_edit')repair.expected.native.textures[0].source=after.native.textures[0].source;
        if(!sameJSON(after,repair.expected))poison();
        const hash=await bounded(host.hash(stable(after)));
        active();
        if(typeof hash!=='string'||!/^[a-f0-9]{64}$/.test(hash)||!sameJSON(snapshotValue(repair.expected.native.display,generation+1),after))poison();
        active();
        generation++;projectPolicy.display=detached(after.native.display);sealedSnapshot=after;sealedHash=hash;
      } else if (sealedSnapshot) assertSealed();
      if (operation === 'capture') captureResult(args, result);
      const raw = JSON.stringify(result);
      const responseLimit = operation === 'snapshot' ? 1572864 : operation === 'capture' ? 786432 : 262144;
      if (typeof raw !== 'string' || raw.length > responseLimit) poison();
      if (operation === 'texture') { textureUUID=nextTexture; if(typeof host.textureIdentity==='function')ownedTexture=host.textureIdentity(textureUUID); }
      if (operation === 'texture_region') regionCount++;
      if (operation === 'cube') { cubeCount++; names.add(args.name);
        if(typeof host.elementIdentity==='function'){const id=result&&result.uuid;
          const object=host.elementIdentity(id);if(!object||object.uuid!==id||object.name!==args.name||ownedParts.some(p=>p.native_uuid===id))poison();
          ownedParts.push({part_id:args.name,native_uuid:id,object});}
      }
      active();
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
})'''.replace('__JAVA_BLOCK_VERSION__', canonical(JAVA_BLOCK_VERSION).decode()).replace('__ITEM_DISPLAY__', canonical(ITEM_DISPLAY).decode())

# Access reviewed provider APIs and pinned per-project version/display APIs,
# plus read-only project/plugin inventory. Missing inventory APIs fail closed at runtime.
HOST_ADAPTER = r'''{
  elementIdentity: uuid => {
    if (typeof Cube === 'undefined') return null;
    const found=Cube.all.filter(c=>c.uuid===uuid);return found.length===1?found[0]:null;
  },
  textureIdentity: uuid => {
    if (typeof Texture === 'undefined') return null;
    const found=Texture.all.filter(t=>t.uuid===uuid);return found.length===1?found[0]:null;
  },
  hash: async value => {
    const bytes=typeof value==='string'?new TextEncoder().encode(value):value;
    const hash=await globalThis.crypto.subtle.digest('SHA-256',bytes);
    return Array.from(new Uint8Array(hash),n=>n.toString(16).padStart(2,'0')).join('');
  },
  snapshot: () => {
    if(typeof Texture==='undefined'||Texture.all.length!==1||!Texture.all[0].ctx||
      typeof Format==='undefined'||!Format.codec||typeof Codecs==='undefined'||!Codecs.project)
      throw new Error('Owned snapshot APIs unavailable');
    const native=Codecs.project.compile({compressed:false,absolute_paths:false,bitmaps:true,raw:true});
    const model=Format.codec.compile();
    if((native&&native.then)||(model&&model.then))throw new Error('Snapshot codecs must be synchronous');
    const t=Texture.all[0],pixels=t.ctx.getImageData(0,0,t.width,t.height).data;
    let raw='';for(const n of pixels)raw+=String.fromCharCode(n);
    return {native:typeof native==='string'?JSON.parse(native):native,
      model:typeof model==='string'?JSON.parse(model):model,rgba:btoa(raw)};
  },
  editDisplay: (slot,property,value) => {
    const owned=Project.display_settings[slot];
    if(!owned||typeof owned.extend!=='function')throw new Error('Owned display slot unavailable');
    Undo.initEdit({display_slots:[slot]});owned.extend({[property]:value.slice()});
    Undo.finishEdit('KNEEKURA: bounded display component');
    return {slot,transform:owned.export()};
  },
  frozenFrames: Object.create(null),
  fixedView: async function(view,generation) {
    const preview=Preview.selected;
    if(!preview||!preview.renderer||!preview.renderer.domElement)throw new Error('Preview unavailable');
    const saved=this.frozenFrames[view];
    if(saved){
      if(typeof preview.setProjectionMode==='function')preview.setProjectionMode(saved.projection==='orthographic');
      const c=preview.camera;
      for(const [key,value] of Object.entries(saved.camera_parameters))c[key]=value;
      c.position.fromArray(saved.position);c.quaternion.fromArray(saved.quaternion);c.up.fromArray(saved.up);
      preview.controls.target.fromArray(saved.target);c.updateProjectionMatrix();c.updateMatrixWorld(true);
    }else{
      if(typeof preview.setProjectionMode==='function')preview.setProjectionMode(false);
      applyAngleName(preview,view);
      if(preview.controls&&typeof preview.controls.update==='function')preview.controls.update();
    }
    // Preview.render() updates OrbitControls and can apply damping/rounding.
    // Once frozen, render the exact restored camera directly without another
    // controls update; the initial baseline is explicitly perspective.
    if(saved)preview.renderer.render(Canvas.scene,preview.camera);
    else preview.render();
    const c=preview.camera,canvas=preview.renderer.domElement;
    const parameters={near:c.near,far:c.far,zoom:c.zoom};
    for(const key of (preview.isOrtho?['left','right','top','bottom']:['fov','aspect']))parameters[key]=c[key];
    const frame={schema_version:1,view,projection:preview.isOrtho?'orthographic':'perspective',
      position:c.position.toArray(),quaternion:c.quaternion.toArray(),up:c.up.toArray(),
      target:preview.controls.target.toArray(),projection_matrix:c.projectionMatrix.toArray(),
      camera_parameters:parameters,viewport:[preview.width,preview.height],canvas:[canvas.width,canvas.height],
      output:[320,320],device_pixel_ratio:typeof devicePixelRatio==='number'?devicePixelRatio:1,
      render_mode:typeof Mode!=='undefined'&&Mode.selected?String(Mode.selected.id):'edit',
      capture_method:'fixed_preview_canvas_v1',render_settings:{
        shading:typeof settings!=='undefined'&&settings.shading?settings.shading.value:null,
        tone_mapping:preview.renderer.toneMapping??0,exposure:preview.renderer.toneMappingExposure??1,
        pixel_ratio:typeof preview.renderer.getPixelRatio==='function'?preview.renderer.getPixelRatio():1,
        background:typeof Canvas!=='undefined'&&Canvas.scene&&Canvas.scene.background&&
          typeof Canvas.scene.background.getHexString==='function'?Canvas.scene.background.getHexString():null}};
    if(!saved)this.frozenFrames[view]=JSON.parse(JSON.stringify(frame));
    const out=document.createElement('canvas');out.width=320;out.height=320;
    const ctx=out.getContext('2d');ctx.clearRect(0,0,320,320);
    const scale=Math.min(320/canvas.width,320/canvas.height),w=canvas.width*scale,h=canvas.height*scale;
    ctx.drawImage(canvas,(320-w)/2,(320-h)/2,w,h);
    const data=out.toDataURL('image/png');if(!data.startsWith('data:image/png;base64,'))throw new Error('Frozen capture is not PNG');
    const info=describeView(view);
    return {kind:'view',mime:'image/png',encoding:'base64',view,looking_at:String(info.looking_at||''),
      model_right_on:String(info.model_right_on||''),note:String(info.note||''),
      frame,generation,content:data.slice('data:image/png;base64,'.length)};
  },
  now: () => performance.now(),
  state: () => ({
    active: typeof Project === 'undefined' ? null : Project,
    projects: typeof ModelProject === 'undefined' ? null : ModelProject.all,
    format: typeof Format === 'undefined' || !Format ? null : Format.id,
    java_block_version: typeof Project === 'undefined' || !Project ? null : Project.java_block_version,
    display: typeof Project === 'undefined' || !Project || !Project.display_settings ? null :
      Object.fromEntries(Object.entries(Project.display_settings).map(([key,slot])=>
        [key,slot && typeof slot.export === 'function' ? slot.export() : null])),
    plugins: typeof Plugins === 'undefined' ? null : (Plugins.all || []).filter(p => p.installed && !p.disabled).map(p => p.id),
    cubes: typeof Cube === 'undefined' ? 0 : Cube.all.length,
    textures: typeof Texture === 'undefined' ? [] : Texture.all.map(t => ({
      uuid:t.uuid,width:t.width,height:t.height,
      ready:!!(t.img && t.img.complete && t.img.naturalWidth===t.width && t.img.naturalHeight===t.height)
    })),
    serverAlreadyRunning: kneekuraPreviousServer
  }),
  configureProject: (ownedProject, policy) => {
    if (typeof Project === 'undefined' || Project !== ownedProject ||
        typeof ModelProject === 'undefined' || ModelProject.all.length !== 1 || ModelProject.all[0] !== ownedProject ||
        typeof Format === 'undefined' || !Format || Format.id !== 'java_block' ||
        typeof DisplayMode === 'undefined' || typeof DisplayMode.loadJSON !== 'function')
      throw new Error('Expected owned Java project with display API');
    Project.java_block_version = policy.java_block_version;
    Project.display_settings = {};
    DisplayMode.loadJSON(policy.display);
  },
  invoke: (action, args) => {
    if (!Object.prototype.hasOwnProperty.call(commands, action)) throw new Error('Missing reviewed action');
    const texture = action === 'paint_texture' ? Texture.all.find(t=>t.uuid===args.texture) : null;
    if (action === 'paint_texture' && !texture) throw new Error('Bound texture is unavailable');
    const result = commands[action](args);
    if (action !== 'paint_texture') return result;
    // Pinned Painter updates img.src after editing the canvas. Its command
    // returns before that bitmap load completes; the guard deadline still applies.
    return Promise.resolve(result).then(async value => {
      if (!texture.img.complete || texture.img.naturalWidth !== texture.width || texture.img.naturalHeight !== texture.height)
        await texture.img.decode();
      return value;
    });
  },
  capture: async function(kind, args) {
    if (kind === 'model') {
      if (typeof Format === 'undefined' || !Format || !Format.codec || typeof Format.codec.compile !== 'function')
        throw new Error('Current format has no reviewed compile path');
      const data = await Promise.resolve(Format.codec.compile());
      const content = typeof data === 'string' ? data : JSON.stringify(data);
      return {kind:'model', mime:'application/json', encoding:'utf8', content};
    }
    if (kind === 'native') {
      if (typeof Codecs === 'undefined' || !Codecs || !Codecs.project || typeof Codecs.project.compile !== 'function')
        throw new Error('Blockbench project codec is unavailable');
      const data = await Promise.resolve(Codecs.project.compile({compressed:false, absolute_paths:false, bitmaps:true, raw:true}));
      const content = typeof data === 'string' ? data : JSON.stringify(data);
      return {kind:'native', mime:'application/json', encoding:'utf8', content};
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
      if(args.freeze===true)return this.fixedView(args.view,args.generation);
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
    allowed={'blockbench_mcp.js','client-private.json','manifest.json'}
    if (not isinstance(files,dict) or not {'blockbench_mcp.js','client-private.json'}<=set(files)
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
    files={'blockbench_mcp.js':plugin,'client-private.json':canonical(c),'manifest.json':canonical(manifest)}
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
