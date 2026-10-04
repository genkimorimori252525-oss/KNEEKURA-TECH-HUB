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
