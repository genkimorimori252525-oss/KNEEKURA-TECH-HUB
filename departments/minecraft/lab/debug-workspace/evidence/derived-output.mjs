import path from 'node:path';
import {realpath,stat} from 'node:fs/promises';

const within=(root,file)=>{const r=path.relative(root,file);return r===''||(!r.startsWith('..'+path.sep)&&r!=='..'&&!path.isAbsolute(r));};
async function exists(file){try{await stat(file);return true;}catch(error){if(error.code==='ENOENT')return false;throw error;}}
/** Resolve directory links and reject every retained run ancestor, including other runs. */
export async function requireDerivedOutput(output,runDir=null,code='DERIVED_OUTPUT_MUST_BE_OUTSIDE_RETAINED_RUN') {
  const file=path.resolve(output),parent=await realpath(path.dirname(file)),resolved=path.join(parent,path.basename(file));
  if(runDir&&within(await realpath(runDir),resolved))throw new Error(code);
  for(let directory=parent;;directory=path.dirname(directory)) {
    if(await exists(path.join(directory,'run-snapshot.json'))||await exists(path.join(directory,'evidence','finalization.json')))throw new Error(code);
    if(directory===path.dirname(directory))break;
  }
  return resolved;
}
