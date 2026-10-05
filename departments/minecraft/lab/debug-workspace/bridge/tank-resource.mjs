import {sha256,stableJson} from './json.mjs';
import {validTankGeometry} from '../evidence/tank-contract.mjs';
import {requireTankProfile} from './tank-preflight.mjs';
import {privatePath} from './result-export-source.mjs';

function privateFields(value) {
  if(privatePath(value))return true;
  if(Array.isArray(value))return value.some(privateFields);
  return value&&typeof value==='object'?Object.entries(value).some(([key,v])=>/(credential|password|secret|token|authorization|nonce|workspaceDir|canonicalWorldRoot|runDir)/i.test(key)||privateFields(v)):false;
}

function crc32(bytes) {
  let crc=0xffffffff;
  for(const byte of bytes) {
    crc^=byte;
    for(let bit=0;bit<8;bit++)crc=(crc>>>1)^((crc&1)?0xedb88320:0);
  }
  return (crc^0xffffffff)>>>0;
}
/** New stored-ZIP capsule for subsequent registration, never an edit of an existing artifact. */
export function buildTankPresentationResource({saved,profile}) {
  requireTankProfile(profile);
  const end=Buffer.alloc(22);end.writeUInt32LE(0x06054b50);
  if(!profile.grid)return end;
  const r=saved?.recipe,hash=saved?.recipeHash?.replace(/^sha256:/,'');
  if(privateFields(r))throw new TypeError('TANK_RESOURCE_PRIVATE_FIELDS_NOT_EXPORTABLE');
  if(saved?.status!=='GEOMETRY_VERIFIED'||r?.v!==1||r.kind!=='tank_recipe'||r.dimension!=='minecraft:overworld'
      ||!validTankGeometry({...r.origin,...r.dimensions})||r.presentation?.gridSpacing!==1
      ||!['NATIVE','OBSERVATION_BRIGHT'].includes(r.presentation?.mode)||sha256(stableJson(r))!==hash
      ||saved.displayMode!==(profile.brightness?'OBSERVATION_BRIGHT':'NATIVE'))throw new TypeError('TANK_RESOURCE_RECIPE_OR_DISPLAY_MISMATCH');
  const capsule={status:saved.status,displayMode:saved.displayMode,recipeHash:saved.recipeHash,recipe:saved.recipe};
  const data=Buffer.from(stableJson(capsule)),name=Buffer.from('kneekura/tank-presentation.json');
  if(data.length>64*1024)throw new RangeError('TANK_RESOURCE_CAPSULE_TOO_LARGE');
  const crc=crc32(data),local=Buffer.alloc(30),central=Buffer.alloc(46);
  local.writeUInt32LE(0x04034b50);local.writeUInt16LE(20,4);local.writeUInt32LE(crc,14);
  local.writeUInt32LE(data.length,18);local.writeUInt32LE(data.length,22);local.writeUInt16LE(name.length,26);
  central.writeUInt32LE(0x02014b50);central.writeUInt16LE(20,4);central.writeUInt16LE(20,6);
  central.writeUInt32LE(crc,16);central.writeUInt32LE(data.length,20);central.writeUInt32LE(data.length,24);central.writeUInt16LE(name.length,28);
  end.writeUInt16LE(1,8);end.writeUInt16LE(1,10);end.writeUInt32LE(central.length+name.length,12);
  end.writeUInt32LE(local.length+name.length+data.length,16);
  return Buffer.concat([local,name,data,central,name,end]);
}
