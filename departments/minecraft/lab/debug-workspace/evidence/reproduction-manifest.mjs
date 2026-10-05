import {realpath,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {sha256,decodeJson,hashId,stableJson} from '../bridge/json.mjs';
import {privatePath} from '../bridge/result-export-source.mjs';
import {validateVisualExperimentRequest} from './visual-request-contract.mjs';
import {requireTankTimeBudget} from '../bridge/tank-preflight.mjs';
import {boundedTankPacket} from './tank-contract.mjs';
function privateFields(value){
  if(privatePath(value))return true;
  if(Array.isArray(value))return value.some(privateFields);
  return value&&typeof value==='object'?Object.entries(value).some(([k,v])=>/(credential|password|secret|token|authorization|ownerNonce|workspaceDir|canonicalWorldRoot|runDir)/i.test(k)||privateFields(v)):false;
}
export function buildReproductionManifest({requestBytes,assertionsBytes,sourceBinding,worldBinding,observerProfile,comparison=null,exportReferences=null}) {
  if(!Buffer.isBuffer(requestBytes)||!Buffer.isBuffer(assertionsBytes))throw new TypeError('ORIGINAL_REQUEST_ASSERTION_BYTES_REQUIRED');
  const requestHash=sha256(requestBytes),assertionsHash=sha256(assertionsBytes);
  if(requestHash!==sourceBinding?.requestHash||assertionsHash!==sourceBinding?.assertionsHash)throw new TypeError('REPRODUCTION_ORIGINAL_BYTE_HASH_MISMATCH');
  const request=validateVisualExperimentRequest(decodeJson(requestBytes,128*1024)),assertions=decodeJson(assertionsBytes,256*1024);
  if(stableJson(request.assertions)!==stableJson(assertions))throw new TypeError('REPRODUCTION_REGISTERED_ASSERTION_MISMATCH');
  for(const key of ['requestHash','assertionsHash','canonicalFileHash','finalizationHash'])hashId(sourceBinding[key]);
  if(observerProfile?.reuseOwner===true||observerProfile?.reuseLease===true)throw new TypeError('REPRODUCTION_REQUIRES_NEW_OWNER');
  const safe={request,assertions,sourceBinding,worldBinding:worldBinding??null,observerProfile:observerProfile??null,comparison,exportReferences};
  if(privateFields(safe))throw new TypeError('REPRODUCTION_PRIVATE_FIELDS_NOT_EXPORTABLE');
  const timeBudget=observerProfile?.timeBudget??null;if(timeBudget)requireTankTimeBudget(timeBudget);
  if(exportReferences)for(const key of ['resultHash','visualBundleHash'])if(exportReferences[key]!=null)hashId(exportReferences[key]);
  return boundedTankPacket({schema:'kneekura.reproduction-manifest/v1',status:worldBinding&&observerProfile?'PREPARATION_ONLY':'INCOMPLETE',
    experimentId:request.experiment_id,request:{contentHash:requestHash,bytes:requestBytes.length,semantics:'EXACT_ORIGINAL_BYTES_NOT_RESERIALIZED'},
    assertions:{contentHash:assertionsHash,bytes:assertionsBytes.length,semantics:'EXACT_ORIGINAL_BYTES_NOT_RESERIALIZED'},
    sourceBinding:structuredClone(sourceBinding),worldBinding:worldBinding??null,observerProfile:observerProfile??null,
    exportReferences,comparison:comparison?{status:comparison.status,before:comparison.before,after:comparison.after}:null,
    timeBudget,images:{status:exportReferences?.visualBundleHash?'RETAINED_CAS_REFERENCE_ONLY':'NOT_CAPTURED',visualBundleHash:exportReferences?.visualBundleHash??null,preFrames:'NOT_CAPTURED',limitations:['USE_ONLY_EXISTING_SEALED_CAPTURE_REFS_NO_RETROACTIVE_IMAGE_GENERATION']},
    replay:{requiresNewRunIdentity:true,requiresNewOwnerRegistration:true,reusesOriginalLease:false,automaticallyExecutes:false,
      preparationSteps:['VERIFY_ORIGINAL_AUTHORITY_SAVE_HASH','CREATE_PRIVATE_DISPOSABLE_COPY','VERIFY_BASELINE_AND_FIXTURE_HASHES',
        'RETAIN_PREDECESSOR_OWNER_RECEIPT','REGISTER_NEW_RUN_AND_OWNER','RECHECK_FULL_TIME_BUDGET_BEFORE_DISPATCH','FINALIZE_AND_RECORD_CLEANUP'],
      procedureReferences:['docs/KNEEKURA_REGISTERED_TANK_ROTATION.md','docs/KNEEKURA_REGISTERED_TANK_PRESENTATION.md'],
      executionReadiness:'NOT_AUTHORIZED_BY_MANIFEST'},limitations:['HASH_REFERENCES_REQUIRE_THE_ORIGINAL_BYTES_AND_EXISTING_CAS_EXPORT_VERIFICATION','NO_RUNTIME_OR_BEHAVIOR_ACCEPTANCE_INFERRED']});
}
export async function writeReproductionManifest({manifest,output,runDir}) {
  const file=path.resolve(output),parent=await realpath(path.dirname(file)),run=await realpath(runDir),resolved=path.join(parent,path.basename(file));
  const relative=path.relative(run,resolved);
  if(relative===''||(!relative.startsWith('..'+path.sep)&&relative!=='..'&&!path.isAbsolute(relative)))throw new Error('REPRODUCTION_OUTPUT_MUST_BE_OUTSIDE_RETAINED_RUN');
  boundedTankPacket(manifest);if(privateFields(manifest))throw new TypeError('REPRODUCTION_PRIVATE_FIELDS_NOT_EXPORTABLE');
  await writeFile(resolved,JSON.stringify(manifest,null,2)+'\n',{flag:'wx',mode:0o600});return resolved;
}
