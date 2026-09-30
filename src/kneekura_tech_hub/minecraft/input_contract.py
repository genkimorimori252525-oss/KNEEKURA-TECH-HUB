"""Run-bound M4 input safety boundary, shared by fixture and registered native adapters.

The injected backend is a trusted adapter, not input data. It must discover the
actual game window, bind its identity to the existing authenticated observer,
and implement atomic target/foreground/viewport checks at dispatch. A snapshot
check here alone cannot prevent an OS focus race. Every backend method must honor
its absolute monotonic deadline; Python cannot interrupt a non-cooperative native
call. The backend must reject pre-existing held controls and arrange a bounded
fail-safe release if its process dies. The selected Linux/X11 production route
lives in input_route/native_input.
Driver implementation and fixture coverage do not constitute live acceptance.

This module starts no game, sends no commands, creates no session authority, and
never treats backend completion as actual right-click or game behavior evidence.
"""
from __future__ import annotations

from concurrent.futures import CancelledError
import json
import math
import re
import time
from typing import Callable, Protocol

from .storage import ContractError, canonical
from .verification import IDENTITY_FIELDS, _identity_errors

_REQUEST_FIELDS = {'schema_version', 'operation_id', 'identity', 'target_id',
                   'control', 'position', 'hold_ms'}
_SCOPE_FIELDS = {'identity', 'target_id', 'foreground', 'client_size'}
_CONTROL = re.compile(r'(?:mouse:(?:left|right|middle)|key:[A-Za-z0-9_]{1,32})')
_ID = re.compile(r'[A-Za-z0-9_.:-]{1,128}')


class InputBackend(Protocol):
    """Explicitly injected, deadline-aware adapter; never an implicit OS fallback.

    snapshot returns the existing observer identity, opaque target_id, foreground
    boolean and client_size in client-local pixels. press must atomically compare
    that scope again before mutation, including the run/epoch. It may acquire only
    the requested control, and must return only after it was pressed. A driver may
    own the full bounded gesture and release before returning. In that case release
    confirms that same owned release, without injecting a second event. release
    releases only that operation's control, even if focus/epoch changed; it must
    never refocus or send a new press to another window. All methods raise when
    completion is uncertain. A real adapter needs its own live evidence for these
    properties; deterministic injected tests cannot prove OS-level guarantees.
    """

    def snapshot(self, *, deadline: float) -> dict: ...

    def press(self, request: dict, scope: dict, *, deadline: float) -> None: ...

    def release(self, *, operation_id: str, target_id: str, control: str,
                deadline: float) -> None: ...


def _detached(value: dict) -> dict:
    try:
        raw = canonical(value)
        if len(raw) > 16384:
            raise ContractError('Input contract exceeds byte budget')
        value = json.loads(raw)
    except (TypeError, ValueError, RecursionError) as exc:
        raise ContractError('Input contract must be finite JSON data') from exc
    if not isinstance(value, dict):
        raise ContractError('Input contract must be an object')
    return value


def _identity(contract: dict, value: dict) -> None:
    if not isinstance(value, dict) or set(value) != set(IDENTITY_FIELDS):
        raise ContractError('Input requires the existing complete run identity only')
    errors = _identity_errors(contract, {'identity': value})
    if errors:
        raise ContractError('; '.join(errors))


def _validate(contract, request, target_id, allowed_controls, timeout_seconds):
    if not isinstance(contract, dict):
        raise ContractError('Existing run contract required')
    errors = _identity_errors(contract, {'identity': contract})
    if errors or contract.get('physical_side') != 'client':
        raise ContractError('Input requires a valid physical-client run contract')
    if (type(timeout_seconds) not in (int, float) or not 0 < timeout_seconds <= 5
            or not math.isfinite(timeout_seconds)):
        raise ContractError('Input timeout must be finite and within five seconds')
    if not isinstance(target_id, str) or not _ID.fullmatch(target_id):
        raise ContractError('Explicit bounded target identity required')
    if (not isinstance(allowed_controls, (tuple, list)) or not 1 <= len(allowed_controls) <= 32
            or any(not isinstance(c, str) or not _CONTROL.fullmatch(c) for c in allowed_controls)
            or len(set(allowed_controls)) != len(allowed_controls)):
        raise ContractError('Explicit distinct bounded physical-control allowlist required')
    request = _detached(request)
    if set(request) != _REQUEST_FIELDS or type(request['schema_version']) is not int or request['schema_version'] != 1:
        raise ContractError('Expected exactly input-request v1 fields')
    _identity(contract, request['identity'])
    if request['target_id'] != target_id:
        raise ContractError('Input request differs from the registered target')
    if not isinstance(request['operation_id'], str) or not _ID.fullmatch(request['operation_id']):
        raise ContractError('Bounded input operation ID required')
    control = request['control']
    if not isinstance(control, str) or control not in allowed_controls:
        raise ContractError('Input control is not explicitly registered')
    hold = request['hold_ms']
    if type(hold) is not int or not 1 <= hold <= 250 or hold / 1000 >= timeout_seconds:
        raise ContractError('Input hold must be 1..250 milliseconds within the operation budget')
    point = request['position']
    if control.startswith('mouse:'):
        if (not isinstance(point, list) or len(point) != 2
                or any(type(n) is not int or not 0 <= n < 32768 for n in point)):
            raise ContractError('Mouse position must be bounded client-local integer coordinates')
    elif point is not None:
        raise ContractError('Keyboard input cannot include mouse coordinates')
    return request


def _scope(contract, request, value):
    value = _detached(value)
    if set(value) != _SCOPE_FIELDS:
        raise ContractError('Expected complete target scope')
    _identity(contract, value['identity'])
    if value['target_id'] != request['target_id'] or value['foreground'] is not True:
        raise ContractError('Expected game target is not foreground')
    size = value['client_size']
    if (not isinstance(size, list) or len(size) != 2
            or any(type(n) is not int or not 1 <= n <= 32768 for n in size)):
        raise ContractError('Invalid client viewport')
    point = request['position']
    if point is not None and any(n >= bound for n, bound in zip(point, size)):
        raise ContractError('Input coordinate is outside the client viewport')
    return value


def _before_deadline(clock, deadline):
    if clock() >= deadline:
        raise ContractError('Input operation deadline expired')


def dispatch_input(contract: dict, request: dict, *, target_id: str,
                   allowed_controls: tuple[str, ...], backend: InputBackend,
                   timeout_seconds: float = 2, clock: Callable[[], float] = time.monotonic,
                   sleep: Callable[[float], None] = time.sleep) -> dict:
    """Attempt exactly one scoped control press and one release, without retries.

    The target and allowed controls come from trusted registration, not a spec or
    command. Key codes are opaque physical backend identifiers, not game actions.
    Mouse coordinates are client-local pixels, never desktop-global coordinates.
    Cleanup has its own one-second budget so an expired press deadline does not
    skip release. Cancellation propagates after a release attempt. This method
    neither persists an operation ledger nor authorizes replay after failure.
    """
    request = _validate(contract, request, target_id, allowed_controls, timeout_seconds)
    # Detach the authority too: a backend must not mutate later comparisons.
    identity = dict(request['identity'])
    deadline = clock() + timeout_seconds
    result = dict(schema_version=1, identity=identity, operation_id=request['operation_id'],
                  target_id=target_id, control=request['control'], input_status='BLOCKED',
                  outcome='BLOCKED', retry_allowed=False, release_attempted=False,
                  release_completed=False, evidence_level='INJECTED_BACKEND_NOT_LIVE_ATTESTATION',
                  verification=dict(actual_right_click='NOT_RUN', server_behavior='NOT_RUN',
                                    visual='NOT_RUN', synchronization='NOT_RUN'), reasons=[])
    try:
        _before_deadline(clock, deadline)
        before = _scope(identity, request, backend.snapshot(deadline=deadline))
        if clock() + request['hold_ms'] / 1000 >= deadline:
            raise ContractError('Insufficient remaining input hold budget')
    except CancelledError:
        raise
    except Exception:
        result['reasons'] = ['No current foreground target and same-run scope within the deadline']
        return result

    failure = False
    pending_cancellation = None
    try:
        # The driver rechecks this immutable-by-copy scope at the actual dispatch.
        backend.press(_detached(request), _detached(before), deadline=deadline)
        if clock() + request['hold_ms'] / 1000 >= deadline:
            raise ContractError('Insufficient remaining input hold budget')
        sleep(request['hold_ms'] / 1000)
        _before_deadline(clock, deadline)
    except BaseException as exc:
        if isinstance(exc, Exception) and not isinstance(exc, CancelledError):
            failure = True
        else:
            # Preserve cancellation/control flow while still attempting release.
            pending_cancellation = exc
    finally:
        result['release_attempted'] = True
        cleanup_deadline = clock() + 1
        try:
            backend.release(operation_id=request['operation_id'], target_id=target_id,
                            control=request['control'], deadline=cleanup_deadline)
            _before_deadline(clock, cleanup_deadline)
            result['release_completed'] = True
        except BaseException as exc:
            if isinstance(exc, Exception) and not isinstance(exc, CancelledError):
                failure = True
            elif pending_cancellation is None:
                pending_cancellation = exc

    if pending_cancellation is not None:
        raise pending_cancellation
    if not failure:
        try:
            _before_deadline(clock, deadline)
            after = _scope(identity, request, backend.snapshot(deadline=deadline))
            _before_deadline(clock, deadline)
            if after != before:
                raise ContractError('Input scope changed during the operation')
        except CancelledError:
            raise
        except Exception:
            failure = True
    if failure:
        result.update(input_status='UNKNOWN', outcome='UNKNOWN',
                      reasons=['Input completion or release is uncertain; inspect before any new operation'])
    else:
        result.update(input_status='COMPLETED', outcome='NOT_RUN',
                      reasons=['Injected adapter completed; actual input and game assertions remain unverified'])
    return result
