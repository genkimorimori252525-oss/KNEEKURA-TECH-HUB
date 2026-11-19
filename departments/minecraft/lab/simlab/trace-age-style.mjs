/** Derived display only: game/cursor ticks, stable identity colors, no random state or evidence mutation. */
export function traceAgeStyle({traceClass,identity,sampleTick,currentTick,lifetimeTicks=100}={}) {
  if(!['MOB_ACTUAL','PROJECTILE_ACTUAL'].includes(traceClass)||typeof identity!=='string'||!identity||identity.length>512||
    ![sampleTick,currentTick,lifetimeTicks].every(Number.isSafeInteger)||sampleTick<0||currentTick<0||lifetimeTicks<1||lifetimeTicks>10000)
    throw new TypeError('INVALID_TRACE_AGE_STYLE');
  const age=currentTick-sampleTick;
  if(age<0||age>=lifetimeTicks)return null;
  const band=Math.floor(age*3/lifetimeTicks),yellow=[255,211,83],red=[255,96,83];
  let rgb=[105,215,255];
  if(traceClass==='PROJECTILE_ACTUAL') {
    let hash=2166136261;for(let i=0;i<identity.length;i++)hash=Math.imul(hash^identity.charCodeAt(i),16777619)>>>0;
    // Reserve yellow/red for age; green/cyan/blue/violet form the stable initial identity range.
    const hue=(100+hash%180)/60,sector=Math.floor(hue),f=hue-sector,low=76.5,up=low+178.5*f,down=255-178.5*f;
    rgb=([[],[down,255,low],[low,255,up],[low,down,255],[up,low,255]][sector]).map(Math.round);
    if(band)rgb=rgb.map((value,i)=>Math.round(value*(band===1?.5:.18)+(band===1?yellow:red)[i]*(band===1?.5:.82)));
  }else if(band)rgb=band===1?yellow:red;
  const alpha=band===0?255:band===1?210:Math.round(180*(lifetimeTicks-age)/(lifetimeTicks-Math.ceil(lifetimeTicks*2/3)));
  return {color:'rgb('+rgb.join(',')+')',alpha:alpha/255,ageBand:['NEW','MIDDLE','OLD'][band]};
}
