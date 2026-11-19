const safe=Number.isSafeInteger;
const object=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
const only=(v,keys)=>object(v)&&Object.keys(v).every(k=>keys.includes(k));
const rootKeys=['schema','semantics','targetRevision','sampleTick','observerCostNanos','observerCostScope','data'];
const dataKeys=['radius','requestedCellCount','classificationScope','effectiveMalusStatus','observerDeadlineScope',
  'dimension','centerX','centerY','centerZ','chunkAccessScope','status','truncated','cells'];
const baseCell=['x','y','z','status','observationRole','effectiveMalusStatus','evaluatedByPathfinderStatus'];
function validCell(c,d) {
  if(!object(c)||!['x','y','z'].every(k=>safe(c[k]))||c.y!==d.centerY||
      Math.abs(c.x-d.centerX)>d.radius||Math.abs(c.z-d.centerZ)>d.radius||
      c.observationRole!=='OBSERVER_QUERIED_GROUND_ONLY'||c.effectiveMalusStatus!=='NOT_EXPOSED'||
      c.evaluatedByPathfinderStatus!=='NOT_CAPTURED')return false;
  if(c.status==='NOT_EXPOSED')return only(c,[...baseCell,'detail'])&&
    typeof c.detail==='string'&&c.detail.length>0&&c.detail.length<=128;
  if(c.status!=='AVAILABLE'||!only(c,[...baseCell,'pathType','defaultTypeMalus','defaultTypeMalusStatus',
    'selectedMobOverrideStatus','selectedMobOverride'])||typeof c.pathType!=='string'||!/^[A-Z_]{1,64}$/.test(c.pathType))return false;
  if(!(Number.isFinite(c.defaultTypeMalus)?c.defaultTypeMalusStatus===undefined:
    c.defaultTypeMalus===undefined&&c.defaultTypeMalusStatus==='NOT_EXPOSED'))return false;
  return c.selectedMobOverrideStatus==='AVAILABLE'?Number.isFinite(c.selectedMobOverride):
    ['NOT_PRESENT','NOT_EXPOSED'].includes(c.selectedMobOverrideStatus)&&c.selectedMobOverride===undefined;
}

/** Observer-only static ground query; never promotes cached overrides to effective navigation costs. */
export function validTerrainGroundQuery(record) {
  const p=record?.payload,d=p?.data;
  if(record?.source?.side!=='SERVER'||!only(p,rootKeys)||p.schema!=='kneekura.terrain-ground-query/v1'||
      p.semantics!=='OBSERVER_QUERIED_GROUND_NOT_PATHFINDER_EVALUATION'||!safe(p.targetRevision)||p.targetRevision<1||
      !safe(p.sampleTick)||p.sampleTick<0||p.sampleTick!==record.gameTime||!safe(p.observerCostNanos)||p.observerCostNanos<0||
      p.observerCostScope!=='GROUND_CAPTURE_ONLY_EXCLUDES_ENCODING_WRITER_VIEWER'||!only(d,dataKeys)||
      !safe(d.radius)||d.radius<0||d.radius>3||d.requestedCellCount!==(2*d.radius+1)**2||
      !['centerX','centerY','centerZ'].every(k=>safe(d[k]))||typeof d.dimension!=='string'||
      !/^[a-z0-9_.-]+:[a-z0-9_./-]{1,256}$/.test(d.dimension)||
      d.classificationScope!=='STATIC_GROUND_NOT_SELECTED_EVALUATOR_ADMISSION'||d.effectiveMalusStatus!=='NOT_EXPOSED'||
      d.observerDeadlineScope!=='CHECKED_BETWEEN_CELLS_CANNOT_PREEMPT_ONE_CLASSIFIER_CALL'||
      d.chunkAccessScope!=='LOADED_NONBLOCKING_MAY_WARM_LOOKUP_CACHE_AND_PROFILER'||
      !Array.isArray(d.cells)||d.cells.length>d.requestedCellCount||typeof d.truncated!=='boolean'||
      d.truncated!==(d.cells.length<d.requestedCellCount)||!d.cells.every(c=>validCell(c,d))||
      new Set(d.cells.map(c=>c.x+','+c.y+','+c.z)).size!==d.cells.length||
      d.status!==(d.truncated||d.cells.some(c=>c.status!=='AVAILABLE')?'PARTIAL':'AVAILABLE'))return false;
  return new TextEncoder().encode(JSON.stringify(p)).length<=32768;
}
