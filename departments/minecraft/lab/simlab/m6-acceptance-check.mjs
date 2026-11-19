import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { readNetworkCompanion } from './network-companion.mjs';

const EXPECTED = [0, 1, 0, 1];

export function evaluateM6Acceptance(parsed, variable='wuqi') {
  if (parsed?.meta?.physicalSide !== 'CLIENT') {
    return {pass:false, reason:'acceptance requires CLIENT network companion'};
  }
  if (parsed?.meta?.bound !== true) {
    return {pass:false, reason:'acceptance requires bound scenario/run identity'};
  }

  const bare = normalizeVariable(variable);
  if (!bare) {
    return {pass:false, reason:'invalid variable', variable:String(variable ?? '')};
  }

  const applied = (parsed?.semantics ?? []).filter(row =>
    row.kind === 'ysm_molang_state_applied'
    && row.payload
    && row.payload.variable === bare
    && row.payload.controlledE2Qualified === true
    && row.payload.packetHandlerOrigin === true
    && row.payload.handledByClient === true
    && row.payload.exactVariableIdentity === true
    && Number.isFinite(row.payload.before)
    && Number.isFinite(row.payload.after)
    && row.payload.before !== row.payload.after
    && typeof row.payload.packetTraceIds === 'string'
    && row.payload.packetTraceIds.trim()
  );

  const byEntity = new Map();
  for (const row of applied) {
    const uuid = row.payload.entityUuid;
    if (typeof uuid !== 'string' || !uuid) continue;
    if (!byEntity.has(uuid)) byEntity.set(uuid, []);
    byEntity.get(uuid).push(row);
  }

  for (const [entityUuid, rows] of byEntity) {
    rows.sort((a,b)=>(a.seq ?? 0)-(b.seq ?? 0));
    for (let i=0; i<=rows.length-EXPECTED.length; i++) {
      const window = rows.slice(i, i+EXPECTED.length);
      if (!window.every((row,j)=>Number(row.payload.after) === EXPECTED[j])) continue;

      const traceIds = window.map(row=>row.payload.packetTraceIds.trim());
      if (new Set(traceIds).size !== traceIds.length) continue;

      return {
        pass:true,
        variable:bare,
        entityUuid,
        expected:EXPECTED,
        observed:window.map(row=>Number(row.payload.after)),
        packetTraceIds:traceIds,
        firstSeq:window[0].seq,
        lastSeq:window.at(-1).seq,
        firstGameTime:window[0].gameTime,
        lastGameTime:window.at(-1).gameTime,
        run:parsed?.meta?.run ?? null,
        scenario:parsed?.meta?.scenario ?? null
      };
    }
  }

  return {
    pass:false,
    reason:'no formal M6 0->1->0->1 window for one entity',
    variable:bare,
    appliedCount:applied.length,
    run:parsed?.meta?.run ?? null,
    scenario:parsed?.meta?.scenario ?? null
  };
}

function normalizeVariable(input) {
  if (typeof input !== 'string') return null;
  let bare=input.trim();
  if (bare.startsWith('variable.')) bare=bare.slice('variable.'.length);
  else if (bare.startsWith('v.')) bare=bare.slice(2);
  return /^[A-Za-z_][A-Za-z0-9_]*$/.test(bare) ? bare : null;
}

async function main() {
  const [, , file, variable='wuqi'] = process.argv;
  if (!file) {
    console.error('usage: node simlab/m6-acceptance-check.mjs <client.net.jsonl> [variable]');
    process.exitCode=2;
    return;
  }
  try {
    const parsed=await readNetworkCompanion(file);
    const result=evaluateM6Acceptance(parsed, variable);
    console.log(JSON.stringify(result,null,2));
    if (!result.pass) process.exitCode=1;
  } catch (e) {
    console.error(e?.stack ?? String(e));
    process.exitCode=2;
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  await main();
}
