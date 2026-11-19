import { createHash, randomBytes } from 'node:crypto';
import { appendFile, link, lstat, mkdir, open, readFile, stat, unlink, writeFile, rename } from 'node:fs/promises';
import { closeSync, openSync } from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { collectProcess } from './process-output.mjs';
import { verifyProcessesExited } from './process-stop.mjs';
import { loadBridgeRegistration, validateTechHubBinding } from './bridge/registration.mjs';
import { hashId, exactKeys, canonicalRunSnapshotBytes } from './bridge/json.mjs';
import { prepareOwnerControl, readPreparedOwnerControl, ownerLaunchEnvironment, ownerLaunchSelection } from './bridge/owner-prelaunch.mjs';
import { decisionHookLaunchOptions } from './decision-hook-launch.mjs';
import { motionOverlayLaunchEnvironment } from './motion-overlay-launch.mjs';

export const READY_PROTOCOL = 'KNEEKURA_DEBUG_READY_V1';
export const CONFIG_SCHEMA_VERSION = 1;

function nowIso() {
  return new Date().toISOString();
}

function safeIdPart(value) {
  return String(value).replace(/[^A-Za-z0-9._-]/g, '_').slice(0, 80);
}

export function createIdentity(prefix) {
  const stamp = new Date().toISOString().replace(/[-:.TZ]/g, '').slice(0, 14);
  return prefix + '-' + stamp + '-' + randomBytes(6).toString('hex');
}

async function exists(file) {
  try {
    await stat(file);
    return true;
  } catch {
    return false;
  }
}

async function writeJsonAtomic(file, value) {
  await mkdir(path.dirname(file), { recursive: true });
  const tmp = file + '.tmp-' + randomBytes(4).toString('hex');
  await writeFile(tmp, JSON.stringify(value, null, 2) + '\n', 'utf8');
  await rename(tmp, file);
}

async function appendTimeline(file, stage, data = {}) {
  const row = { at: nowIso(), stage, ...data };
  await mkdir(path.dirname(file), { recursive: true });
  await appendFile(file, JSON.stringify(row) + '\n', 'utf8');
}

function resolveFrom(base, value) {
  if (!value) return null;
  return path.isAbsolute(value) ? path.normalize(value) : path.resolve(base, value);
}

export function validateConfig(config, repoRoot) {
  const errors = [];
  if (!config || typeof config !== 'object') {
    return { ok: false, errors: ['config must be an object'] };
  }
  if (config.schemaVersion !== CONFIG_SCHEMA_VERSION) {
    errors.push('schemaVersion must be ' + CONFIG_SCHEMA_VERSION);
  }
  if (!config.workspaceId || typeof config.workspaceId !== 'string') {
    errors.push('workspaceId is required');
  }
  if (!config.workspaceDir || typeof config.workspaceDir !== 'string') {
    errors.push('workspaceDir is required');
  }
  if (!config.launch || typeof config.launch !== 'object') {
    errors.push('launch is required');
  } else {
    if (!config.launch.command || typeof config.launch.command !== 'string') {
      errors.push('launch.command is required');
    }
    if (config.launch.args != null && !Array.isArray(config.launch.args)) {
      errors.push('launch.args must be an array');
    }
    if (config.launch.env != null &&
        (typeof config.launch.env !== 'object' || Array.isArray(config.launch.env))) {
      errors.push('launch.env must be an object');
    }
  }
  if (config.readyTimeoutMs != null &&
      (!Number.isInteger(config.readyTimeoutMs) || config.readyTimeoutMs < 1000)) {
    errors.push('readyTimeoutMs must be an integer >= 1000');
  }
  if (config.worldName != null &&
      (typeof config.worldName !== 'string' || !config.worldName.trim())) {
    errors.push('worldName must be a non-empty string');
  }
  if (config.gameDir != null && typeof config.gameDir !== 'string') {
    errors.push('gameDir must be a string');
  }
  if (config.requireExistingWorld === true && !config.gameDir) {
    errors.push('gameDir is required when requireExistingWorld=true');
  }
  if (config.workspaceChecks != null && !Array.isArray(config.workspaceChecks)) {
    errors.push('workspaceChecks must be an array');
  }
  if (config.requireGitIdentity != null &&
      typeof config.requireGitIdentity !== 'boolean') {
    errors.push('requireGitIdentity must be boolean');
  }
  if(config.decisionHooks!=null && typeof config.decisionHooks!=='boolean')errors.push('decisionHooks must be boolean');
  if(config.motionOverlay!=null && typeof config.motionOverlay!=='boolean')errors.push('motionOverlay must be boolean');

  try { ownerLaunchSelection(config); }
  catch (error) { errors.push('ownerControl: ' + error.message); }

  const normalized = errors.length ? null : {
    ...config,
    workspaceId: safeIdPart(config.workspaceId),
    workspaceDir: resolveFrom(repoRoot, config.workspaceDir),
    runtimeRoot: resolveFrom(repoRoot, config.runtimeRoot || 'debug-runtime'),
    readyTimeoutMs: config.readyTimeoutMs == null ? 180000 : config.readyTimeoutMs,
    worldName: (config.worldName || 'KNEEKURA_DEBUG_WORLD').trim(),
    gameDir: config.gameDir
      ? resolveFrom(resolveFrom(repoRoot, config.workspaceDir), config.gameDir)
      : null,
    requireExistingWorld: config.requireExistingWorld === true,
    workspaceChecks: [...(config.workspaceChecks || [])],
    requireGitIdentity: config.requireGitIdentity === true,
    decisionHooks: config.decisionHooks === true,
    motionOverlay: config.motionOverlay === true,
    debugProfile: typeof config.debugProfile === 'string' && config.debugProfile.trim()
      ? config.debugProfile.trim()
      : 'FAST_DEBUG',
    launch: {
      ...config.launch,
      args: [...(config.launch.args || [])],
      env: { ...(config.launch.env || {}) },
      shell: config.launch.shell === true,
    },
  };

  return { ok: errors.length === 0, errors, config: normalized };
}


async function runWorkspaceChecks(checks, workspaceDir) {
  const results = [];
  for (const check of checks || []) {
    if (!check || typeof check !== 'object' || !check.path) {
      results.push({
        name: 'workspaceCheck',
        ok: false,
        detail: 'invalid check: path is required',
      });
      continue;
    }
    const target = path.resolve(workspaceDir, String(check.path));
    const present = await exists(target);
    if (!present) {
      results.push({
        name: 'workspaceCheck:' + check.path,
        ok: false,
        detail: target + ' (missing)',
      });
      continue;
    }

    if (check.contains != null) {
      try {
        const text = await readFile(target, 'utf8');
        const needles = Array.isArray(check.contains) ? check.contains : [check.contains];
        const missing = needles
          .map((x) => String(x))
          .filter((needle) => !text.includes(needle));
        results.push({
          name: 'workspaceCheck:' + check.path,
          ok: missing.length === 0,
          detail: missing.length === 0
            ? target + ' (required markers present)'
            : target + ' (missing markers: ' + missing.join(', ') + ')',
        });
      } catch (error) {
        results.push({
          name: 'workspaceCheck:' + check.path,
          ok: false,
          detail: target + ' (read failed: ' + error.message + ')',
        });
      }
    } else {
      results.push({
        name: 'workspaceCheck:' + check.path,
        ok: true,
        detail: target,
      });
    }
  }
  return results;
}

export async function doctor(config, repoRoot) {
  const validation = validateConfig(config, repoRoot);
  if (!validation.ok) return validation;
  const c = validation.config;
  const checks = [];

  checks.push({
    name: 'workspaceDir',
    ok: await exists(c.workspaceDir),
    detail: c.workspaceDir,
  });

  if (await exists(c.workspaceDir)) {
    checks.push(...await runWorkspaceChecks(c.workspaceChecks, c.workspaceDir));
    if (c.requireGitIdentity) {
      const gitIdentity = await inspectGitWorkspace(c.workspaceDir);
      checks.push({
        name: 'gitIdentity',
        ok: gitIdentity.available === true,
        detail: gitIdentity.available
          ? c.workspaceDir + ' @ ' + gitIdentity.commit
          : (gitIdentity.error || 'git identity unavailable'),
      });
    }
  }

  const commandLower = c.launch.command.toLowerCase();
  const commandLooksLikePath =
    path.isAbsolute(c.launch.command) ||
    c.launch.command.includes('/') ||
    c.launch.command.includes('\\') ||
    commandLower.endsWith('.bat') ||
    commandLower.endsWith('.cmd');

  if (commandLooksLikePath) {
    const commandPath = path.isAbsolute(c.launch.command)
      ? c.launch.command
      : path.resolve(c.workspaceDir, c.launch.command);
    checks.push({
      name: 'launch.command',
      ok: await exists(commandPath),
      detail: commandPath,
    });
  } else {
    checks.push({
      name: 'launch.command',
      ok: true,
      detail: c.launch.command + ' (PATH lookup deferred to spawn)',
    });
  }

  checks.push({ name: 'runtimeRoot', ok: true, detail: c.runtimeRoot });

  if (c.gameDir) {
    checks.push({
      name: 'gameDir',
      ok: await exists(c.gameDir),
      detail: c.gameDir,
    });
    const debugWorldDir = path.join(c.gameDir, 'saves', c.worldName);
    checks.push({
      name: 'debugWorld',
      ok: !c.requireExistingWorld || await exists(debugWorldDir),
      detail: debugWorldDir + (c.requireExistingWorld ? ' (required)' : ' (optional)'),
    });
  }

  const forgeBridgeSourceDir = path.join(
    repoRoot, 'debug-workspace', 'forge-bridge', 'src', 'main', 'java'
  );
  checks.push({
    name: 'forgeBridgeSourceDir',
    ok: await exists(forgeBridgeSourceDir),
    detail: forgeBridgeSourceDir,
  });

  return {
    ok: checks.every((x) => x.ok),
    errors: [],
    config: c,
    checks,
  };
}

function templateVars(ctx) {
  return {
    debugSessionId: ctx.debugSessionId,
    runId: ctx.runId,
    runSnapshotId: ctx.runSnapshotId,
    processEpoch: String(ctx.processEpoch),
    runDir: ctx.runDir,
    runtimeRoot: ctx.runtimeRoot,
    readyFile: ctx.readyFile,
    buildMarkerFile: ctx.buildMarkerFile,
    shutdownRequestFile: ctx.shutdownRequestFile,
    shutdownAckFile: ctx.shutdownAckFile,
    handshakeNonce: ctx.handshakeNonce,
  };
}

export function expandTemplate(value, vars) {
  let out = String(value);
  for (const [key, replacement] of Object.entries(vars)) {
    const token = String.fromCharCode(36) + '{' + key + '}';
    out = out.split(token).join(String(replacement));
  }
  return out;
}
export function validateReadyManifest(manifest, expected) {
  const errors = [];
  if (!manifest || typeof manifest !== 'object') {
    return { ok: false, errors: ['READY manifest must be an object'] };
  }
  const exact = [
    ['protocolVersion', READY_PROTOCOL],
    ['debugSessionId', expected.debugSessionId],
    ['runId', expected.runId],
    ['runSnapshotId', expected.runSnapshotId],
    ['worldName', expected.worldName],
    ['processEpoch', expected.processEpoch],
    ['handshakeNonce', expected.handshakeNonce],
    ['status', 'DEBUG_READY'],
  ];
  for (const pair of exact) {
    const field = pair[0];
    const value = pair[1];
    if (manifest[field] !== value) errors.push(field + ' mismatch');
  }
  const gates = manifest.gates;
  for (const gate of ['probeHandshake', 'debugWorldReady', 'runtimeAttested']) {
    if (!gates || gates[gate] !== true) errors.push('gate ' + gate + ' is not true');
  }
  if (!Number.isInteger(manifest.pid) || manifest.pid <= 0) {
    errors.push('pid must be a positive integer');
  }

  if (!manifest.runtime || typeof manifest.runtime !== 'object') {
    errors.push('runtime attestation object is required');
  } else if (!manifest.runtime.processCommandHint ||
             typeof manifest.runtime.processCommandHint !== 'string') {
    errors.push('runtime.processCommandHint is required');
  }

  const milestones = manifest.milestones;
  const milestoneFields = [
    'jvmStartedAt',
    'forgeInitializedAt',
    'clientWorldAvailableAt',
    'playerJoinedAt',
    'probeReadyAt',
    'debugWorldReadyAt',
  ];
  const parsedMilestones = [];
  if (!milestones || typeof milestones !== 'object') {
    errors.push('milestones object is required');
  } else {
    for (const field of milestoneFields) {
      const value = milestones[field];
      const parsed = typeof value === 'string' ? Date.parse(value) : NaN;
      if (!Number.isFinite(parsed)) {
        errors.push('milestone ' + field + ' missing or invalid');
      }
      parsedMilestones.push([field, parsed]);
    }
    for (let i = 1; i < parsedMilestones.length; i++) {
      const previous = parsedMilestones[i - 1];
      const current = parsedMilestones[i];
      if (Number.isFinite(previous[1]) &&
          Number.isFinite(current[1]) &&
          current[1] < previous[1]) {
        errors.push(
          'milestone order invalid: ' + current[0] + ' precedes ' + previous[0]
        );
      }
    }
  }

  return { ok: errors.length === 0, errors };
}


export function validateBuildMarker(marker, expected) {
  const errors = [];
  if (!marker || typeof marker !== 'object') {
    return { ok: false, errors: ['build marker must be an object'] };
  }
  for (const field of ['debugSessionId', 'runId', 'handshakeNonce']) {
    if (marker[field] !== expected[field]) errors.push(field + ' mismatch');
  }
  if (!marker.builtAt || !Number.isFinite(Date.parse(marker.builtAt))) {
    errors.push('builtAt missing or invalid');
  }
  return { ok: errors.length === 0, errors };
}

async function readBuildMarker(file, expected) {
  if (!(await exists(file))) {
    throw new Error('build-complete marker missing: ' + file);
  }
  const marker = JSON.parse(await readFile(file, 'utf8'));
  const validation = validateBuildMarker(marker, expected);
  if (!validation.ok) {
    throw new Error('build marker rejected: ' + validation.errors.join(', '));
  }
  return marker;
}

async function readReadyWhenAvailable(file, expected, timeoutMs, childState) {
  const deadline = Date.now() + timeoutMs;
  let lastParseError = null;

  while (Date.now() < deadline) {
    if (childState.error) {
      throw new Error('debug target spawn failed: ' + childState.error.message);
    }
    if (childState.exited) {
      throw new Error(
        'debug target exited before READY (exit=' + childState.code +
        ', signal=' + childState.signal + ')'
      );
    }

    if (await exists(file)) {
      try {
        const manifest = JSON.parse(await readFile(file, 'utf8'));
        const validation = validateReadyManifest(manifest, expected);
        if (!validation.ok) {
          throw new Error('READY manifest rejected: ' + validation.errors.join(', '));
        }
        return manifest;
      } catch (error) {
        lastParseError = error;
      }
    }

    await new Promise((resolve) => setTimeout(resolve, 100));
  }

  if (lastParseError) {
    throw new Error('READY timeout; last READY error: ' + lastParseError.message);
  }
  throw new Error('READY timeout after ' + timeoutMs + 'ms');
}


export async function inspectGitWorkspace(workspaceDir) {
  const head = await collectProcess('git', ['-C', workspaceDir, 'rev-parse', 'HEAD']);
  if (!head.ok || !head.stdout) {
    return {
      available: false,
      error: head.error || head.stderr || 'git rev-parse failed',
    };
  }

  const [branch, status, diff, untracked] = await Promise.all([
    collectProcess('git', ['-C', workspaceDir, 'rev-parse', '--abbrev-ref', 'HEAD']),
    collectProcess(
      'git',
      ['-C', workspaceDir, 'status', '--porcelain=v1', '--untracked-files=all', '--', '.']
    ),
    collectProcess(
      'git',
      ['-C', workspaceDir, 'diff', '--binary', 'HEAD', '--', '.']
    ),
    collectProcess(
      'git',
      ['-C', workspaceDir, 'ls-files', '--others', '--exclude-standard', '--', '.']
    ),
  ]);

  if (!status.ok || !diff.ok || !untracked.ok) {
    return {
      available: false,
      commit: head.stdout.trim(),
      error:
        status.error || status.stderr ||
        diff.error || diff.stderr ||
        untracked.error || untracked.stderr ||
        'git workspace inspection failed',
    };
  }

  const porcelain = status.stdout || '';
  const untrackedPaths = (untracked.stdout || '')
    .split(/\r?\n/)
    .map((x) => x.trim())
    .filter(Boolean)
    .sort();

  const MAX_UNTRACKED_FILES = 256;
  const MAX_UNTRACKED_BYTES = 64 * 1024 * 1024;
  let hashedBytes = 0;
  let untrackedContentComplete = true;
  const untrackedEntries = [];

  for (let i = 0; i < untrackedPaths.length; i++) {
    const relative = untrackedPaths[i];
    if (i >= MAX_UNTRACKED_FILES) {
      untrackedContentComplete = false;
      untrackedEntries.push({
        path: relative,
        status: 'SKIPPED_FILE_LIMIT',
      });
      continue;
    }

    const full = path.resolve(workspaceDir, relative);
    const relCheck = path.relative(workspaceDir, full);
    if (relCheck.startsWith('..') || path.isAbsolute(relCheck)) {
      untrackedContentComplete = false;
      untrackedEntries.push({
        path: relative,
        status: 'OUTSIDE_WORKSPACE',
      });
      continue;
    }

    try {
      const s = await lstat(full);
      if (!s.isFile()) {
        untrackedContentComplete = false;
        untrackedEntries.push({
          path: relative,
          status: s.isSymbolicLink() ? 'SYMLINK_NOT_HASHED' : 'NON_REGULAR',
          size: s.size,
        });
        continue;
      }

      if (hashedBytes + s.size > MAX_UNTRACKED_BYTES) {
        untrackedContentComplete = false;
        untrackedEntries.push({
          path: relative,
          status: 'SKIPPED_BYTE_LIMIT',
          size: s.size,
        });
        continue;
      }

      const bytes = await readFile(full);
      hashedBytes += bytes.length;
      untrackedEntries.push({
        path: relative,
        status: 'HASHED',
        size: bytes.length,
        sha256: createHash('sha256').update(bytes).digest('hex'),
      });
    } catch (error) {
      untrackedContentComplete = false;
      untrackedEntries.push({
        path: relative,
        status: 'READ_FAILED',
        error: error.message,
      });
    }
  }

  const trackedDiffSha256 = createHash('sha256')
    .update(diff.stdout || '', 'utf8')
    .digest('hex');
  const statusSha256 = createHash('sha256')
    .update(porcelain, 'utf8')
    .digest('hex');

  const fingerprintPayload = JSON.stringify({
    commit: head.stdout.trim(),
    branch: branch.ok ? branch.stdout.trim() : null,
    statusSha256,
    trackedDiffSha256,
    untrackedEntries,
    untrackedContentComplete,
  });
  const fingerprintSha256 = createHash('sha256')
    .update(fingerprintPayload, 'utf8')
    .digest('hex');

  return {
    available: true,
    commit: head.stdout.trim(),
    branch: branch.ok ? branch.stdout.trim() : null,
    dirty: porcelain.trim().length > 0,
    statusSha256,
    trackedDiffSha256,
    fingerprintSha256,
    changedEntryCount: porcelain
      ? porcelain.split(/\r?\n/).filter(Boolean).length
      : 0,
    untrackedFileCount: untrackedPaths.length,
    untrackedHashedBytes: hashedBytes,
    untrackedContentComplete,
    untrackedEntries,
  };
}

function gitIdentityStable(before, after) {
  if (!before?.available || !after?.available) {
    return null;
  }
  return before.fingerprintSha256 === after.fingerprintSha256;
}

export function buildRunSnapshot(snapshot, bridgeContext = null) {
  const result = structuredClone(snapshot);
  if (!bridgeContext) return result;
  if (Object.hasOwn(result, 'techHub') || Object.hasOwn(result, 'bridge')) {
    throw new Error('SNAPSHOT_BRIDGE_ALREADY_BOUND');
  }
  result.techHub = validateTechHubBinding(bridgeContext.binding);
  hashId(bridgeContext.registrationHash);
  result.bridge = {
    schemaVersion: 1,
    registrationHash: bridgeContext.registrationHash,
    materialInventory: structuredClone(bridgeContext.materialInventory),
    materialScope: 'DISK_FILES_ONLY',
    runtimeAttestation: 'NOT_ESTABLISHED',
    execution: 'BLOCKED',
    arena: 'BLOCKED',
    capture: 'BLOCKED',
  };
  if (bridgeContext.ownerControlIntent != null) {
    const intent = bridgeContext.ownerControlIntent;
    exactKeys(intent, ['envelopeHash', 'scope', 'fullTargetAttestation'], 'OWNER_CONTROL_INTENT');
    hashId(intent.envelopeHash);
    if (intent.scope !== 'BOUNDED_DIAGNOSTIC_CONTROL' || intent.fullTargetAttestation !== 'NOT_ESTABLISHED')
      throw new Error('INVALID_OWNER_CONTROL_INTENT');
    result.bridge.ownerControlIntent = structuredClone(intent);
  }
  return result;
}

export async function prepareBridgeContext(runtimeRoot, sourceGit, requestHash) {
  if (requestHash == null) return null;
  const bridge = await loadBridgeRegistration({ runtimeRoot, requestHash });
  if (!sourceGit?.available || sourceGit.commit !== bridge.binding.target.source_revision) {
    throw new Error('BRIDGE_SOURCE_REVISION_MISMATCH');
  }
  if (sourceGit.dirty !== false) throw new Error('BRIDGE_DIRTY_SOURCE_UNSUPPORTED');
  return bridge;
}

export async function writeImmutableRunSnapshot(file, snapshot) {
  if (Object.hasOwn(snapshot, 'snapshotHash') || path.basename(file) !== 'run-snapshot.json')
    throw new Error('INVALID_INITIAL_RUN_SNAPSHOT');
  const canonicalBody = canonicalRunSnapshotBytes(snapshot);
  const payload = { ...snapshot, snapshotHash: 'sha256:' + createHash('sha256').update(canonicalBody).digest('hex') };
  const raw = Buffer.from(JSON.stringify(payload, null, 2) + '\n', 'utf8');
  if (canonicalBody.length > 2 * 1024 * 1024 || raw.length > 2 * 1024 * 1024)
    throw new Error('INITIAL_SNAPSHOT_SIZE_LIMIT');
  const sidecar = path.join(path.dirname(file), 'run-snapshot.canonical.json');
  await mkdir(path.dirname(file), { recursive: true });
  for (const candidate of [file, sidecar]) {
    try { await lstat(candidate); throw new Error('run snapshot already exists and is immutable: ' + candidate); }
    catch (error) { if (error.code !== 'ENOENT') throw error; }
  }
  const sidecarHandle = await open(sidecar, 'wx', 0o600);
  try { await sidecarHandle.writeFile(canonicalBody); await sidecarHandle.sync(); } finally { await sidecarHandle.close(); }
  const temporaryFile = path.join(path.dirname(file), '.run-snapshot-' + randomBytes(8).toString('hex') + '.pending');
  const handle = await open(temporaryFile, 'wx', 0o600);
  try {
    await handle.writeFile(raw); await handle.sync(); await handle.close();
    await link(temporaryFile, file); // Atomic no-replace commit: readers never see a partial marker.
  } finally {
    await handle.close().catch(() => {});
    await unlink(temporaryFile).catch(error => { if (error.code !== 'ENOENT') throw error; });
  }
  return payload;
}

export function assessProcessOwnership(current, observed, toleranceMs = 120000) {
  if (!current || !Number.isInteger(current.pid) || current.pid <= 0) {
    return { owned: false, reason: 'missing-recorded-pid' };
  }
  if (!observed || observed.exists !== true) {
    return { owned: false, reason: 'process-not-running' };
  }
  if (observed.pid !== current.pid) {
    return { owned: false, reason: 'pid-mismatch' };
  }
  if (!Number.isFinite(current.spawnedAtEpochMs) ||
      !Number.isFinite(observed.startedAtEpochMs)) {
    return { owned: false, reason: 'missing-start-time-evidence' };
  }

  const deltaMs = Math.abs(observed.startedAtEpochMs - current.spawnedAtEpochMs);
  if (deltaMs > toleranceMs) {
    return {
      owned: false,
      reason: 'start-time-mismatch',
      deltaMs,
    };
  }

  const expectedBase = current.launchCommand
    ? path.basename(String(current.launchCommand)).toLowerCase()
    : '';
  const commandLine = String(observed.commandLine || '').toLowerCase();
  if (!expectedBase || !commandLine.includes(expectedBase)) {
    return {
      owned: false,
      reason: 'launch-command-mismatch',
      expectedBase,
      commandLine: observed.commandLine || '',
      deltaMs,
    };
  }

  return {
    owned: true,
    reason: 'pid-start-time-and-command-match',
    deltaMs,
    expectedBase,
  };
}

export async function inspectProcess(pid) {
  if (!Number.isInteger(pid) || pid <= 0) {
    return { exists: false, pid };
  }

  if (process.platform === 'win32') {
    const script = [
      "$p = Get-CimInstance Win32_Process -Filter \"ProcessId = " + pid + "\" -ErrorAction SilentlyContinue",
      "if ($null -eq $p) {",
      "  [pscustomobject]@{ exists = $false; pid = " + pid + " } | ConvertTo-Json -Compress",
      "} else {",
      "  [pscustomobject]@{",
      "    exists = $true",
      "    pid = [int]$p.ProcessId",
      "    commandLine = [string]$p.CommandLine",
      "    startedAt = $p.CreationDate.ToUniversalTime().ToString('o')",
      "  } | ConvertTo-Json -Compress",
      "}",
    ].join('\n');
    const result = await collectProcess(
      'powershell',
      ['-NoProfile', '-NonInteractive', '-Command', script]
    );
    if (!result.ok || !result.stdout) {
      return {
        exists: false,
        pid,
        inspectionError: result.error || result.stderr || 'powershell inspection failed',
      };
    }
    try {
      const parsed = JSON.parse(result.stdout);
      return {
        exists: parsed.exists === true,
        pid: Number(parsed.pid),
        commandLine: parsed.commandLine || '',
        startedAtEpochMs: parsed.startedAt ? Date.parse(parsed.startedAt) : NaN,
      };
    } catch (error) {
      return {
        exists: false,
        pid,
        inspectionError: 'invalid powershell process JSON: ' + error.message,
      };
    }
  }

  if (process.platform === 'linux') {
    const result = await collectProcess(
      'ps',
      ['-p', String(pid), '-o', 'etimes=', '-o', 'command=']
    );
    if (!result.ok || !result.stdout) {
      const absent = result.code === 1 && !result.stdout && !result.stderr && !result.error;
      return { exists: false, pid, ...(!absent ? { inspectionError: result.error || result.stderr || 'process inspection failed' } : {}) };
    }
    const line = result.stdout.trim();
    const match = line.match(/^(\d+)\s+(.*)$/s);
    if (!match) {
      return {
        exists: false,
        pid,
        inspectionError: 'unexpected ps output',
      };
    }
    const elapsedSeconds = Number(match[1]);
    return {
      exists: true,
      pid,
      commandLine: match[2],
      startedAtEpochMs: Date.now() - elapsedSeconds * 1000,
    };
  }

  return {
    exists: false,
    pid,
    inspectionError: 'process ownership inspection unsupported on ' + process.platform,
  };
}

export async function stopProcessTree(pid) {
  if (!Number.isInteger(pid) || pid <= 0) return;

  if (process.platform === 'win32') {
    await new Promise((resolve) => {
      const p = spawn('taskkill', ['/PID', String(pid), '/T', '/F'], {
        stdio: 'ignore',
        windowsHide: true,
      });
      p.on('error', () => resolve());
      p.on('exit', () => resolve());
    });
    return;
  }

  try {
    process.kill(-pid, 'SIGTERM');
  } catch {
    try {
      process.kill(pid, 'SIGTERM');
    } catch {
      // already gone
    }
  }
}


function completeProcessIdentity(record) {
  return Number.isInteger(record?.pid) && record.pid > 0 &&
    Number.isFinite(record.spawnedAtEpochMs) && typeof record.launchCommand === 'string' &&
    record.launchCommand.length > 0;
}

async function inspectRecordedProcesses(current, inspect = inspectProcess) {
  const launcherObserved = Number.isInteger(current?.pid)
    ? await inspect(current.pid)
    : { exists: false, pid: current?.pid ?? null };
  const launcherOwnership = Number.isInteger(current?.pid)
    ? assessProcessOwnership(current, launcherObserved)
    : { owned: false, reason: 'missing-recorded-pid' };

  const runtimeRecord = Number.isInteger(current?.runtimePid)
    ? {
        pid: current.runtimePid,
        spawnedAtEpochMs: current.runtimeStartedAtEpochMs,
        launchCommand: current.runtimeCommandHint,
      }
    : null;
  const runtimeObserved = runtimeRecord
    ? await inspect(runtimeRecord.pid)
    : { exists: false, pid: current?.runtimePid ?? null };
  const runtimeOwnership = runtimeRecord
    ? assessProcessOwnership(runtimeRecord, runtimeObserved, 10000)
    : { owned: false, reason: 'missing-runtime-pid' };

  return {
    launcher: {
      observed: launcherObserved,
      ownership: launcherOwnership,
    },
    runtime: {
      observed: runtimeObserved,
      ownership: runtimeOwnership,
    },
    inspectionUnknown: Boolean(launcherObserved.inspectionError || runtimeObserved.inspectionError),
    identityIncomplete: !completeProcessIdentity(current) ||
      ((current.status !== 'STARTING' && current.status !== 'FAILED') && !completeProcessIdentity(runtimeRecord)),
    anyOwned: launcherOwnership.owned || runtimeOwnership.owned,
    anyObserved: launcherObserved.exists === true || runtimeObserved.exists === true,
    anyObservedUnowned:
      (launcherObserved.exists === true && !launcherOwnership.owned) ||
      (runtimeObserved.exists === true && !runtimeOwnership.owned),
  };
}

async function reconcileCurrent(c, inspect = inspectProcess) {
  const file = path.join(c.runtimeRoot, 'current.json');
  if (!(await exists(file))) {
    return {
      file,
      current: null,
      processes: null,
      status: 'NOT_STARTED',
      live: false,
    };
  }

  const current = JSON.parse(await readFile(file, 'utf8'));
  const processes = await inspectRecordedProcesses(current, inspect);
  const wasActive = current.status === 'STARTING' || current.status === 'DEBUG_READY';

  if (wasActive && (!processes.anyOwned || processes.inspectionUnknown || processes.identityIncomplete)) {
    current.status = (processes.inspectionUnknown || processes.identityIncomplete) ? 'OWNERSHIP_UNKNOWN' : processes.anyObservedUnowned
      ? 'OWNERSHIP_LOST'
      : 'STALE_NOT_RUNNING';
    current.reconciledAt = nowIso();
    current.updatedAt = nowIso();
    current.processes = processes;
    await writeJsonAtomic(file, current);
  }

  return {
    file,
    current,
    processes,
    status: current.status,
    live: (processes.inspectionUnknown || processes.identityIncomplete) ? null : processes.anyOwned,
  };
}

export function assertCurrentAllowsLaunch(state) {
  const quarantined = ['OWNERSHIP_LOST', 'OWNERSHIP_UNKNOWN', 'STOP_INSPECTION_UNKNOWN',
    'STOP_REFUSED_UNVERIFIED', 'STOP_INCOMPLETE'].includes(state.current?.status);
  if (state.processes?.anyObservedUnowned || state.processes?.identityIncomplete || quarantined) {
    throw new Error('debug runtime identity unverified; explicit reconciliation required');
  }
  if (state.live !== false) {
    throw new Error('debug runtime already active or unverified');
  }
}

async function fenceActiveCurrent(c) {
  const state = await reconcileCurrent(c);
  assertCurrentAllowsLaunch(state);
  return state;
}

export async function launchDebugRun(config, repoRoot, options = {}) {
  const d = await doctor(config, repoRoot);
  if (!d.ok) {
    const detail = d.errors && d.errors.length
      ? d.errors.join('; ')
      : d.checks.filter((x) => !x.ok)
          .map((x) => x.name + ': ' + x.detail)
          .join('; ');
    throw new Error('debug workspace doctor failed: ' + detail);
  }
  const c = d.config;
  await fenceActiveCurrent(c);

  const sourceGit = await inspectGitWorkspace(c.workspaceDir);
  const labGit = await inspectGitWorkspace(repoRoot);
  const ownerSelection = ownerLaunchSelection(c, options);
  const bridgeContext = await prepareBridgeContext(c.runtimeRoot, sourceGit, ownerSelection.requestHash);
  if (ownerSelection.operatorRegistration != null && (!bridgeContext || c.worldName !== 'KNEEKURA_DEBUG_WORLD'))
    throw new Error('OWNER_REGISTERED_DISPOSABLE_BRIDGE_REQUIRED');

  const debugSessionId = options.debugSessionId || createIdentity('sess');
  const runId = options.runId || createIdentity('run');
  const processEpoch = Number.isInteger(options.processEpoch) ? options.processEpoch : 1;
  const handshakeNonce = randomBytes(16).toString('hex');
  const runSnapshotId = createIdentity('snapshot');

  const sessionDir = path.join(c.runtimeRoot, 'sessions', safeIdPart(debugSessionId));
  const runDir = path.join(sessionDir, 'runs', safeIdPart(runId));
  const readyFile = path.join(runDir, 'ready.json');
  const buildMarkerFile = path.join(runDir, 'build-complete.json');
  const evidenceRawDir = path.join(runDir, 'evidence', 'raw');
  const targetFile = path.join(runDir, 'control', 'target.json');
  const shutdownRequestFile = path.join(
    runDir,
    'control',
    'shutdown-request.json'
  );
  const shutdownAckFile = path.join(
    runDir,
    'control',
    'shutdown-ack.json'
  );
  const timelineFile = path.join(runDir, 'timeline.jsonl');
  const logFile = path.join(runDir, 'process.log');
  const runFile = path.join(runDir, 'run.json');
  const runSnapshotFile = path.join(runDir, 'run-snapshot.json');
  const currentFile = path.join(c.runtimeRoot, 'current.json');

  await mkdir(runDir, { recursive: true });

  const sessionFile = path.join(sessionDir, 'session.json');
  if (!(await exists(sessionFile))) {
    await writeJsonAtomic(sessionFile, {
      schemaVersion: 1,
      debugSessionId,
      workspaceId: c.workspaceId,
      createdAt: nowIso(),
      initialSourceGit: sourceGit,
      initialLabGit: labGit,
    });
  }

  const ctx = {
    debugSessionId,
    runId,
    processEpoch,
    runSnapshotId,
    handshakeNonce,
    runDir,
    readyFile,
    buildMarkerFile,
    evidenceRawDir,
    targetFile,
    shutdownRequestFile,
    shutdownAckFile,
    runtimeRoot: c.runtimeRoot,
  };
  const preparedOwner = ownerSelection.operatorRegistration == null ? null : await prepareOwnerControl({
    runtimeRoot: c.runtimeRoot, runDir,
    identity: { debugSessionId, runId, runSnapshotId, processEpoch, handshakeNonce },
    operatorRegistration: ownerSelection.operatorRegistration, bridgeContext,
  });
  const vars = templateVars(ctx);

  const decisionHooks=decisionHookLaunchOptions(c,repoRoot);
  const launchArgs = c.launch.args.map((x) => expandTemplate(x, vars)).concat(decisionHooks.extraArgs);
  const forgeBridgeSourceDir = path.join(
    repoRoot, 'debug-workspace', 'forge-bridge', 'src', 'main', 'java'
  );
  const launchEnv = ownerLaunchEnvironment({
    ...process.env,
    ...Object.fromEntries(
      Object.entries(c.launch.env).map(([k, v]) => [k, expandTemplate(v, vars)])
    ),
    KNEEKURA_DEBUG_ENABLED: '1',
    KNEEKURA_DEBUG_SESSION_ID: debugSessionId,
    KNEEKURA_DEBUG_RUN_ID: runId,
    KNEEKURA_DEBUG_PROCESS_EPOCH: String(processEpoch),
    KNEEKURA_DEBUG_RUN_SNAPSHOT_ID: runSnapshotId,
    KNEEKURA_DEBUG_HANDSHAKE_NONCE: handshakeNonce,
    KNEEKURA_DEBUG_READY_FILE: readyFile,
    KNEEKURA_DEBUG_BUILD_MARKER: buildMarkerFile,
    KNEEKURA_DEBUG_EVIDENCE_RAW_DIR: evidenceRawDir,
    KNEEKURA_DEBUG_TARGET_FILE: targetFile,
    KNEEKURA_DEBUG_SHUTDOWN_REQUEST_FILE: shutdownRequestFile,
    KNEEKURA_DEBUG_SHUTDOWN_ACK_FILE: shutdownAckFile,
    KNEEKURA_DEBUG_RUN_DIR: runDir,
    KNEEKURA_DEBUG_RUNTIME_ROOT: c.runtimeRoot,
    KNEEKURA_DEBUG_FORGE_BRIDGE_SRC: forgeBridgeSourceDir,
    KNEEKURA_DEBUG_WORLD_NAME: c.worldName,
    ...decisionHooks.env,
    ...motionOverlayLaunchEnvironment(c),
  }, preparedOwner);

  const runRecord = {
    schemaVersion: 1,
    workspaceId: c.workspaceId,
    debugSessionId,
    runId,
    processEpoch,
    runSnapshotId,
    status: 'STARTING',
    ...(preparedOwner ? { ownerControlIntent: preparedOwner.ownerControlIntent } : {}),
    createdAt: nowIso(),
    workspaceDir: c.workspaceDir,
    sourceGit,
    labGit,
    worldName: c.worldName,
    forgeBridgeSourceDir,
    decisionHooksEnabled:c.decisionHooks,
    motionOverlayEnabled:c.motionOverlay,
    launch: {
      command: c.launch.command,
      args: launchArgs,
      shell: c.launch.shell,
    },
    paths: {
      runDir,
      readyFile,
      buildMarkerFile,
      evidenceRawDir,
      targetFile,
      shutdownRequestFile,
      shutdownAckFile,
      runSnapshotFile,
      timelineFile,
      logFile
    },
  };

  await writeJsonAtomic(runFile, runRecord);
  await appendTimeline(timelineFile, 'T0_RESTART_REQUESTED', {
    debugSessionId,
    runId,
    processEpoch,
  });

  const logFd = openSync(logFile, 'a');
  let child;
  try {
    child = spawn(c.launch.command, launchArgs, {
      cwd: c.workspaceDir,
      env: launchEnv,
      shell: c.launch.shell,
      detached: true,
      windowsHide: true,
      stdio: ['ignore', logFd, logFd],
    });
  } finally {
    closeSync(logFd);
  }

  const childState = { exited: false, code: null, signal: null, error: null };
  child.once('error', (error) => {
    childState.error = error;
  });
  child.once('exit', (code, signal) => {
    childState.exited = true;
    childState.code = code;
    childState.signal = signal;
  });

  const spawnedAtEpochMs = Date.now();
  await appendTimeline(timelineFile, 'LAUNCHER_PROCESS_STARTED', {
    pid: child.pid,
    spawnedAtEpochMs,
  });

  runRecord.pid = child.pid;
  runRecord.spawnedAtEpochMs = spawnedAtEpochMs;
  await writeJsonAtomic(runFile, runRecord);
  await writeJsonAtomic(currentFile, {
    schemaVersion: 1,
    workspaceId: c.workspaceId,
    debugSessionId,
    runId,
    processEpoch,
    runSnapshotId,
    status: 'STARTING',
    pid: child.pid,
    spawnedAtEpochMs,
    launchCommand: c.launch.command,
    runDir,
    shutdownRequestFile,
    shutdownAckFile,
    updatedAt: nowIso(),
  });

  try {
    const ready = await readReadyWhenAvailable(
      readyFile,
      {
        debugSessionId,
        runId,
        runSnapshotId,
        worldName: c.worldName,
        processEpoch,
        handshakeNonce
      },
      c.readyTimeoutMs,
      childState
    );

    const buildMarker = await readBuildMarker(
      buildMarkerFile,
      { debugSessionId, runId, handshakeNonce }
    );
    await appendTimeline(timelineFile, 'T1_BUILD_COMPLETE', {
      source: 'gradle-marker',
      reportedAt: buildMarker.builtAt,
    });

    const probeMilestones = ready.milestones || {};
    const runtimeStartedAtEpochMs = Date.parse(probeMilestones.jvmStartedAt);
    const runtimeCommandHint = ready.runtime.processCommandHint;
    const runtimeObserved = await inspectProcess(ready.pid);
    const runtimeOwnership = assessProcessOwnership({
      pid: ready.pid,
      spawnedAtEpochMs: runtimeStartedAtEpochMs,
      launchCommand: runtimeCommandHint,
    }, runtimeObserved, 10000);

    if (!runtimeOwnership.owned) {
      throw new Error(
        'runtime PID attestation failed: ' + JSON.stringify({
          ownership: runtimeOwnership,
          observed: runtimeObserved,
        })
      );
    }

    const sourceGitReady = await inspectGitWorkspace(c.workspaceDir);
    const labGitReady = await inspectGitWorkspace(repoRoot);
    const sourceStable = gitIdentityStable(sourceGit, sourceGitReady);
    const labStable = gitIdentityStable(labGit, labGitReady);

    if (c.requireGitIdentity &&
        (!sourceGit.available || !sourceGitReady.available)) {
      throw new Error('required source Git identity unavailable during startup');
    }
    if (sourceStable === false) {
      throw new Error('SOURCE_CHANGED_DURING_START');
    }
    if (labStable === false) {
      throw new Error('OBSERVER_CHANGED_DURING_START');
    }

    const bridgeReady = await prepareBridgeContext(c.runtimeRoot, sourceGitReady, ownerSelection.requestHash);
    if (bridgeContext && bridgeReady.registrationHash !== bridgeContext.registrationHash) {
      throw new Error('BRIDGE_REGISTRATION_CHANGED_DURING_START');
    }
    if (preparedOwner) {
      await readPreparedOwnerControl({ runDir, envelopeHash: preparedOwner.envelopeHash });
      bridgeReady.ownerControlIntent = preparedOwner.ownerControlIntent;
    }
    const runSnapshot = await writeImmutableRunSnapshot(
      runSnapshotFile,
      buildRunSnapshot({
        schemaVersion: 1,
        snapshotId: runSnapshotId,
        createdAt: nowIso(),
        debugProfile: c.debugProfile,
        workspaceId: c.workspaceId,
        debugSessionId,
        runId,
        processEpoch,
        worldName: c.worldName,
        source: {
          before: sourceGit,
          ready: sourceGitReady,
          stableDuringStartup: sourceStable,
        },
        observer: {
          before: labGit,
          ready: labGitReady,
          stableDuringStartup: labStable,
          forgeBridgeSourceDir,
          observationSchemaVersion: 1,
        },
        build: buildMarker,
        runtime: {
          pid: ready.pid,
          startedAtEpochMs: runtimeStartedAtEpochMs,
          ownership: runtimeOwnership,
          attestation: ready.runtime,
        },
      }, bridgeReady)
    );

    if (preparedOwner) await readPreparedOwnerControl({ runDir, envelopeHash: preparedOwner.envelopeHash, requireSnapshot: true });

    const milestoneMap = [
      ['jvmStartedAt', 'T2_JVM_STARTED'],
      ['forgeInitializedAt', 'T3_FORGE_INITIALIZED'],
      ['clientWorldAvailableAt', 'T4_CLIENT_WORLD_AVAILABLE'],
      ['playerJoinedAt', 'T5_PLAYER_JOINED'],
      ['probeReadyAt', 'T6_PROBE_READY'],
      ['debugWorldReadyAt', 'T7_DEBUG_WORLD_READY'],
    ];
    for (const pair of milestoneMap) {
      const field = pair[0];
      const stage = pair[1];
      if (probeMilestones[field]) {
        await appendTimeline(timelineFile, stage, {
          source: 'probe',
          reportedAt: probeMilestones[field],
        });
      }
    }

    await appendTimeline(timelineFile, 'T8_DEBUG_READY', {
      source: 'ready-manifest',
      runtimePid: ready.pid == null ? null : ready.pid,
    });

    runRecord.status = 'DEBUG_READY';
    runRecord.readyAt = nowIso();
    runRecord.buildMarker = buildMarker;
    runRecord.runSnapshotId = runSnapshotId;
    runRecord.runSnapshotHash = runSnapshot.snapshotHash;
    runRecord.runSnapshotFile = runSnapshotFile;
    runRecord.sourceGitReady = sourceGitReady;
    runRecord.labGitReady = labGitReady;
    runRecord.runtimePid = ready.pid;
    runRecord.runtimeStartedAtEpochMs = runtimeStartedAtEpochMs;
    runRecord.runtimeCommandHint = runtimeCommandHint;
    runRecord.runtimeOwnership = runtimeOwnership;
    runRecord.runtimeAttestation = ready.runtime;
    runRecord.readyManifest = ready;
    await writeJsonAtomic(runFile, runRecord);

    await writeJsonAtomic(currentFile, {
      schemaVersion: 1,
      workspaceId: c.workspaceId,
      debugSessionId,
      runId,
      processEpoch,
      runSnapshotId,
      runSnapshotHash: runSnapshot.snapshotHash,
      runSnapshotFile,
      ...(preparedOwner ? { ownerControlIntent: preparedOwner.ownerControlIntent } : {}),
      status: 'DEBUG_READY',
      decisionHooksEnabled: c.decisionHooks,
      motionOverlayEnabled: c.motionOverlay,
      pid: child.pid,
      runtimePid: ready.pid,
      runtimeStartedAtEpochMs,
      runtimeCommandHint,
      runtimeOwnership,
      spawnedAtEpochMs,
      launchCommand: c.launch.command,
      runDir,
      shutdownRequestFile,
      shutdownAckFile,
      updatedAt: nowIso(),
    });

    child.unref();

    return {
      ok: true,
      status: 'DEBUG_READY',
      decisionHooksEnabled: c.decisionHooks,
      motionOverlayEnabled: c.motionOverlay,
      debugSessionId,
      runId,
      processEpoch,
      runSnapshotId,
      runSnapshotHash: runSnapshot.snapshotHash,
      runSnapshotFile,
      ...(preparedOwner ? { ownerControlIntent: preparedOwner.ownerControlIntent } : {}),
      pid: child.pid,
      runtimePid: ready.pid == null ? null : ready.pid,
      runDir,
      sourceGit,
      labGit,
      ready,
    };
  } catch (error) {
    await appendTimeline(timelineFile, 'DEBUG_START_FAILED', {
      error: error.message,
      childExited: childState.exited,
      exitCode: childState.code,
      signal: childState.signal,
    });

    runRecord.status = 'FAILED';
    runRecord.failedAt = nowIso();
    runRecord.error = error.message;
    await writeJsonAtomic(runFile, runRecord);

    await writeJsonAtomic(currentFile, {
      schemaVersion: 1,
      workspaceId: c.workspaceId,
      debugSessionId,
      runId,
      processEpoch,
      runSnapshotId,
      status: 'FAILED',
      pid: child.pid,
      spawnedAtEpochMs,
      launchCommand: c.launch.command,
      runDir,
      shutdownRequestFile,
      shutdownAckFile,
      error: error.message,
      updatedAt: nowIso(),
    });

    await stopProcessTree(child.pid);
    throw error;
  }
}

export async function readCurrent(config, repoRoot) {
  const validation = validateConfig(config, repoRoot);
  if (!validation.ok) throw new Error(validation.errors.join('; '));
  const state = await reconcileCurrent(validation.config);
  if (!state.current) {
    return {
      status: 'NOT_STARTED',
      live: false,
      runtimeRoot: validation.config.runtimeRoot,
    };
  }
  return {
    ...state.current,
    live: state.live,
    processes: state.processes,
  };
}



export async function writeG1Acceptance(config, repoRoot, evidence) {
  const validation = validateConfig(config, repoRoot);
  if (!validation.ok) throw new Error(validation.errors.join('; '));

  if (!evidence || !evidence.started || !evidence.timeline || !evidence.status || !evidence.stopped) {
    throw new Error('G1 acceptance evidence is incomplete');
  }

  const safeStopPassed = evidence.stopped.ok === true &&
    evidence.stopped.cleanup?.status === 'VERIFIED_EXIT';
  const passed =
    evidence.started.status === 'DEBUG_READY' &&
    evidence.timeline.complete === true &&
    evidence.status.live === true &&
    safeStopPassed;

  const file = path.join(evidence.started.runDir, 'g1-acceptance.json');
  const manifest = {
    schemaVersion: 1,
    gate: 'G1_DEBUG_LAUNCH',
    result: passed ? 'PASS' : 'FAIL',
    recordedAt: nowIso(),
    debugSessionId: evidence.started.debugSessionId,
    runId: evidence.started.runId,
    processEpoch: evidence.started.processEpoch,
    sourceGit: evidence.started.sourceGit || null,
    labGit: evidence.started.labGit || null,
    runSnapshotId: evidence.started.runSnapshotId || null,
    runSnapshotHash: evidence.started.runSnapshotHash || null,
    runSnapshotFile: evidence.started.runSnapshotFile || null,
    runtimeAttestation: evidence.started.ready?.runtime || null,
    totalStartupMs: evidence.timeline.totalStartupMs,
    timelineComplete: evidence.timeline.complete,
    runtimeWasLiveBeforeStop: evidence.status.live === true,
    safeStopPassed,
    stoppedPids: evidence.stopped.stoppedPids || [],
  };

  await writeJsonAtomic(file, manifest);
  return { file, manifest };
}

export async function readStartupTimeline(config, repoRoot) {
  const validation = validateConfig(config, repoRoot);
  if (!validation.ok) throw new Error(validation.errors.join('; '));

  const state = await reconcileCurrent(validation.config);
  if (!state.current || !state.current.runDir) {
    return {
      ok: false,
      complete: false,
      status: 'NOT_STARTED',
      stages: [],
    };
  }

  const timelineFile = path.join(state.current.runDir, 'timeline.jsonl');
  if (!(await exists(timelineFile))) {
    return {
      ok: false,
      complete: false,
      status: state.current.status,
      runId: state.current.runId,
      timelineFile,
      stages: [],
      error: 'timeline file missing',
    };
  }

  const raw = await readFile(timelineFile, 'utf8');
  const rows = raw.split(/\r?\n/)
    .filter(Boolean)
    .map((line) => JSON.parse(line));

  const order = [
    'T0_RESTART_REQUESTED',
    'T1_BUILD_COMPLETE',
    'T2_JVM_STARTED',
    'T3_FORGE_INITIALIZED',
    'T4_CLIENT_WORLD_AVAILABLE',
    'T5_PLAYER_JOINED',
    'T6_PROBE_READY',
    'T7_DEBUG_WORLD_READY',
    'T8_DEBUG_READY',
  ];

  const latestByStage = new Map();
  for (const row of rows) {
    if (order.includes(row.stage)) latestByStage.set(row.stage, row);
  }

  let t0 = null;
  let previous = null;
  const stages = order.map((stage) => {
    const row = latestByStage.get(stage);
    if (!row) {
      return {
        stage,
        present: false,
        at: null,
        fromPreviousMs: null,
        fromT0Ms: null,
      };
    }

    const timestamp = row.reportedAt || row.at;
    const ms = Date.parse(timestamp);
    if (!Number.isFinite(ms)) {
      return {
        stage,
        present: true,
        at: timestamp,
        fromPreviousMs: null,
        fromT0Ms: null,
        invalidTimestamp: true,
      };
    }

    if (t0 == null) t0 = ms;
    const result = {
      stage,
      present: true,
      at: timestamp,
      fromPreviousMs: previous == null ? 0 : ms - previous,
      fromT0Ms: ms - t0,
    };
    previous = ms;
    return result;
  });

  const complete = stages.every((x) => x.present && !x.invalidTimestamp);
  const finalStage = stages[stages.length - 1];
  const launcher = rows.find((x) => x.stage === 'LAUNCHER_PROCESS_STARTED') || null;

  return {
    ok: complete,
    complete,
    status: state.current.status,
    live: state.live,
    debugSessionId: state.current.debugSessionId,
    runId: state.current.runId,
    timelineFile,
    totalStartupMs: complete ? finalStage.fromT0Ms : null,
    launcherProcessStartedAt: launcher?.at || null,
    stages,
  };
}

async function requestCleanEvidenceShutdown(
  current,
  timeoutMs = 5000
) {
  if (!current?.runDir ||
      !current?.debugSessionId ||
      !current?.runId ||
      !current?.runSnapshotId ||
      !Number.isInteger(current?.processEpoch)) {
    return {
      clean: false,
      status: 'SHUTDOWN_IDENTITY_INCOMPLETE'
    };
  }

  const requestFile =
    current.shutdownRequestFile ||
    path.join(current.runDir, 'control', 'shutdown-request.json');
  const ackFile =
    current.shutdownAckFile ||
    path.join(current.runDir, 'control', 'shutdown-ack.json');

  const request = {
    v: 1,
    debugSessionId: current.debugSessionId,
    runId: current.runId,
    runSnapshotId: current.runSnapshotId,
    processEpoch: current.processEpoch,
    requestedAt: nowIso(),
  };
  await writeJsonAtomic(requestFile, request);

  const deadline = Date.now() + timeoutMs;
  let lastError = null;
  while (Date.now() < deadline) {
    if (await exists(ackFile)) {
      try {
        const ack = JSON.parse(await readFile(ackFile, 'utf8'));
        const identityMatches =
          ack.v === 1 &&
          ack.debugSessionId === current.debugSessionId &&
          ack.runId === current.runId &&
          ack.runSnapshotId === current.runSnapshotId &&
          ack.processEpoch === current.processEpoch;

        if (!identityMatches) {
          throw new Error('shutdown ACK identity mismatch');
        }

        return {
          clean:
            ack.clean === true &&
            ack.status === 'CLEAN_EVIDENCE_SHUTDOWN',
          status: ack.status || 'UNKNOWN_ACK_STATUS',
          requestFile,
          ackFile,
          ack,
        };
      } catch (error) {
        lastError = error;
      }
    }
    await new Promise((resolve) => setTimeout(resolve, 50));
  }

  return {
    clean: false,
    status: 'SHUTDOWN_ACK_TIMEOUT',
    requestFile,
    ackFile,
    error: lastError?.message || null,
    timeoutMs,
  };
}

export async function stopCurrent(config, repoRoot, options = {}) {
  const validation = validateConfig(config, repoRoot);
  if (!validation.ok) throw new Error(validation.errors.join('; '));
  const c = validation.config;

  const processOps = options.processOperations || {};
  const inspect = processOps.inspect || inspectProcess;
  const terminate = processOps.terminate || stopProcessTree;
  const state = await reconcileCurrent(c, inspect);
  if (!state.current) {
    return { ok: true, status: 'NOT_STARTED', live: false };
  }

  const current = state.current;
  const processes = state.processes;

  if (processes.inspectionUnknown || processes.identityIncomplete || processes.anyObservedUnowned) {
    current.status = (processes.inspectionUnknown || processes.identityIncomplete) ? 'STOP_INSPECTION_UNKNOWN' : 'STOP_REFUSED_UNVERIFIED';
    current.cleanup = { status: (processes.inspectionUnknown || processes.identityIncomplete) ? 'INSPECTION_UNKNOWN' : 'OWNERSHIP_CHANGED' };
    current.processes = processes;
    await writeJsonAtomic(state.file, current);
    return { ...current, ok: false, live: (processes.inspectionUnknown || processes.identityIncomplete) ? null : processes.anyOwned };
  }

  if (!processes.anyOwned) {
    if (processes.anyObservedUnowned) {
      current.status = 'STOP_REFUSED_UNVERIFIED';
      current.stopRefusedAt = nowIso();
      current.processes = processes;
      current.updatedAt = nowIso();
      await writeJsonAtomic(state.file, current);
      return {
        ok: false,
        live: false,
        ...current,
      };
    }

    current.cleanup = { status: 'VERIFIED_EXIT', observations: [processes.launcher.observed, processes.runtime.observed] };
    current.status = 'STALE_NOT_RUNNING';
    current.stoppedAt = nowIso();
    current.processes = processes;
    current.updatedAt = nowIso();
    await writeJsonAtomic(state.file, current);
    return {
      ok: true,
      live: false,
      ...current,
    };
  }

  let evidenceShutdown = null;
  if (processes.runtime.ownership.owned) {
    try {
      evidenceShutdown = await requestCleanEvidenceShutdown(current);
    } catch (error) {
      evidenceShutdown = {
        clean: false,
        status: 'SHUTDOWN_REQUEST_FAILED',
        error: error.message,
      };
    }
  } else {
    evidenceShutdown = {
      clean: false,
      status: 'RUNTIME_NOT_OWNED_FOR_FLUSH',
    };
  }

  const stoppedPids = [];
  if (processes.launcher.ownership.owned && Number.isInteger(current.pid)) {
    await terminate(current.pid);
    stoppedPids.push(current.pid);
  }

  if (processes.runtime.ownership.owned &&
      Number.isInteger(current.runtimePid) &&
      !stoppedPids.includes(current.runtimePid)) {
    await terminate(current.runtimePid);
    stoppedPids.push(current.runtimePid);
  }

  const records = [];
  if (processes.launcher.ownership.owned) {
    records.push({
      pid: current.pid, spawnedAtEpochMs: current.spawnedAtEpochMs,
      launchCommand: current.launchCommand,
    });
  }
  if (processes.runtime.ownership.owned && current.runtimePid !== current.pid) {
    records.push({
      pid: current.runtimePid, spawnedAtEpochMs: current.runtimeStartedAtEpochMs,
      launchCommand: current.runtimeCommandHint,
    });
  }
  const cleanup = await verifyProcessesExited(records, {
    inspect, timeoutMs: processOps.timeoutMs ?? 5000, pollMs: processOps.pollMs ?? 50,
  });
  const stopped = cleanup.status === 'VERIFIED_EXIT';
  current.cleanup = cleanup;
  current.status = stopped ? 'STOPPED' : 'STOP_INCOMPLETE';
  current.stoppedAt = nowIso();
  current.stoppedPids = stoppedPids;
  current.evidenceShutdown = evidenceShutdown;
  current.processes = processes;
  current.updatedAt = nowIso();
  await writeJsonAtomic(state.file, current);
  return {
    ...current,
    ok: stopped,
    live: stopped ? false : (cleanup.status === 'EXIT_TIMEOUT' ? true : null),
  };
}
