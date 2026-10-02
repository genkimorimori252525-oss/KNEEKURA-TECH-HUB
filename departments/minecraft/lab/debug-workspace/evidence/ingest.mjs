import { readFile } from 'node:fs/promises';
import {
  validateObservation,
} from './schema.mjs';

export class RawEvidenceIngestor {
  constructor(store, options = {}) {
    this.store = store;
    this.expectedProcessEpoch = Number.isInteger(options.processEpoch)
      ? options.processEpoch
      : null;
    this.expectedRunSnapshotId =
      typeof options.runSnapshotId === 'string' && options.runSnapshotId
        ? options.runSnapshotId
        : null;
  }

  validateIdentity(record) {
    const errors = [];
    if (record.debugSessionId !== this.store.identity.debugSessionId) {
      errors.push(
        'debugSessionId mismatch: expected=' +
        this.store.identity.debugSessionId +
        ' actual=' + record.debugSessionId
      );
    }
    if (record.runId !== this.store.identity.runId) {
      errors.push(
        'runId mismatch: expected=' +
        this.store.identity.runId +
        ' actual=' + record.runId
      );
    }
    if (this.expectedRunSnapshotId != null &&
        record.runSnapshotId !== this.expectedRunSnapshotId) {
      errors.push(
        'runSnapshotId mismatch: expected=' +
        this.expectedRunSnapshotId +
        ' actual=' + record.runSnapshotId
      );
    }
    if (this.expectedProcessEpoch != null &&
        record.processEpoch !== this.expectedProcessEpoch) {
      errors.push(
        'processEpoch mismatch: expected=' +
        this.expectedProcessEpoch +
        ' actual=' + record.processEpoch
      );
    }
    return {
      ok: errors.length === 0,
      errors,
    };
  }

  async ingestRecord(record, context = {}) {
    const validation = validateObservation(record);
    if (!validation.ok) {
      throw new Error(
        'raw observation schema rejected' +
        (context.source ? ' source=' + context.source : '') +
        ': ' + validation.errors.join('; ')
      );
    }

    const identity = this.validateIdentity(record);
    if (!identity.ok) {
      throw new Error(
        'raw observation identity rejected' +
        (context.source ? ' source=' + context.source : '') +
        ': ' + identity.errors.join('; ')
      );
    }

    return await this.store.appendObservation(record);
  }

  async ingestText(text, context = {}) {
    const sourceText = String(text);
    const lines = sourceText.split(/\r?\n/);
    let parsed = 0;
    let written = 0;
    let suppressed = 0;
    let trailingPartial = false;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      if (!line.trim()) continue;

      let record;
      try {
        record = JSON.parse(line);
      } catch (error) {
        const isFinalLine = i === lines.length - 1;
        const fileEndsWithNewline = /(?:\r?\n)$/.test(sourceText);
        if (context.allowTrailingPartial === true &&
            isFinalLine &&
            !fileEndsWithNewline) {
          trailingPartial = true;
          break;
        }

        throw new Error(
          'invalid raw JSONL at line ' + (i + 1) +
          (context.source ? ' source=' + context.source : '') +
          ': ' + error.message
        );
      }

      parsed++;
      const result = await this.ingestRecord(record, {
        ...context,
        line: i + 1,
      });
      if (result.written) written++;
      else suppressed++;
    }

    return {
      parsed,
      written,
      suppressed,
      trailingPartial,
    };
  }

  async ingestFile(file) {
    const text = await readFile(file, 'utf8');
    return await this.ingestText(text, {
      source: file,
      allowTrailingPartial: true,
    });
  }
}
