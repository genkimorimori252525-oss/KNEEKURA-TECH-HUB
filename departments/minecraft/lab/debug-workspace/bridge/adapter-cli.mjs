#!/usr/bin/env node
/** One bounded invocation; arguments come exclusively from the registered host adapter. */
import path from 'node:path';
import { readRegisteredFile } from './materials.mjs';
import { decodeJson } from './json.mjs';
import { invokeAdapter } from './adapter.mjs';
async function read(file,limit) {
  if(typeof file!=='string'||!path.isAbsolute(file)) throw new Error('ABSOLUTE_FILE_REQUIRED');
  return decodeJson((await readRegisteredFile({root:path.dirname(file),relativePath:path.basename(file),maxBytes:limit})).bytes,limit);
}
try {
  const args=process.argv.slice(2);
  if(args.length!==4||args[0]!=='--owner'||args[2]!=='--request') throw new Error('FIXED_ARGUMENTS_REQUIRED');
  const result=await invokeAdapter(await read(args[1],65536),await read(args[3],16384));
  const output=JSON.stringify(result)+'\n';
  if(Buffer.byteLength(output)>65536) throw new Error('OUTPUT_LIMIT');
  process.stdout.write(output);
} catch {
  // Never expose owner paths, raw parser contents or filesystem errors.
  process.stdout.write(JSON.stringify({schemaVersion:1,status:'BLOCKED',reasonCode:'INVALID_OR_UNAVAILABLE_ADAPTER_INPUT',execution:'NOT_RUN',runtimeAttestation:'NOT_ESTABLISHED'})+'\n');
  process.exitCode=2;
}
