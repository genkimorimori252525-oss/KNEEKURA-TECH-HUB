import path from 'node:path';

const sleepDefault = milliseconds => new Promise(resolve => setTimeout(resolve, milliseconds));

export async function verifyProcessesExited(records, options = {}) {
  const { inspect, now = Date.now, sleep = sleepDefault, timeoutMs = 5000, pollMs = 50 } = options;
  if (typeof inspect !== 'function' || typeof now !== 'function' || typeof sleep !== 'function' ||
      !Number.isInteger(timeoutMs) || timeoutMs < 1 || timeoutMs > 30000 ||
      !Number.isInteger(pollMs) || pollMs < 1 || pollMs > timeoutMs ||
      !Array.isArray(records) || records.length > 16) {
    throw new TypeError('INVALID_EXIT_VERIFICATION');
  }
  for (const record of records) {
    if (!Number.isSafeInteger(record.pid) || record.pid <= 0 ||
        !Number.isFinite(record.spawnedAtEpochMs) ||
        typeof record.launchCommand !== 'string' || !record.launchCommand) {
      throw new TypeError('INVALID_PROCESS_IDENTITY');
    }
  }
  if (records.length === 0) {
    return { status: 'INSPECTION_UNKNOWN', observations: [], elapsedMs: 0, reason: 'NO_RECORDED_PROCESSES' };
  }
  const start = now();
  const realStart = Date.now();
  let observations = [];
  const elapsed = () => Math.max(now() - start, Date.now() - realStart);
  const result = status => ({ status, observations, elapsedMs: elapsed() });

  while (true) {
    observations = [];
    let anyAlive = false;
    for (const record of records) {
      let observed;
      let timer;
      const remaining = Math.max(1, timeoutMs - elapsed());
      try {
        observed = await Promise.race([
          Promise.resolve().then(() => inspect(record.pid)),
          new Promise((_, reject) => {
            timer = setTimeout(() => reject(new Error('PROCESS_INSPECTION_TIMEOUT')), remaining);
          }),
        ]);
      } catch (error) {
        observations.push({ pid: record.pid, inspectionError: error.message });
        return result('INSPECTION_UNKNOWN');
      } finally {
        clearTimeout(timer);
      }
      observations.push(observed);
      if (!observed || observed.inspectionError || observed.pid !== record.pid ||
          typeof observed.exists !== 'boolean') {
        return result('INSPECTION_UNKNOWN');
      }
      if (!observed.exists) continue;
      if (!Number.isFinite(observed.startedAtEpochMs) || typeof observed.commandLine !== 'string') {
        return result('INSPECTION_UNKNOWN');
      }
      if (Math.abs(observed.startedAtEpochMs - record.spawnedAtEpochMs) > 2000 ||
          !observed.commandLine.toLowerCase().includes(path.basename(record.launchCommand).toLowerCase())) {
        return result('OWNERSHIP_CHANGED');
      }
      anyAlive = true;
    }
    if (!anyAlive) return result('VERIFIED_EXIT');
    if (elapsed() >= timeoutMs) return result('EXIT_TIMEOUT');
    await sleep(Math.min(pollMs, timeoutMs - elapsed()));
  }
}
