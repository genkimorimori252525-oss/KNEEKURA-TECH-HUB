import { sha256, stableJson, identifier, exactKeys, hashId } from '../bridge/json.mjs';
import { derivedArtifact } from './visual-artifacts.mjs';
import { validatePacket } from './visual-packet.mjs';
export { validatePacket } from './visual-packet.mjs';
import { escapeXml } from './visual-geometry.mjs';
const MODES=['HumanNormal','HumanDebug','HumanEvidenceReview'];
const INTERACTIONS={
 PRESENTATION_ONLY:['panel_layout','select_evidence','overlay_visibility','contact_sheet_zoom','retained_timeline_browse'],
 OBSERVATION_AFFECTING:['free_camera_move','change_fov','force_render_view','open_pausing_screen'],
 EXPERIMENT_MUTATION:['pause','slow_motion','teleport','change_blocks','change_entities','change_time_weather','change_config','scenario_action'],
};
export function classifyInteraction(type) {
 const classification=Object.keys(INTERACTIONS).find(key=>INTERACTIONS[key].includes(type));
 if(!classification)throw new TypeError('UNKNOWN_PRESENTATION_INTERACTION');
 return {type,classification,executionRoute:classification==='PRESENTATION_ONLY'?'LOCAL_PRESENTATION_ONLY':
   classification==='OBSERVATION_AFFECTING'?'OBSERVATION_CONTROL_WITH_PERTURBATION_RECEIPT':'TYPED_CONTROL_WITH_RECEIPT',
   mayExecuteFromPresentation:classification==='PRESENTATION_ONLY'};
}
export function createHumanPresentation({packet,mode,overlayIds=[],finding=null}) {
 packet=validatePacket(packet);
 if(!MODES.includes(mode)||!Array.isArray(overlayIds)||overlayIds.length>2||new Set(overlayIds).size!==overlayIds.length||
   overlayIds.some(v=>!['subject_labels','bounds'].includes(v))||(mode==='HumanNormal'&&overlayIds.length))throw new TypeError('INVALID_HUMAN_PRESENTATION');
 let card=null;
 if(finding!==null) {
  exactKeys(finding,['findingId','epistemicStatus','subjectUuid','view','checkId','result','explanation','evidenceHashes'],'VISUAL_FINDING');
  identifier(finding.findingId);identifier(finding.checkId);
  if(!['INFERRED','CORRELATED','DERIVED','UNKNOWN'].includes(finding.epistemicStatus)||
   !packet.binding.subjects.includes(finding.subjectUuid)||!packet.rawViews.some(v=>v.view===finding.view)||
   !['YES','NO','NOT_VISIBLE','AMBIGUOUS'].includes(finding.result)||typeof finding.explanation!=='string'||finding.explanation.length>1024)throw new TypeError('INVALID_VISUAL_FINDING');
  const check=packet.visualChecks.find(c=>c.checkId===finding.checkId);
  if(!check||check.subjectUuid!==finding.subjectUuid||check.answer!==finding.result||!check.evidenceViews.includes(finding.view))throw new TypeError('FINDING_VISUAL_CHECK_MISMATCH');
  const view=packet.rawViews.find(v=>v.view===finding.view);
  if(!Array.isArray(finding.evidenceHashes)||!finding.evidenceHashes.length||finding.evidenceHashes.length>4||
    finding.evidenceHashes.some(h=>h!==view.imageHash))throw new TypeError('FINDING_EVIDENCE_MISMATCH');
  card={...structuredClone(finding),stateWindow:packet.binding.stateWindow,experimentId:packet.binding.experimentId,
    sourceObservationId:packet.binding.sourceObservationId,acceptanceEffect:'NONE'};
 }
 const body={schemaVersion:1,kind:'human_visual_presentation',mode,binding:packet.binding,aiPacketId:packet.packetId,
   temporalStatus:'RETAINED_EVIDENCE_NOT_LIVE',sceneRole:'RAW_SCENE_RGB',overlayRole:'DERIVED_PRESENTATION',
   overlays:[...overlayIds],finding:card,rawArtifactHashes:packet.rawViews.map(v=>v.imageHash),
   humanCompositeArtifact:null,aiGenerationDependsOnHumanMode:false,canonicalMutationAllowed:false};
 return {presentationId:sha256(stableJson(body)),...body};
}
const name=ref=>{
 hashId(ref.sha256);
 if(!new RegExp(`^evidence/derived/visual/${ref.sha256}\\.(png|svg|json)$`).test(ref.path))throw new TypeError('UNSAFE_PRESENTATION_ARTIFACT');
 return ref.path.split('/').at(-1);
};
/** No script, network calls, renderer, or runtime controls. Radios change CSS presentation only. */
export function createEvidenceReviewArtifact({packet}) {
 packet=validatePacket(packet);
 const presentations=MODES.map(mode=>createHumanPresentation({packet,mode,overlayIds:mode==='HumanDebug'?['subject_labels','bounds']:[]}));
 const e=escapeXml; const b=packet.binding;
 const rawLinks=packet.rawViews.map(v=>{hashId(v.imageHash);return `<li><a href="../../raw/visual/${v.imageHash}.png">${e(v.view.toUpperCase())}: original RGB</a> · render frame ${v.renderFrame}</li>`;}).join('');
 const checks=packet.visualChecks.map(c=>`<li>${e(c.checkId)} · ${e(c.question)} · ${e(c.answer)} (${e(c.resolution)}) · ${e(c.evidenceViews.join(', '))}</li>`).join('')||'<li>No visual answers recorded</li>';
 const html=`<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src 'self'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"><title>Retained visual evidence ${e(b.captureId)}</title><style>
 body{margin:0;background:#121722;color:#edf1f7;font:16px system-ui,sans-serif}main{max-width:1100px;margin:auto;padding:28px}h1{font-size:26px}p{line-height:1.5}.muted{color:#a9b7cb}.badge{background:#593719;padding:9px 12px;border-radius:6px}input{margin:16px 4px 16px 0}label{margin-right:18px;cursor:pointer}.panel{display:none;padding:20px;background:#1b2331;border:1px solid #3b4a60;border-radius:9px}#normal:checked~.normal,#debug:checked~.debug,#review:checked~.review{display:block}img{max-width:100%;height:auto;image-rendering:auto}a{color:#a1d2ff}li{margin:9px 0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px}code{overflow-wrap:anywhere}details{margin-top:16px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px}
 </style></head><body><main><h1>Visual evidence review</h1><p class="badge">Retained evidence, not current runtime</p><p>${e(b.experimentId)} · generation ${b.generation} · ${e(b.captureId)} · server tick ${b.stateWindow.serverTickStart}</p><p class="muted">RunSnapshot: <code>${e(b.runSnapshotId)}</code> · ${e(packet.capture.restoration)} · sequential Cardinal-4, not same-frame</p>
 <input id="normal" name="mode" type="radio" checked><label for="normal">Human Normal</label><input id="debug" name="mode" type="radio"><label for="debug">Human Debug</label><input id="review" name="mode" type="radio"><label for="review">Human Evidence Review</label>
 <section class="panel normal"><h2>Retained scene</h2><p>Original scene RGB arranged into a compact contact sheet. The live Minecraft camera remains owned by the runtime.</p><img alt="North east south west contact sheet" src="${name(packet.contactSheet)}"></section>
 <section class="panel debug"><h2>Derived annotations</h2><p>Subject labels and projected bounds come from structured facts. They do not prove visibility through walls or identify rendered mesh pixels.</p><div class="grid"><img alt="Derived annotated contact sheet" src="${name(packet.annotatedContactSheet)}"><img alt="Exact top down schematic" src="${name(packet.topDown)}"></div><ul>${packet.labels.map(l=>`<li>${e(l.label)} = ${e(l.uuid)}</li>`).join('')}</ul></section>
 <section class="panel review"><h2>Evidence and checks</h2><ul>${checks}</ul><h3>Original camera views</h3><ul>${rawLinks}</ul><p><a href="${name(packet.structuredSummaryArtifact)}">Structured facts</a> · <a href="${name(packet.timelineArtifact)}">Selected timeline</a></p><details><summary>Exact identity and evidence cut</summary><pre>${e(JSON.stringify(b,null,2))}</pre></details><details><summary>Observer effects and verdicts</summary><pre>${e(JSON.stringify({capture:packet.capture,visualVerdict:packet.visualVerdict,behaviorVerdict:packet.behaviorVerdict,acceptance:packet.acceptance},null,2))}</pre></details></section>
 <p class="muted">Visual format is provisional. Real-task benchmark and runtime validation are deferred. Switching these panels only changes this retained presentation.</p></main></body></html>`;
 return derivedArtifact(Buffer.from(html),{role:'DERIVED_HUMAN_EVIDENCE_REVIEW',mediaType:'text/html',extension:'html',
   sourceObservationIds:packet.contactSheet.sourceObservationIds,rawSourceHashes:packet.rawViews.map(v=>v.imageHash),binding:b,
   details:{aiPacketId:packet.packetId,presentationIds:presentations.map(p=>p.presentationId),scriptEnabled:false}});
}
