/** A data check is not native PASS until owned exit, clean ACK and seal are verified. */
export async function finalizeNativeTrial({current,stop,read,finalize}){
 const stopped=await stop();
 if(stopped.ok!==true||stopped.cleanup?.status!=='VERIFIED_EXIT')return {status:'FAIL',reason:'NATIVE_EXIT_NOT_VERIFIED',stopped,finalization:null};
 const after=await read();
 if(after.live!==false||after.runId!==current.runId||after.runSnapshotId!==current.runSnapshotId)return {status:'FAIL',reason:'NATIVE_STOP_IDENTITY_OR_LIVENESS',stopped,finalization:null};
 const clean=after.evidenceShutdown?.clean===true,finalization=await finalize(after,{cleanShutdown:clean});
 return {status:clean&&finalization.manifest?.status==='EVIDENCE_COMPLETE'?'PASS':'FAIL',
  reason:!clean?'NATIVE_SHUTDOWN_UNCLEAN':finalization.manifest?.status!=='EVIDENCE_COMPLETE'?'NATIVE_EVIDENCE_PARTIAL':null,
  stopped,shutdown:after.evidenceShutdown,finalization};
}
