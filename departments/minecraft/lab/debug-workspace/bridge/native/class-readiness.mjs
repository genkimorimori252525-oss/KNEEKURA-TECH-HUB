import {readRegisteredFile} from '../materials.mjs';

/** Finite byte/resource readiness only: not source freshness or transformed bytecode attestation. */
export async function verifyCompiledClasses({outputRoot,classes}){
 if(!Array.isArray(classes)||classes.length<1||classes.length>64||
  classes.some(c=>!c||typeof c.className!=='string'||!c.className.match(/^[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)+$/)||
   Object.keys(c).some(k=>!['className','sha256'].includes(k)))||new Set(classes.map(c=>c.className)).size!==classes.length)
  throw new Error('CLASS_READINESS_SELECTION');
 const classResources=[];
 for(const c of classes){
  const file=await readRegisteredFile({root:outputRoot,relativePath:c.className.replaceAll('.','/')+'.class',expectedSha256:c.sha256,maxBytes:4*1024*1024});
  if(file.bytes.length<10||file.bytes.readUInt32BE(0)!==0xcafebabe)throw new Error('INVALID_CLASS_RESOURCE: '+c.className);
  classResources.push({className:c.className,sha256:file.sha256});
 }
 return {status:'COMPILED_RESOURCES_READY',outputRoot,classResources,sourceFreshness:'NOT_ATTESTED'};
}
