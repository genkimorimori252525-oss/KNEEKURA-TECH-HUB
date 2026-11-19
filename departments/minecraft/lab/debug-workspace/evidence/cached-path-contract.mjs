export function validSnapshotReference(ref, revision, namespace) {
  if (!ref || ref.allocator !== 'SNAPSHOT_REFERENCE' || ref.targetRevision !== revision) return false;
  if (ref.status === 'NOT_EXPOSED') return ref.detail === 'REFERENCE_LIMIT' && !Object.hasOwn(ref,'token');
  if (ref.status !== 'AVAILABLE' || typeof ref.token !== 'string') return false;
  const parts=ref.token.split(':');
  return parts.length === 3 && parts[0] === namespace && parts[1] === String(revision) &&
    /^[1-9][0-9]*$/.test(parts[2]) && Number(parts[2]) <= 256;
}

export function incompleteCachedFields(v) {
  if (!v || typeof v !== 'object') return false;
  return Object.entries(v).some(([k,child])=>((k === 'status' || k.endsWith('Status')) && child !== 'AVAILABLE') ||
    (k === 'truncated' && child === true) || incompleteCachedFields(child));
}

// Shared exact-Path cached data, used by memory snapshots and original Navigation returns.
export function validCachedPathData(d) {
  if (!d || typeof d !== 'object' || Array.isArray(d)) return false;
  const unknown=v=>v?.status === 'NOT_EXPOSED';
  const point=v=>unknown(v) || (v?.status === 'AVAILABLE' && ['x','y','z'].every(k=>Number.isSafeInteger(v[k])));
  const scalar=v=>unknown(v) || (v?.status === 'AVAILABLE' && Number.isFinite(v.value));
  let valid=d.semantics === 'CACHED_MEMORY_ROUTE_NOT_ADOPTION_ACTUAL_MOTION_OR_SEARCH_FRONTIER' &&
    Number.isSafeInteger(d.nextNodeIndex) && typeof d.canReach === 'boolean' && point(d.target) && scalar(d.distanceToTarget);
  if (d.nodesStatus === 'NOT_EXPOSED') valid &&= !Object.hasOwn(d,'nodes') && ['NULL_NODE_LIST','CUSTOM_NODE_LIST'].includes(d.nodesDetail);
  else valid &&= Number.isSafeInteger(d.nodeCount) && d.nodeCount >= 0 &&
    d.truncated === (d.nodeCount > 64) && d.nodesStatus === (d.truncated ? 'PARTIAL' : 'AVAILABLE') &&
    Array.isArray(d.nodes) && d.nodes.length === Math.min(d.nodeCount,64) && d.nodes.every(n=>unknown(n) ||
      (['AVAILABLE','PARTIAL'].includes(n.status) && ['x','y','z'].every(k=>Number.isSafeInteger(n[k])) &&
        (n.status === 'PARTIAL' || (typeof n.type === 'string' && Number.isFinite(n.costMalus)))));
  return valid;
}

export const exactObjectKeys=(value,keys)=>value!==null&&typeof value==='object'&&!Array.isArray(value)&&
  Object.keys(value).length===keys.length&&Object.keys(value).every(k=>keys.includes(k));
export function sameCapturedValue(a,b) {
  if(Array.isArray(a))return Array.isArray(b)&&a.length===b.length&&a.every((v,i)=>sameCapturedValue(v,b[i]));
  return a!==null&&typeof a==='object'?b!==null&&typeof b==='object'&&!Array.isArray(b)&&
    Object.keys(a).length===Object.keys(b).length&&Object.keys(a).every(k=>sameCapturedValue(a[k],b[k])):a===b;
}
function strictPathReference(ref,revision) {
  return validSnapshotReference(ref,revision,'path')&&exactObjectKeys(ref,
    ['status','allocator','targetRevision',ref.status==='AVAILABLE'?'token':'detail']);
}
export function validPathReferenceFact(p,revision) {
  if(p?.present===false)return exactObjectKeys(p,['present']);
  return p?.present===true&&exactObjectKeys(p,['present','className','identity'])&&typeof p.className==='string'&&
    p.className.length>0&&p.className.length<=512&&strictPathReference(p.identity,revision);
}
export function validCachedPathFact(p,revision) {
  if(p?.present===false)return exactObjectKeys(p,['present']);
  if(p?.present!==true||!exactObjectKeys(p,['present','className','identity','cachedFields'])||
    !validPathReferenceFact({present:p.present,className:p.className,identity:p.identity},revision))return false;
  const value=p.cachedFields;
  if(value?.status==='NOT_EXPOSED')return (exactObjectKeys(value,['className','status'])&&value.className===p.className&&
    p.className!=='net.minecraft.world.level.pathfinder.Path')||(exactObjectKeys(value,['status','detail'])&&
    typeof value.detail==='string'&&value.detail.startsWith('MEMBER_UNAVAILABLE:'));
  return p.className==='net.minecraft.world.level.pathfinder.Path'&&exactObjectKeys(value,['status','className','encoding','kind','data'])&&
    value.className===p.className&&value.encoding==='TYPED_CACHED_MEMORY_V1'&&value.kind==='PATH'&&
    ['AVAILABLE','PARTIAL'].includes(value.status)&&validCachedPathData(value.data)&&strictPathReference(value.data.instanceIdentity,revision)&&
    sameCapturedValue(value.data.instanceIdentity,p.identity)&&(value.status!=='AVAILABLE'||!incompleteCachedFields(value.data));
}
/** Cross-check a raw source boolean without deriving equality from unknown reference tokens. */
export function consistentRawPathMatch(match,requested,cached,fullCopies=false) {
  if(match){
    if(fullCopies)return sameCapturedValue(requested,cached);
    return requested.present===cached.present&&(!requested.present||requested.className===cached.className&&
      sameCapturedValue(requested.identity,cached.identity));
  }
  if(!requested.present&&!cached.present)return false;
  return !requested.present||!cached.present||requested.identity.status!=='AVAILABLE'||cached.identity.status!=='AVAILABLE'||
    requested.identity.token!==cached.identity.token;
}
