import path from 'node:path';
import {spawn} from 'node:child_process';
import {fileURLToPath,pathToFileURL} from 'node:url';

/** Windows detached PowerShell may exit0 without running -File. Keep it attached to this Node owner. */
export function runPowerShellScript(script,args=[],environment=process.env){
 return new Promise((resolve,reject)=>{
  const child=spawn('powershell.exe',['-NoProfile','-NonInteractive','-File',script,...args],{env:environment,detached:false,windowsHide:true,stdio:['ignore','inherit','inherit']});
  child.once('error',reject);child.once('exit',code=>resolve(code??1));
 });
}
if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href){
 try{process.exitCode=await runPowerShellScript(path.join(path.dirname(fileURLToPath(import.meta.url)),'gradle.ps1'),['runClient','--offline','--console=plain','-Dnet.minecraftforge.gradle.check.certs=false']);}
 catch(error){console.error('TANK_LAUNCH_BRIDGE_FAILED '+error.message);process.exitCode=1;}
}
