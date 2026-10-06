import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const options = new Map();
for (let i = 2; i < process.argv.length; i += 2) {
  const key = process.argv[i], value = process.argv[i + 1];
  if (key !== '--java-home' || !value || options.has(key))
    throw new Error('Usage: node check-microkernel.mjs --java-home REGISTERED_JDK');
  options.set(key, value);
}
if (!options.has('--java-home')) throw new Error('Explicit registered JDK path required');

const here = path.dirname(fileURLToPath(import.meta.url));
const packageDir = 'org/kneekura/techhub/warfarewings/physics';
const mainDir = path.join(here, 'src/main/java', packageDir);
const testDir = path.join(here, 'src/test/java', packageDir);
const work = await mkdtemp(path.join(tmpdir(), 'warfare-wings-physics-ai-'));
const classes = path.join(work, 'classes');
const generated = path.join(work, 'reports');
const suffix = process.platform === 'win32' ? '.exe' : '';
const javac = path.join(options.get('--java-home'), 'bin', 'javac' + suffix);
const java = path.join(options.get('--java-home'), 'bin', 'java' + suffix);

function run(command, args) {
  const result = spawnSync(command, args, { encoding: 'utf8', timeout: 120000, maxBuffer: 4 * 1024 * 1024 });
  if (result.stdout) process.stdout.write(result.stdout);
  if (result.stderr) process.stderr.write(result.stderr);
  if (result.error || result.status !== 0) throw result.error ?? new Error(`Command failed: ${result.status}`);
}

async function same(generatedPath, goldenPath) {
  const normalize = value => value.replace(/\r\n/g, '\n').replace(/\n*$/, '') + '\n';
  const a = normalize(await readFile(generatedPath, 'utf8'));
  const b = normalize(await readFile(goldenPath, 'utf8'));
  if (a === b) return;
  const al = a.split('\n');
  const bl = b.split('\n');
  const limit = Math.max(al.length, bl.length);
  for (let i = 0; i < limit; i++) {
    if (al[i] !== bl[i]) {
      throw new Error(`Generated report drift: ${path.basename(goldenPath)} line ${i + 1}\nGENERATED: ${al[i]}\nGOLDEN:    ${bl[i]}`);
    }
  }
  throw new Error(`Generated report drift: ${path.basename(goldenPath)}`);
}

try {
  const sources = [
    path.join(mainDir, 'Ia133Microkernel.java'),
    path.join(mainDir, 'WarfareWingsAircraft.java'),
    path.join(mainDir, 'PerformanceReportMain.java'),
    path.join(mainDir, 'TraceCsv.java'),
    path.join(mainDir, 'TraceScenarioMain.java'),
    path.join(mainDir, 'AircraftAtlasMain.java'),
    path.join(testDir, 'Ia133MicrokernelSelfTest.java'),
  ];
  run(javac, ['--release', '17', '-d', classes, ...sources]);
  run(java, ['-cp', classes, 'org.kneekura.techhub.warfarewings.physics.Ia133MicrokernelSelfTest']);
  run(java, ['-cp', classes, 'org.kneekura.techhub.warfarewings.physics.PerformanceReportMain', generated]);
  const traceA = path.join(generated, 'a6m-throttle-step-v1-a.csv');
  const traceB = path.join(generated, 'a6m-throttle-step-v1-b.csv');
  run(java, ['-cp', classes, 'org.kneekura.techhub.warfarewings.physics.TraceScenarioMain', traceA]);
  run(java, ['-cp', classes, 'org.kneekura.techhub.warfarewings.physics.TraceScenarioMain', traceB]);
  await same(traceA, traceB);
  const traceText = await readFile(traceA, 'utf8');
  const traceLines = traceText.trimEnd().split(/\r?\n/);
  if (traceLines.length !== 402) throw new Error(`Expected trace header + 401 rows, got ${traceLines.length}`);
  if (!traceLines[0].startsWith('schema_version,source,scenario_id,aircraft_id,tick,game_time,'))
    throw new Error('Unexpected trace schema header');
  await same(path.join(generated, 'a6m-p47n-source-microkernel.csv'), path.join(here, 'reports/a6m-p47n-source-microkernel.csv'));
  await same(path.join(generated, 'a6m-p47n-source-microkernel.md'), path.join(here, 'reports/a6m-p47n-source-microkernel.md'));
  const atlasA = path.join(generated, 'base-aircraft-source-atlas-a.csv');
  const atlasB = path.join(generated, 'base-aircraft-source-atlas-b.csv');
  const dataset = path.join(here, 'data/base-aircraft-anchor-v1.csv');
  run(java, ['-cp', classes, 'org.kneekura.techhub.warfarewings.physics.AircraftAtlasMain', dataset, atlasA]);
  run(java, ['-cp', classes, 'org.kneekura.techhub.warfarewings.physics.AircraftAtlasMain', dataset, atlasB]);
  await same(atlasA, atlasB);
  await same(atlasA, path.join(here, 'reports/base-aircraft-source-atlas.csv'));
  const atlasLines = (await readFile(atlasA, 'utf8')).trimEnd().split(/\r?\n/);
  if (atlasLines.length !== 25) throw new Error(`Expected Atlas header + 24 rows, got ${atlasLines.length}`);
  process.stdout.write('Warfare Wings Physics AI microkernel + 24-aircraft Atlas checks passed; real Minecraft parity NOT_RUN\n');
} finally {
  await rm(work, { recursive: true, force: true });
}