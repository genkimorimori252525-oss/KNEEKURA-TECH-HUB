import {boundedTankPacket,requireTankIdentity} from './tank-contract.mjs';
import {requireTankTimeBudget} from '../bridge/tank-preflight.mjs';
const queries=new Set(['path_search','path_returned_nodes','movement_control','brain_memory_changes','terrain_ground','tank-status','tank-preflight']);
const finite=v=>Number.isFinite(v)&&v>=0?v:null;
/** Suggestions are typed read-only questions; they never invoke owner control or world commands. */
export function buildExperimentGuidance({digest,health={},capabilities={queries:[]},maxBookmarks=32}) {
  if(digest?.schema!=='kneekura.experiment-digest/v1')throw new TypeError('EXPERIMENT_DIGEST_REQUIRED');requireTankIdentity(digest.identity);
  if(!Number.isSafeInteger(maxBookmarks)||maxBookmarks<0||maxBookmarks>32)throw new TypeError('BOUNDED_BOOKMARK_LIMIT_REQUIRED');
  if(!Array.isArray(capabilities.queries)||capabilities.queries.length>queries.size||capabilities.queries.some(q=>!queries.has(q)))throw new TypeError('ALLOWLISTED_READ_ONLY_QUERY_REQUIRED');
  if(!Array.isArray(digest.retainedEvents)||digest.retainedEvents.length>50000)throw new TypeError('BOUNDED_RETAINED_EVENTS_REQUIRED');
  const seen=new Set(),events=digest.retainedEvents.toSorted((a,b)=>a.tick-b.tick||a.observationId.localeCompare(b.observationId));
  for(const e of events){if(typeof e.observationId!=='string'||seen.has(e.observationId)||!Number.isSafeInteger(e.tick)||!Array.isArray(e.evidenceRefs)
      ||!e.evidenceRefs.includes(e.observationId))throw new TypeError('RETAINED_EVENT_REFERENCE_REQUIRED');seen.add(e.observationId);}
  const selected=maxBookmarks?events.slice(-maxBookmarks):[];
  const captures=digest.retainedCaptures??[];
  if(!Array.isArray(captures)||captures.length>64)throw new TypeError('BOUNDED_CAPTURE_LINKS_REQUIRED');
  for(const c of captures)if(c.status!=='VERIFIED_SEALED_CAPTURE_REFERENCE'||!Number.isSafeInteger(c.captureTick)||!/^[a-f0-9]{64}$/.test(c.imageHash)||typeof c.sourceObservationId!=='string')throw new TypeError('VERIFIED_CAPTURE_REFERENCE_REQUIRED');
  const bookmarks=selected.map(e=>{const images=captures.filter(c=>c.captureTick===e.tick);return {tick:e.tick,kind:e.kind,observationId:e.observationId,evidenceRefs:e.evidenceRefs,
    identity:digest.identity,image:images.length?{status:'RETAINED_SAME_TICK_CONTEXT',references:images,relationship:'TIME_MATCH_NOT_EVENT_OR_CAUSE_PROOF'}:
      {status:'NOT_CAPTURED',reference:null,reason:'NO_VERIFIED_CAPTURE_LINK_IN_DIGEST'},packet:{status:'REGENERATE_FROM_RETAINED_EVIDENCE',cursorTick:e.tick}};});
  const refs=digest.evidenceRefs?.sourceObservationIds??[],suggestions=[],window=digest.quality.coverage.requestedWindow;
  const suggest=(channel,reason,expectedInformation)=>{
    if(!capabilities.queries.includes(channel))return;
    suggestions.push({reason,evidenceRefs:refs.slice(0,4),identity:digest.identity,proposedQuery:{channel,readOnly:true,
      subjectUuid:digest.identity.subjectUuid,targetRevision:digest.identity.targetRevision,...window,limit:8,maxNodes:32},expectedInformation});
  };
  if(health.targetMismatch)suggest('tank-status','対象照合が一致していないため、現在の記録と選択identityを確認する。','同一run/Arena/対象の状態。AIの判断理由は未確定。');
  if(health.leaseExpired)suggest('tank-preflight','記録上の期限終了後に開始権限を再利用できない。新ownerの準備を確認する。','新しい登録と現在の残時間。保存値は権限にならない。');
  if(digest.quality.coverage.gapCount>0)suggest('movement_control','要求区間に欠測・境界があるため、保持された移動記録を確認する。','取得された移動制御の事実。欠けた区間や原因は補完しない。');
  if(health.pathAdoptionMissing){suggest('path_returned_nodes','Pathの採用記録が不足しているため、返されたPathを確認する。','元検索の戻り値。採用や実移動を証明しない。');suggest('path_search','採用理由は未取得なので、検索の元記録を確認する。','保持された検索結果とcache。全候補や棄却理由は補完しない。');}
  const timeBudget=health.timeBudget??null;if(timeBudget)requireTankTimeBudget(timeBudget);
  return boundedTankPacket({schema:'kneekura.experiment-guidance/v1',identity:digest.identity,bookmarks,suggestions,
    displaySelection:{eligibleCount:events.length,displayedCount:bookmarks.length,omittedCount:events.length-bookmarks.length,selectionPolicy:'LATEST_RETAINED_EVENTS_SORTED_BY_TICK_AND_ID'},
    budgets:{timeBudget,remainingMs:finite(health.remainingMs),remainingSemantics:'HISTORICAL_REFERENCE_NOT_AUTHORITY',coldStartupMs:finite(health.coldStartupMs),warmStartupMs:finite(health.warmStartupMs),
      capacityBytes:finite(health.capacityBytes),repetitions:Number.isSafeInteger(health.repetitions)&&health.repetitions>=0?health.repetitions:null,cleanup:digest.cleanup??'UNKNOWN'},
    automaticallyExecutes:false,semantics:{bookmarksAreNotEventTotals:true,suggestionsAreNotCauses:true,missingImagesGenerated:false}});
}
