import {requireTankIdentity,boundedTankPacket,validTankGeometry} from './tank-contract.mjs';

export function buildTankMap({status,positions=[],declaredPaths=[],viewport={}}={}) {
  if(status?.schema!=='kneekura.tank-status/v1')throw new TypeError('TANK_STATUS_REQUIRED');
  const identity=requireTankIdentity(status.identity),geometry=status.geometry?.value;
  if(!geometry)return {schema:'kneekura.tank-map/v1',identity,status:'NOT_CAPTURED',bounds:null,axes:null,layers:null,evidenceRefs:[]};
  if(!validTankGeometry(geometry))throw new TypeError('INVALID_TANK_GEOMETRY');
  const samples=Array.isArray(positions)?positions:positions.samples;
  if(!Array.isArray(samples)||samples.length>128||!Array.isArray(declaredPaths)||declaredPaths.length>64)throw new RangeError('TANK_MAP_DISPLAY_LIMIT');
  const point=p=>{
    if(!p||['x','y','z'].some(k=>!Number.isFinite(p[k])||Math.abs(p[k])>30000000))throw new TypeError('INVALID_TANK_POSITION');
    return {...structuredClone(p),outsideTank:p.x<geometry.x||p.x>geometry.x+geometry.width||p.y<geometry.y||p.y>geometry.y+geometry.height||p.z<geometry.z||p.z>geometry.z+geometry.depth};
  };
  const display={width:viewport.width??960,height:viewport.height??960,pixelsPerBlock:viewport.pixelsPerBlock??12,margin:32};
  if(![display.width,display.height].every(n=>Number.isSafeInteger(n)&&n>=128&&n<=4096)
      ||!Number.isFinite(display.pixelsPerBlock)||display.pixelsPerBlock<1||display.pixelsPerBlock>128)throw new TypeError('BOUNDED_TANK_VIEWPORT_REQUIRED');
  const segments=Array.isArray(positions)?[]:positions.segments??[];
  if(segments.length>127)throw new RangeError('TANK_MAP_SEGMENT_LIMIT');
  const sampleIds=new Set(samples.map(p=>p.sample_id));
  if(segments.some(s=>!sampleIds.has(s.from_sample_id)||!sampleIds.has(s.to_sample_id)))throw new TypeError('TANK_MAP_SEGMENT_SOURCE_MISSING');
  return boundedTankPacket({schema:'kneekura.tank-map/v1',identity,status:'AVAILABLE',geometry,
    bounds:{min:[geometry.x,geometry.z],max:[geometry.x+geometry.width,geometry.z+geometry.depth]},
    axes:{horizontal:'+X',vertical:'+Z',north:'-Z',gridSpacing:1,elevation:'TICK_VS_Y'},viewport:display,
    layers:{motion:{points:samples.map(point),segments:structuredClone(segments)},declaredNavigation:{nodes:declaredPaths.map(point)},walls:[]},
    evidenceRefs:status.geometry.sourceObservationIds??[],semantics:{autoFit:false,clampsOutliers:false,unknownWallsInvented:false}});
}
