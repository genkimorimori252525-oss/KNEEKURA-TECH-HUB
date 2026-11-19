import { mkdtemp, readFile, rm, stat } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const options = new Map();
for (let i = 2; i < process.argv.length; i += 2) {
  const key = process.argv[i]; const value = process.argv[i + 1];
  if (!['--java-home', '--forge-classpath-file', '--arena-source-dir'].includes(key) || !value || options.has(key))
    throw new Error('Usage: --java-home REGISTERED_JDK [--forge-classpath-file JAR_LIST_JSON --arena-source-dir MAIN_JAVA_DIR]');
  options.set(key, value);
}
if (!options.has('--java-home')) throw new Error('Explicit registered JDK path required');
const here = path.dirname(fileURLToPath(import.meta.url));
const packageDir = 'com/github/tartaricacid/touhoulittlemaid/sim/debug';
const main = path.join(here, 'src/main/java', packageDir);
const tests = path.join(here, 'src/test/java', packageDir);
const work = await mkdtemp(path.join(tmpdir(), 'kneekura-capture-source-'));
const suffix = process.platform === 'win32' ? '.exe' : '';
const javac = path.join(options.get('--java-home'), 'bin', 'javac' + suffix);
const java = path.join(options.get('--java-home'), 'bin', 'java' + suffix);
function run(command, args) {
  const result = spawnSync(command, args, { encoding: 'utf8', timeout: 120000, maxBuffer: 4 * 1024 * 1024 });
  if (result.stdout) process.stdout.write(result.stdout);
  if (result.stderr) process.stderr.write(result.stderr);
  if (result.error || result.status !== 0) throw result.error ?? new Error(`Source check failed: ${result.status}`);
}
try {
  const pure = ['CaptureSession', 'CaptureBarrier', 'CaptureRestoration', 'ImageArtifact', 'CapturePolicy', 'CaptureClock'];
  run(javac, ['--release', '17', '-d', work, ...pure.map(n => path.join(main, `KneekuraDebug${n}.java`)),
    ...pure.map(n => path.join(tests, `KneekuraDebug${n}SelfTest.java`))]);
  for (const name of pure) run(java, ['-cp', work, `com.github.tartaricacid.touhoulittlemaid.sim.debug.KneekuraDebug${name}SelfTest`]);
  if (options.has('--forge-classpath-file')) {
    const jars = JSON.parse(await readFile(options.get('--forge-classpath-file'), 'utf8'));
    if (!Array.isArray(jars) || !jars.length || jars.length > 1024 || jars.some(p => typeof p !== 'string' || !path.isAbsolute(p) || !p.endsWith('.jar')))
      throw new Error('Expected explicit absolute real dependency jar paths');
    for (const jar of jars) if (!(await stat(jar)).isFile()) throw new Error('Dependency is not a file');
    const forge = ['Env', 'CaptureSession', 'CaptureBarrier', 'CaptureRestoration', 'ImageArtifact',
      'CardinalCapture', 'CapturePolicy', 'CaptureOwner', 'CaptureEvidenceSink', 'EvidenceWriter', 'Durability'];
    run(javac, ['--release', '17', '-proc:none', '-classpath', jars.join(path.delimiter),
      '-sourcepath', options.get('--arena-source-dir') ?? path.join(here, 'src/main/java'),
      '-d', work, ...forge.map(n => path.join(main, `KneekuraDebug${n}.java`))]);
    run(javac, ['--release', '17', '-proc:none', '-classpath', [work, ...jars].join(path.delimiter),
      '-d', work, path.join(tests, 'KneekuraDebugCaptureWriterSelfTest.java')]);
    run(java, ['-cp', [work, ...jars].join(path.delimiter),
      'com.github.tartaricacid.touhoulittlemaid.sim.debug.KneekuraDebugCaptureWriterSelfTest']);
    process.stdout.write('Actual dependency source compilation passed; runtime execution NOT_RUN\n');
  } else process.stdout.write('Pure source checks passed; actual Forge dependency compilation NOT_RUN\n');
} finally { await rm(work, { recursive: true, force: true }); }
