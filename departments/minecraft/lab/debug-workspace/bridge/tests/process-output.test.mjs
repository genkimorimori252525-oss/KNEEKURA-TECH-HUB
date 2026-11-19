import test from 'node:test';
import assert from 'node:assert/strict';
import {EventEmitter} from 'node:events';
import {collectProcess} from '../../process-output.mjs';
test('process output is finalized after stream close, not exit notification',async()=>{
 const child=new EventEmitter();child.stdout=new EventEmitter();child.stderr=new EventEmitter();
 const result=collectProcess('fixture',[],{spawn:()=>child});
 child.stdout.emit('data',Buffer.from('first'));child.emit('exit',0);
 child.stdout.emit('data',Buffer.from('-last'));child.stderr.emit('data',Buffer.from('tail'));child.emit('close',0);
 assert.deepEqual(await result,{ok:true,code:0,stdout:'first-last',stderr:'tail'});
});
test('spawn error is preserved without claiming complete output',async()=>{
 const child=new EventEmitter();child.stdout=new EventEmitter();child.stderr=new EventEmitter();
 const result=collectProcess('fixture',[],{spawn:()=>child});child.emit('error',new Error('not started'));
 assert.equal((await result).ok,false);
});
test('real subprocess timeout terminates collection within its bound',async()=>{
 const started=Date.now();const result=await collectProcess(process.execPath,['-e','setInterval(()=>{},1000)'],{timeoutMs:100});
 assert.equal(result.ok,false);assert.equal(result.error,'PROCESS_TIMEOUT');assert.ok(Date.now()-started<1500);
});
test('real subprocess output over limit is rejected without unbounded buffering',async()=>{
 const result=await collectProcess(process.execPath,['-e','process.stdout.write(Buffer.alloc(65536,120))'],{maxOutputBytes:128});
 assert.equal(result.ok,false);assert.equal(result.error,'PROCESS_OUTPUT_LIMIT');assert.ok(Buffer.byteLength(result.stdout)+Buffer.byteLength(result.stderr)<=128);
});
test('invalid collection budgets are rejected',async()=>{
 await assert.rejects(collectProcess('fixture',[],{timeoutMs:Infinity}),/INVALID_PROCESS_COLLECTION_BUDGET/);
});
test('exited parent with inherited descendant pipe cannot make collection wait forever',async()=>{
 const code="require('node:child_process').spawn(process.execPath,['-e','setTimeout(()=>{},500)'],{stdio:['ignore','inherit','ignore']});process.exit(0)";
 const started=Date.now();const result=await collectProcess(process.execPath,['-e',code],{timeoutMs:100});
 assert.equal(result.ok,false);assert.equal(result.error,'PROCESS_TIMEOUT');assert.ok(Date.now()-started<1500);
});
test('timed-out owned subprocess that ignores SIGTERM is force-stopped',async(t)=>{
 const {spawn}=await import('node:child_process');let child;
 t.after(()=>{try{child?.kill('SIGKILL');}catch{}});
 const result=await collectProcess(process.execPath,['-e',"process.on('SIGTERM',()=>{});process.stdout.write('ready');setInterval(()=>{},1000)"],{timeoutMs:200,spawn:(...args)=>{child=spawn(...args);return child;}});
 assert.equal(result.ok,false);assert.equal(result.error,'PROCESS_TIMEOUT');
 await new Promise(resolve=>setTimeout(resolve,50));assert.equal(child.signalCode,'SIGKILL');
});
