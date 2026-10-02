"""Pure Before/After camera-condition comparison, without an aesthetic verdict."""
from __future__ import annotations

import math
from .asset_contract import decode_json
from .asset_guard import load_request
from .asset_mutation import BoundedStoreView, bounded_read, decode_png_rgba, json_equal, load_snapshot, require
from .storage import ContractError, Store, canonical, valid_hash

_FRAME_FIELDS={'schema_version','view','projection','position','quaternion','up','target','projection_matrix',
               'camera_parameters','viewport','canvas','output','device_pixel_ratio','render_mode',
               'capture_method','render_settings'}


def validate_frame(value: dict, view: str) -> dict:
    try:
        raw=canonical(value)
        f=decode_json(raw,max_bytes=8192)
    except (ValueError,TypeError,RecursionError) as exc:
        raise ContractError('Invalid finite frame metadata') from exc
    require(isinstance(f,dict) and set(f)==_FRAME_FIELDS and type(f['schema_version']) is int and
            f['schema_version']==1 and f['view']==view and f['projection'] in ('perspective','orthographic') and
            f['capture_method']=='fixed_preview_canvas_v1', 'Invalid exact frozen frame metadata')
    def number(n):return type(n) in (int,float) and math.isfinite(n) and abs(n)<=1e9
    for key,size in [('position',3),('quaternion',4),('up',3),('target',3),('projection_matrix',16)]:
        require(isinstance(f[key],list) and len(f[key])==size and all(number(n) for n in f[key]), 'Invalid frame vector')
    for key in ('viewport','canvas','output'):
        require(isinstance(f[key],list) and len(f[key])==2 and all(type(n) is int and 1<=n<=16384 for n in f[key]),
                'Invalid frame pixel dimensions')
    require(all(n<=512 for n in f['output']), 'Frame output exceeds capture limit')
    require(number(f['device_pixel_ratio']) and 0<f['device_pixel_ratio']<=16 and
            isinstance(f['render_mode'],str) and 1<=len(f['render_mode'])<=64 and isinstance(f['render_settings'],dict)
            and len(canonical(f['render_settings']))<=2048, 'Invalid frame rendering settings')
    p=f['camera_parameters'];expected={'near','far','zoom'}|({'fov','aspect'} if f['projection']=='perspective' else {'left','right','top','bottom'})
    require(isinstance(p,dict) and set(p)==expected and all(number(n) for n in p.values()) and
            p['near']<p['far'] and p['zoom']>0, 'Invalid frame projection parameters')
    if f['projection']=='perspective':
        require(p['near']>0 and 0<p['fov']<180 and p['aspect']>0, 'Invalid perspective projection')
    else:
        require(p['left']<p['right'] and p['bottom']<p['top'], 'Invalid orthographic projection')
    return f


def _receipt(store,key):
    r=decode_json(bounded_read(store,key,1024*1024),max_bytes=1024*1024)
    require(isinstance(r,dict) and r.get('record_type')=='asset_session_capture' and
            type(r.get('schema_version')) is int and r['schema_version'] in (1,2), 'Expected captured asset receipt')
    return r


def compare_captures(store: Store, before_receipt_hash: str, after_receipt_hash: str) -> dict:
    store = BoundedStoreView(store)
    before=_receipt(store,before_receipt_hash);after=_receipt(store,after_receipt_hash)
    require(before.get('request_hash')==after.get('request_hash') and
            before.get('project_uuid')==after.get('project_uuid'), 'Before/After request or project mismatch')
    request,_=load_request(store,before['request_hash'])
    reasons=[]
    if before['schema_version']!=2 or after['schema_version']!=2:
        reasons.append('MISSING_GENERATION_METADATA')
    else:
        load_snapshot(store,before_receipt_hash);load_snapshot(store,after_receipt_hash)
        if after.get('generation')!=before.get('generation',-2)+1:
            reasons.append('NONCONSECUTIVE_GENERATION')
        if after.get('parent_receipt_hash')!=before_receipt_hash:
            reasons.append('LINEAGE_MISMATCH')
        else:
            m=decode_json(bounded_read(store,after.get('mutation_hash'),65536))
            require(isinstance(m,dict) and m.get('record_type')=='asset_mutation' and
                    m.get('base_receipt_hash')==before_receipt_hash and m.get('request_hash')==before['request_hash'] and
                    m.get('project_uuid')==before['project_uuid'] and type(m.get('expected_generation')) is int and
                    type(m.get('resulting_generation')) is int and m['expected_generation']==before['generation'] and
                    m['resulting_generation']==after['generation'] and m.get('expected_snapshot_hash')==before['snapshot_hash'],
                    'Mutation lineage identity mismatch')
    def views(r):
        items=r.get('artifacts');require(isinstance(items,list) and len(items)<=10,'Invalid captured artifact inventory')
        out={}
        for item in items:
            if isinstance(item,dict) and item.get('kind')=='view':
                name=item.get('view');require(isinstance(name,str) and name not in out,'Duplicate/invalid view')
                out[name]=item
        return out
    bv,av=views(before),views(after);entries=[]
    for view in request['required_views']:
        left,right=bv.get(view),av.get(view);local=list(reasons)
        if left is None or right is None:
            local.append('MISSING_CAPTURE')
        else:
            for item,r in [(left,before),(right,after)]:
                raw=bounded_read(store,item.get('content_hash'),512*1024)
                require(type(item.get('size_bytes')) is int and len(raw)==item['size_bytes'] and
                        len(raw)<=512*1024 and item.get('mime')=='image/png','Invalid view capture bytes')
                if not isinstance(item.get('frame'),dict):
                    local.append('MISSING_FRAME_METADATA');continue
                f=validate_frame(item['frame'],view)
                if type(item.get('generation')) is not int or item['generation']!=r.get('generation'):
                    local.append('VIEW_GENERATION_MISMATCH')
                try:
                    decode_png_rgba(raw,f['output'])
                except ContractError:
                    local.append('OUTPUT_DIMENSIONS_OR_PNG_MISMATCH')
            if not json_equal(left.get('frame'),right.get('frame')):
                local.append('FRAME_MISMATCH')
        local=list(dict.fromkeys(local))
        entries.append({'view':view,'comparability':'NON_COMPARABLE' if local else 'COMPARABLE','reasons':local,
            'before_hash':left.get('content_hash') if left else None,'after_hash':right.get('content_hash') if right else None,
            'before_generation':before.get('generation'),'after_generation':after.get('generation')})
    combined=list(dict.fromkeys(reasons+[reason for e in entries for reason in e['reasons']]))
    return {'schema_version':1,'assertion_domain':'asset_view_comparison','request_hash':before['request_hash'],
        'project_uuid':before['project_uuid'],'before_receipt_hash':before_receipt_hash,'after_receipt_hash':after_receipt_hash,
        'comparability':'NON_COMPARABLE' if combined else 'COMPARABLE','reasons':combined,'views':entries,
        'verification':{'structural':'NOT_RUN','visual':'NOT_RUN','runtime':'NOT_RUN'},'outcome':'NOT_RUN'}
