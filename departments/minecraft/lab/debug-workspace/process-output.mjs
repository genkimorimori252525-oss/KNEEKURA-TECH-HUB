import {spawn as spawnProcess} from 'node:child_process';
/** Git preflight collection: wait for drained streams, with bounded time and buffering. */
export async function collectProcess(command,args,options={}) {
 const timeoutMs=options.timeoutMs??5000,maxOutputBytes=options.maxOutputBytes??4*1024*1024;
 if(!Number.isInteger(timeoutMs)||timeoutMs<1||timeoutMs>60000||!Number.isInteger(maxOutputBytes)||maxOutputBytes<1||maxOutputBytes>4*1024*1024)throw new TypeError('INVALID_PROCESS_COLLECTION_BUDGET');
 return await new Promise(resolve=>{
  const child=(options.spawn??spawnProcess)(command,args,{windowsHide:true,stdio:['ignore','pipe','pipe']});
  let stdout='',stderr='',bytes=0,settled=false;
  const finish=value=>{if(settled)return;settled=true;clearTimeout(timer);resolve(value);};
  const failed=error=>{
   if(settled)return;
   try{child.kill?.('SIGKILL');}catch{}
   child.stdout?.destroy?.();child.stderr?.destroy?.();child.unref?.();
   finish({ok:false,error,stdout,stderr});
  };
  const timer=setTimeout(()=>failed('PROCESS_TIMEOUT'),timeoutMs);
  const consume=(chunk,lane)=>{
   if(settled)return;
   const buffer=Buffer.isBuffer(chunk)?chunk:Buffer.from(chunk),remaining=maxOutputBytes-bytes;
   const part=buffer.subarray(0,remaining).toString();if(lane==='stdout')stdout+=part;else stderr+=part;
   bytes+=Math.min(buffer.length,remaining);if(buffer.length>remaining)failed('PROCESS_OUTPUT_LIMIT');
  };
  child.stdout?.on('data',chunk=>consume(chunk,'stdout'));child.stderr?.on('data',chunk=>consume(chunk,'stderr'));
  child.stdout?.on('error',error=>failed('PROCESS_STDOUT_ERROR:'+error.message));child.stderr?.on('error',error=>failed('PROCESS_STDERR_ERROR:'+error.message));
  child.on('error',error=>finish({ok:false,error:error.message,stdout,stderr}));
  child.on('close',code=>finish({ok:code===0,code,stdout:stdout.trim(),stderr:stderr.trim()}));
 });
}
