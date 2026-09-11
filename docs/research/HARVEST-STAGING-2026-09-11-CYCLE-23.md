# KNEEKURA TECH HUB — Harvest Staging 2026-09-11 Cycle 23

Status: **STAGING / NON-CANONICAL**

This memo records evidence-backed candidates only. Popularity was used as a discovery prior, not as validation. Existing main research and open Harvest PRs through Cycle 22 were checked for obvious duplication. No VALIDATED promotion, canonical Knowledge Entity creation, production implementation, or authority expansion is implied.

## 1. React Scheduler — deadline aging so deferred work eventually becomes non-yieldable

- Repository: `react/react`
- Repository URL: https://github.com/react/react
- Stars observed during harvest: 250,033
- Revision: `00f48cecfc34b371a03f3c601819439cb16e2e96`
- Primary path: `packages/scheduler/src/forks/Scheduler.js`
- Supporting path: `packages/scheduler/src/SchedulerFeatureFlags.js`
- Evidence URL: https://github.com/react/react/blob/00f48cecfc34b371a03f3c601819439cb16e2e96/packages/scheduler/src/forks/Scheduler.js

### Technique

Scheduler tasks carry both a priority and an `expirationTime`. Normal, low, and user-blocking priorities receive different timeout horizons. The work loop may yield while a task is still unexpired, but once `expirationTime <= currentTime`, the task is treated as timed out and no longer deferred merely because the current time slice has been consumed. Delayed tasks are separately kept in a timer heap until their start time is reached, then moved into the runnable heap ordered by expiration.

This is a useful distinction between **priority** and **age/deadline**: low-priority work may yield repeatedly while the system is busy, but it does not have to remain postponable forever.

### Why it may help KNEEKURA

Potential use in background indexing, evidence enrichment, repository scans, or maintenance queues where interactive work should normally win but old maintenance items must eventually run. A KNEEKURA scheduler could keep `priority_class` separate from `must_run_after` / `expiration_at`, preventing permanent starvation without pretending old background work has always been high priority.

### Limitations / uncertainty

- React's concrete timeout constants (for example 250 ms and 5000 ms in the inspected feature flags) are UI scheduler tuning values and must not be copied into KNEEKURA.
- This pattern does not itself provide CPU, RAM, I/O, or authority isolation.
- Expiration makes work less deferrable; it does not prove the work is safe to execute under overload.
- Cycle 09 already harvested cooperative task budgeting from Tokio. The distinct candidate here is specifically **age/deadline promotion against starvation**, not cooperative yielding itself.

## 2. Celery — acknowledge only after completion, with explicit worker-loss redelivery policy

- Repository: `celery/celery`
- Repository URL: https://github.com/celery/celery
- Stars observed during harvest: 28,875
- Revision: `918a740497a4ce883f37eb1a3e7c2a80dfcc8b7a`
- Primary paths:
  - `celery/worker/request.py`
  - `celery/app/task.py`
  - `docs/userguide/tasks.rst`
- Evidence URLs:
  - https://github.com/celery/celery/blob/918a740497a4ce883f37eb1a3e7c2a80dfcc8b7a/celery/worker/request.py
  - https://github.com/celery/celery/blob/918a740497a4ce883f37eb1a3e7c2a80dfcc8b7a/celery/app/task.py

### Technique

Celery exposes `acks_late` so a queued task can be acknowledged after execution rather than when first received. Its worker request handling also distinguishes worker-loss behavior: `reject_on_worker_lost` can cause a late-ack task to be rejected/requeued when the process executing it disappears, rather than treating disappearance as successful consumption. The documentation explicitly warns that worker termination is normally acknowledged in several cases and exposes `task_reject_on_worker_lost` when redelivery is truly desired.

The reusable idea is to separate four facts that are often incorrectly collapsed into one:

1. work was delivered,
2. work started,
3. work completed with acceptable evidence,
4. the queue item may now be acknowledged/retired.

### Why it may help KNEEKURA

For Runner jobs, repository analysis, long model calls, Minecraft observation jobs, or other crash-prone workers, KNEEKURA can avoid converting "worker disappeared after receipt" into "job completed". A governed receipt could remain outstanding until a completion artifact/checkpoint is durable, while worker-loss policy decides whether the task becomes retryable, terminal, or human-review-required.

### Limitations / uncertainty

- Late acknowledgement produces at-least-once behavior, so duplicate execution is possible. Side-effecting jobs therefore require idempotency keys, deduplication, or a transactional boundary.
- Blind requeue-on-loss can create loops for deterministic crashes or OOMs; Celery itself warns this setting can cause message loops.
- External side effects may have happened before the worker died, so "not acknowledged" does not mean "nothing happened".
- KNEEKURA should preserve separate execution evidence and mutation receipts rather than treating queue acknowledgement as proof of semantic success.

## 3. systemd — manager-owned socket activation decouples endpoint lifetime from worker lifetime

- Repository: `systemd/systemd`
- Repository URL: https://github.com/systemd/systemd
- Stars observed during harvest: 16,675
- Revision: `aaab1f107ca1203636ecac2f47a4f5f8611c0b1c`
- Primary paths:
  - `man/systemd.socket.xml`
  - `man/sd_listen_fds.xml`
  - `src/core/socket.c`
- Supporting path: `man/sd_notify.xml`
- Evidence URLs:
  - https://github.com/systemd/systemd/blob/aaab1f107ca1203636ecac2f47a4f5f8611c0b1c/man/systemd.socket.xml
  - https://github.com/systemd/systemd/blob/aaab1f107ca1203636ecac2f47a4f5f8611c0b1c/man/sd_listen_fds.xml

### Technique

With socket activation, the supervisor/service manager owns and listens on the communication endpoint, then passes the already-open file descriptor to the service. The service checks descriptors supplied by the manager via the `sd_listen_fds()` contract instead of always creating/binding the endpoint itself. This separates **endpoint ownership** from **worker-process ownership** and allows service activation to be driven by incoming work.

The broader pattern is: keep the durable ingress endpoint in a smaller, more stable supervisor; allow replaceable workers to attach to that endpoint rather than owning its identity and lifetime.

### Why it may help KNEEKURA

A local Command Bridge, model proxy, Runner gateway, or observation helper could preserve a stable local endpoint while the implementation worker is restarted/upgraded. Requests can be accepted/queued at the supervisor boundary instead of failing solely because the worker generation is between processes. It also enables on-demand worker startup rather than keeping every heavy helper resident.

### Limitations / uncertainty

- Passing listening sockets is platform/runtime-specific; Windows implementation details differ substantially from Linux/systemd.
- An available socket is not proof the downstream worker is healthy or ready. Readiness and bounded queue/backpressure signals are still required.
- Queuing requests while a worker is absent can increase latency and memory pressure; admission limits are necessary.
- This does not automatically preserve in-flight application state across restarts; only endpoint/file-descriptor lifetime is decoupled.
- For KNEEKURA on Windows, the architectural concept is more portable than the literal `sd_listen_fds()` mechanism.

## Cross-finding hypothesis (still NON-CANONICAL)

A possible KNEEKURA runtime contract suggested by these three findings is:

1. let interactive/critical work normally outrank maintenance, but attach an age/deadline so deferred work cannot starve forever;
2. keep delivery/start/completion/acknowledgement as separate durable states, and never interpret worker disappearance as completion without evidence;
3. where practical, let a stable supervisor own ingress identity while replaceable workers can restart behind it.

This composition is an inference made during this harvest, not evidence that the three upstream projects endorse the combined design. It requires independent KNEEKURA validation before any canonical promotion or implementation.

## Governance boundary

All findings above remain **STAGING / NON-CANONICAL**. No claim here authorizes implementation, merge to canonical knowledge, or VALIDATED status. Human/governed review must evaluate evidence quality, fit, failure modes, and interaction with existing KNEEKURA invariants before promotion.
