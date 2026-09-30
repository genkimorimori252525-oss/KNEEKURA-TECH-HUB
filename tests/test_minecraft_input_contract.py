"""M4 injected-backend contracts; no native input or live game coverage."""
from __future__ import annotations

import asyncio
from concurrent.futures import CancelledError
import copy
import importlib

import pytest

from kneekura_tech_hub.minecraft.storage import ContractError
from test_minecraft_verification import contract
from kneekura_tech_hub.minecraft.verification import IDENTITY_FIELDS


def api():
    try:
        return importlib.import_module('kneekura_tech_hub.minecraft.input_contract')
    except ImportError:
        pytest.fail('Scoped input contract is not implemented')


class Clock:
    def __init__(self):
        self.value = 10.0

    def now(self):
        return self.value

    def sleep(self, seconds):
        self.value += seconds


class Backend:
    """Cooperative deterministic fixture, never a real input driver."""
    def __init__(self, identity, clock):
        self.state = dict(identity=copy.deepcopy(identity), target_id='game-window-1',
                          foreground=True, client_size=[640, 480])
        self.clock = clock
        self.calls = []
        self.after_press = None
        self.press_error = None
        self.release_error = None
        self.snapshot_delay = 0

    def snapshot(self, *, deadline):
        self.calls.append(('snapshot', deadline))
        self.clock.value += self.snapshot_delay
        return copy.deepcopy(self.state)

    def press(self, request, scope, *, deadline):
        self.calls.append(('press', copy.deepcopy(request), copy.deepcopy(scope), deadline))
        if self.after_press:
            self.after_press(self)
        if self.press_error:
            raise self.press_error

    def release(self, *, operation_id, target_id, control, deadline):
        self.calls.append(('release', operation_id, target_id, control, deadline))
        if self.release_error:
            raise self.release_error


@pytest.fixture
def case():
    c = contract()
    c.update(physical_side='client', assertion_domain='client_observation')
    identity = {key: c[key] for key in IDENTITY_FIELDS}
    request = dict(schema_version=1, operation_id='use-1', identity=identity,
                   target_id='game-window-1', control='mouse:right', position=[320, 240], hold_ms=50)
    clock = Clock()
    backend = Backend(identity, clock)
    return c, request, clock, backend


def dispatch(case, **kwargs):
    c, request, clock, backend = case
    return api().dispatch_input(c, request, target_id='game-window-1',
                                allowed_controls=('mouse:right', 'key:E'), backend=backend,
                                clock=clock.now, sleep=clock.sleep, **kwargs)


def mutations(backend):
    return [row for row in backend.calls if row[0] in ('press', 'release')]


def test_single_scoped_press_release_keeps_runtime_verdict_unrun(case):
    c, request, clock, backend = case
    result = dispatch(case)
    assert [row[0] for row in backend.calls] == ['snapshot', 'press', 'release', 'snapshot']
    assert mutations(backend)[0][1] == request
    assert mutations(backend)[0][2]['client_size'] == [640, 480]
    assert mutations(backend)[1][1:4] == ('use-1', 'game-window-1', 'mouse:right')
    assert result['input_status'] == 'COMPLETED'
    assert result['outcome'] == 'NOT_RUN'
    assert result['verification'] == dict(actual_right_click='NOT_RUN', server_behavior='NOT_RUN',
                                          visual='NOT_RUN', synchronization='NOT_RUN')
    assert result['evidence_level'] == 'INJECTED_BACKEND_NOT_LIVE_ATTESTATION'
    assert result['identity'] == request['identity'] and result['operation_id'] == 'use-1'
    assert result['release_attempted'] is True and result['release_completed'] is True
    assert result['retry_allowed'] is False


@pytest.mark.parametrize('field', ['run_id', 'session_epoch', 'profile_id', 'build_artifact_hash',
                                    'world_id', 'scenario_hash', 'assertion_hash'])
def test_stale_request_is_rejected_before_backend_contact(case, field):
    case[1]['identity'][field] = 'stale'
    with pytest.raises(ContractError):
        dispatch(case)
    assert case[3].calls == []


@pytest.mark.parametrize('change', [
    {'command': '/function pretend_right_click'}, {'control': 'command:use'},
    {'control': 'key:F5'}, {'target_id': 'other-window'}, {'schema_version': True},
    {'hold_ms': True}, {'hold_ms': 0}, {'hold_ms': 251}, {'hold_ms': float('nan')},
    {'position': [-1, 0]}, {'position': [True, 1]}, {'position': [1.5, 2]},
    {'operation_id': ''}, {'operation_id': 'x' * 129},
])
def test_invalid_requests_never_reach_backend(case, change):
    case[1].update(change)
    with pytest.raises(ContractError):
        dispatch(case)
    assert case[3].calls == []


@pytest.mark.parametrize('change', [
    {'foreground': False}, {'foreground': 1}, {'target_id': 'different'},
    {'client_size': [320, 240]}, {'client_size': [0, 480]}, {'client_size': [640, True]},
])
def test_wrong_foreground_target_or_viewport_blocks_without_press(case, change):
    case[3].state.update(change)
    result = dispatch(case)
    assert result['input_status'] == 'BLOCKED'
    assert result['outcome'] == 'BLOCKED'
    assert result['release_attempted'] is False
    assert mutations(case[3]) == []


def test_stale_backend_epoch_blocks_without_press(case):
    case[3].state['identity']['session_epoch'] = 'restarted'
    result = dispatch(case)
    assert result['input_status'] == 'BLOCKED' and mutations(case[3]) == []


def test_keyboard_requires_explicit_registration_and_no_coordinates(case):
    case[1].update(control='key:E', position=None)
    result = dispatch(case)
    assert result['input_status'] == 'COMPLETED'
    assert mutations(case[3])[1][3] == 'key:E'


def test_keyboard_with_mouse_coordinates_is_invalid(case):
    case[1]['control'] = 'key:E'
    with pytest.raises(ContractError):
        dispatch(case)
    assert case[3].calls == []


def test_server_contract_cannot_dispatch_client_input(case):
    case[0]['physical_side'] = 'server'
    case[1]['identity']['physical_side'] = 'server'
    with pytest.raises(ContractError):
        dispatch(case)
    assert case[3].calls == []


@pytest.mark.parametrize('failure', ['focus', 'epoch', 'target', 'viewport'])
def test_changed_scope_after_press_releases_and_never_claims_success(case, failure):
    def change(backend):
        if failure == 'focus': backend.state['foreground'] = False
        if failure == 'epoch': backend.state['identity']['session_epoch'] = 'restarted'
        if failure == 'target': backend.state['target_id'] = 'different'
        if failure == 'viewport': backend.state['client_size'] = [800, 600]
    case[3].after_press = change
    result = dispatch(case)
    assert result['input_status'] == 'UNKNOWN' and result['outcome'] == 'UNKNOWN'
    assert result['release_completed'] is True
    assert [row[0] for row in mutations(case[3])] == ['press', 'release']
    assert result['retry_allowed'] is False


def test_uncertain_press_releases_once_without_retry_or_exception_leak(case):
    case[3].press_error = OSError('secret backend error')
    result = dispatch(case)
    assert result['input_status'] == 'UNKNOWN' and result['outcome'] == 'UNKNOWN'
    assert result['release_completed'] is True
    assert [row[0] for row in mutations(case[3])] == ['press', 'release']
    assert 'secret backend error' not in str(result)


def test_release_failure_is_unknown_and_not_retried(case):
    case[3].release_error = OSError('uncertain release')
    result = dispatch(case)
    assert result['input_status'] == 'UNKNOWN'
    assert result['release_attempted'] is True and result['release_completed'] is False
    assert [row[0] for row in mutations(case[3])] == ['press', 'release']


def test_cancellation_still_attempts_release_and_propagates(case):
    case[3].press_error = KeyboardInterrupt()
    with pytest.raises(KeyboardInterrupt):
        dispatch(case)
    assert [row[0] for row in mutations(case[3])] == ['press', 'release']


def test_expired_preflight_has_no_mutation(case):
    case[3].snapshot_delay = 3
    result = dispatch(case, timeout_seconds=2)
    assert result['input_status'] == 'BLOCKED'
    assert mutations(case[3]) == []


def test_expired_press_gets_separate_bounded_cleanup_deadline(case):
    case[3].after_press = lambda backend: setattr(backend.clock, 'value', 20)
    result = dispatch(case, timeout_seconds=2)
    assert result['input_status'] == 'UNKNOWN'
    press, release = mutations(case[3])
    assert press[-1] == 12 and release[-1] == 21
    assert result['release_completed'] is True


@pytest.mark.parametrize('timeout', [0, -1, True, float('inf'), float('nan'), 5.01])
def test_timeout_must_be_finite_and_bounded_before_backend_contact(case, timeout):
    with pytest.raises(ContractError):
        dispatch(case, timeout_seconds=timeout)
    assert case[3].calls == []


def test_hold_never_sleeps_past_remaining_operation_budget(case):
    # The preflight consumed most of the budget, leaving less than the hold.
    case[3].snapshot_delay = 0.09
    result = dispatch(case, timeout_seconds=0.1)
    assert result['input_status'] in ('BLOCKED', 'UNKNOWN')
    assert case[2].value <= 10.1


def test_extreme_timeout_is_a_contract_error_without_backend_contact(case):
    with pytest.raises(ContractError):
        dispatch(case, timeout_seconds=10**1000)
    assert case[3].calls == []


def test_backend_cannot_change_release_target_control_or_returned_identity(case):
    backend = case[3]
    original = backend.press

    def mutate(request, scope, *, deadline):
        original(request, scope, deadline=deadline)
        request['control'] = 'key:OTHER'
        request['target_id'] = 'other-window'
        request['identity']['session_epoch'] = 'foreign'
        scope['identity']['run_id'] = 'foreign'

    backend.press = mutate
    result = dispatch(case)
    assert result['input_status'] == 'COMPLETED'
    assert result['identity']['session_epoch'] == case[0]['session_epoch']
    assert mutations(backend)[1][1:4] == ('use-1', 'game-window-1', 'mouse:right')


def test_unknown_identity_fields_cannot_carry_a_second_authority(case):
    case[1]['identity']['token'] = 'secret'
    with pytest.raises(ContractError):
        dispatch(case)
    assert case[3].calls == []


def test_snapshot_failure_is_blocked_without_mutation_or_backend_error_leak(case):
    def unavailable(*, deadline):
        raise OSError('private backend detail')
    case[3].snapshot = unavailable
    result = dispatch(case)
    assert result['input_status'] == 'BLOCKED'
    assert mutations(case[3]) == []
    assert 'private backend detail' not in str(result)


def test_release_returning_after_cleanup_deadline_is_unconfirmed(case):
    backend = case[3]
    original = backend.release
    def late(**kwargs):
        original(**kwargs)
        case[2].value += 2
    backend.release = late
    result = dispatch(case)
    assert result['input_status'] == 'UNKNOWN'
    assert result['release_attempted'] and not result['release_completed']
    assert [row[0] for row in mutations(backend)] == ['press', 'release']


@pytest.mark.parametrize('cancel_type', [CancelledError, asyncio.CancelledError])
@pytest.mark.parametrize('boundary', ['pre_snapshot', 'press', 'hold', 'release', 'post_snapshot'])
def test_standard_cancellation_propagates_at_each_input_boundary(case, cancel_type, boundary):
    cancellation = cancel_type('cancelled')
    backend = case[3]
    if boundary in ('pre_snapshot', 'post_snapshot'):
        original = backend.snapshot
        def cancel_snapshot(*, deadline):
            state = original(deadline=deadline)
            if boundary == 'pre_snapshot' or any(row[0] == 'release' for row in backend.calls):
                raise cancellation
            return state
        backend.snapshot = cancel_snapshot
    elif boundary == 'press':
        backend.press_error = cancellation
    elif boundary == 'hold':
        def cancel_hold(seconds):
            raise cancellation
        case[2].sleep = cancel_hold
    else:
        backend.release_error = cancellation
    with pytest.raises(cancel_type) as raised:
        dispatch(case)
    assert raised.value is cancellation
    expected = [] if boundary == 'pre_snapshot' else ['press', 'release']
    assert [row[0] for row in mutations(backend)] == expected


@pytest.mark.parametrize('pending_type', [CancelledError, asyncio.CancelledError, KeyboardInterrupt])
@pytest.mark.parametrize('release_type', [OSError, CancelledError, asyncio.CancelledError])
def test_release_failure_cannot_mask_pending_cancellation(case, pending_type, release_type):
    cancellation = pending_type('original cancellation')
    case[3].press_error = cancellation
    case[3].release_error = release_type('cleanup failure')
    with pytest.raises(pending_type) as raised:
        dispatch(case)
    assert raised.value is cancellation
    assert [row[0] for row in mutations(case[3])] == ['press', 'release']
