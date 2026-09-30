"""Window-addressed Linux/X11 native button events; no global device injection.

XSendEvent targets the exact authenticated native window with propagation disabled
and NoEventMask, which delivers only to that window's creating client. Physical
pointer motion cannot change either event's destination. GLFW's X11 Button3
handlers consume these synthetic native events through its normal mouse callback.
This is not hardware-device attestation or proof Minecraft handled the gesture.

Short server grabs protect identity checks and each send, not the physical pointer.
They are never held for the requested delay. The child owns one scoped release;
parent timeout permits bounded cleanup then closes any stuck helper connection.
Unconfirmed game-side release is UNKNOWN and quarantined, never retried globally.

API: https://xorg.freedesktop.org/archive/X11R7.5/doc/man/man3/XSendEvent.3.html
GLFW: https://raw.githubusercontent.com/glfw/glfw/3.4/src/x11_window.c
"""
from __future__ import annotations

import ctypes as C
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import threading
import time

from .storage import ContractError, canonical

BACKEND_ID = 'linux-x11-send-event-v1'


def validate_display(value):
    if not isinstance(value, str) or not re.fullmatch(r':[0-9]{1,5}(?:\.[0-9]{1,2})?', value):
        raise ContractError('Explicit local X11 display required; no remote display or fallback')
    return value


def process_start(pid):
    if type(pid) is not int or not 1 <= pid <= 2**31-1 or not sys.platform.startswith('linux'):
        raise ContractError('Linux process identity required')
    path = Path('/proc') / str(pid)
    try:
        if path.stat().st_uid != os.getuid():
            raise ContractError('Game must run as the current local user')
        raw = (path / 'stat').read_text()
        # comm may contain spaces and parentheses; field 22 follows the last ')'.
        value = raw.rsplit(')', 1)[1].split()[19]
        if not value.isdecimal(): raise ValueError()
        return value
    except (OSError, IndexError, ValueError) as exc:
        raise ContractError('Native process is unavailable or changed') from exc


def validate_target(target):
    if (not isinstance(target, dict) or set(target) != {'process_id', 'process_start', 'window_id', 'client_size'}
            or not isinstance(target['window_id'], str) or not target['window_id'].isdecimal()
            or not 2 <= int(target['window_id']) < 2**32
            or not isinstance(target['process_start'], str) or not target['process_start'].isdecimal()
            or not isinstance(target['client_size'], list) or len(target['client_size']) != 2
            or any(type(n) is not int or not 1 <= n <= 32768 for n in target['client_size'])):
        raise ContractError('Complete native process/window/local viewport identity required')
    if process_start(target['process_id']) != target['process_start']:
        raise ContractError('Native process start identity changed')
    return target


class _SendNotAttempted(ContractError):
    """Read-only event preparation failed before XSendEvent could run."""


class XButtonEvent(C.Structure):
    _fields_ = [('type',C.c_int), ('serial',C.c_ulong), ('send_event',C.c_int),
                ('display',C.c_void_p), ('window',C.c_ulong), ('root',C.c_ulong),
                ('subwindow',C.c_ulong), ('time',C.c_ulong), ('x',C.c_int),
                ('y',C.c_int), ('x_root',C.c_int), ('y_root',C.c_int),
                ('state',C.c_uint), ('button',C.c_uint), ('same_screen',C.c_int)]


class XEvent(C.Union):
    _fields_ = [('button',XButtonEvent), ('pad',C.c_long*24)]


class X11:
    """Private helper-only ctypes wrapper around installed system libraries."""
    def __init__(self, display):
        validate_display(display)
        if not sys.platform.startswith('linux'):
            raise ContractError('This driver only supports Linux X11')
        try:
            self.x = C.CDLL('libX11.so.6')
        except OSError as exc:
            raise ContractError('Installed libX11 required') from exc
        V, I, U, L = C.c_void_p, C.c_int, C.c_uint, C.c_ulong
        self._declare(self.x, 'XOpenDisplay', V, [C.c_char_p])
        self._declare(self.x, 'XCloseDisplay', I, [V])
        self._declare(self.x, 'XGrabServer', I, [V]); self._declare(self.x, 'XUngrabServer', I, [V])
        self._declare(self.x, 'XSync', I, [V, I]); self._declare(self.x, 'XDefaultRootWindow', L, [V])
        self._declare(self.x, 'XGetInputFocus', I, [V, C.POINTER(L), C.POINTER(I)])
        self._declare(self.x, 'XGetGeometry', I, [V,L,C.POINTER(L),C.POINTER(I),C.POINTER(I),C.POINTER(U),C.POINTER(U),C.POINTER(U),C.POINTER(U)])
        self._declare(self.x, 'XTranslateCoordinates', I, [V,L,L,I,I,C.POINTER(I),C.POINTER(I),C.POINTER(L)])
        self._declare(self.x, 'XQueryPointer', I, [V,L,C.POINTER(L),C.POINTER(L),C.POINTER(I),C.POINTER(I),C.POINTER(I),C.POINTER(I),C.POINTER(U)])
        self._declare(self.x, 'XQueryKeymap', I, [V, C.POINTER(C.c_char)])
        self._declare(self.x, 'XInternAtom', L, [V,C.c_char_p,I])
        self._declare(self.x, 'XGetWindowProperty', I, [V,L,L,C.c_long,C.c_long,I,L,C.POINTER(L),C.POINTER(I),C.POINTER(L),C.POINTER(L),C.POINTER(C.POINTER(C.c_ubyte))])
        self._declare(self.x, 'XFree', I, [V])
        self._declare(self.x, 'XSendEvent', I, [V,L,I,C.c_long,C.POINTER(XEvent)])
        self.d = self.x.XOpenDisplay(display.encode('ascii'))
        if not self.d: raise ContractError('Registered X11 display is unavailable')

    @staticmethod
    def _declare(lib, name, result, args):
        function = getattr(lib, name); function.restype = result; function.argtypes = args

    def grab(self): self.x.XGrabServer(self.d); self.sync()
    def ungrab(self): self.x.XUngrabServer(self.d)
    def sync(self): self.x.XSync(self.d, 0)
    def close(self):
        if self.d: self.x.XCloseDisplay(self.d); self.d = None

    def _pid(self, window):
        atom = self.x.XInternAtom(self.d, b'_NET_WM_PID', 1)
        actual = C.c_ulong(); fmt = C.c_int(); count = C.c_ulong(); remaining = C.c_ulong()
        data = C.POINTER(C.c_ubyte)()
        status = self.x.XGetWindowProperty(self.d, window, atom, 0, 1, 0, 6,
                   C.byref(actual), C.byref(fmt), C.byref(count), C.byref(remaining), C.byref(data))
        try:
            if status or actual.value != 6 or fmt.value != 32 or count.value != 1 or remaining.value:
                raise ContractError('Native window lacks exact process metadata')
            return C.cast(data, C.POINTER(C.c_ulong))[0]
        finally:
            if data: self.x.XFree(data)

    def confirm_owner(self, target):
        validate_target(target)
        if self._pid(int(target['window_id'])) != target['process_id']:
            raise ContractError('Authenticated native window owner changed')

    def inspect(self, target):
        self.confirm_owner(target)
        window = int(target['window_id']); focus = C.c_ulong(); revert = C.c_int()
        self.x.XGetInputFocus(self.d, C.byref(focus), C.byref(revert))
        if focus.value != window:
            raise ContractError('Authenticated native window is not the foreground process')
        root = C.c_ulong(); x = C.c_int(); y = C.c_int(); width = C.c_uint(); height = C.c_uint()
        border = C.c_uint(); depth = C.c_uint()
        if not self.x.XGetGeometry(self.d, window, C.byref(root), C.byref(x), C.byref(y),
                                  C.byref(width), C.byref(height), C.byref(border), C.byref(depth)):
            raise ContractError('Native viewport unavailable')
        return {'client_size': [width.value, height.value], 'foreground': True}

    def _pointer(self, window):
        root = C.c_ulong(); child = C.c_ulong(); coords = [C.c_int() for _ in range(4)]; mask = C.c_uint()
        same = self.x.XQueryPointer(self.d, window, C.byref(root), C.byref(child),
                                   *(C.byref(n) for n in coords), C.byref(mask))
        return same, child.value, mask.value

    def any_held(self):
        keys = C.create_string_buffer(32); self.x.XQueryKeymap(self.d, keys)
        return any(keys.raw) or bool(self._pointer(self.x.XDefaultRootWindow(self.d))[2])

    def pointer_on_target(self, target):
        window = self.x.XDefaultRootWindow(self.d)
        for _ in range(32):
            if window == int(target['window_id']): return True
            same, window, _ = self._pointer(window)
            if not same or not window: return False
        return False

    def send_button(self, target, position, pressed, *, deadline):
        window = int(target['window_id'])
        if not 2 <= window < 2**32: raise _SendNotAttempted('An exact native window is required')
        root = self.x.XDefaultRootWindow(self.d); x = C.c_int(); y = C.c_int(); child = C.c_ulong()
        if not self.x.XTranslateCoordinates(self.d, window, root, *position,
                                           C.byref(x), C.byref(y), C.byref(child)):
            raise _SendNotAttempted('Native coordinate translation failed')
        if time.monotonic() >= deadline: raise _SendNotAttempted('Native send deadline expired')
        event = XEvent()
        event.button = XButtonEvent(type=4 if pressed else 5, display=self.d,
            window=window, root=root, subwindow=0, time=0,
            x=position[0], y=position[1], x_root=x.value, y_root=y.value,
            state=0 if pressed else 1<<10, button=3, same_screen=1)
        # NoEventMask=0 sends only to the creating client. Never use InputFocus,
        # PointerWindow, propagation, XTEST, or the current physical pointer.
        if not self.x.XSendEvent(self.d, window, 0, 0, C.byref(event)):
            raise ContractError('Native window event delivery is uncertain')


def perform_gesture(native, target, position, hold_ms, *, deadline):
    size = target.get('client_size')
    if (not isinstance(size, list) or len(size) != 2 or not isinstance(position, list) or len(position) != 2
            or any(type(v) is not int or not 0 <= v < bound for v, bound in zip(position, size))
            or type(hold_ms) is not int or not 1 <= hold_ms <= 250
            or time.monotonic() + hold_ms / 1000 + .05 >= deadline):
        raise ContractError('Invalid native gesture or insufficient deadline')
    pressed = False; released = False
    def remaining():
        if time.monotonic() + hold_ms / 1000 + .02 >= deadline:
            raise ContractError('Native gesture deadline expired before mutation')
    try:
        try:
            native.grab(); remaining()
            current = native.inspect(target); remaining()
            held = native.any_held(); remaining()
            if current != {'client_size':size, 'foreground':True} or held:
                raise ContractError('Native viewport changed or a physical control is already held')
            visible = native.pointer_on_target(target); remaining()
            if not visible: raise ContractError('Native target is occluded')
            # Physical input may change after that sample. It cannot retarget the
            # explicit XSendEvent window, unlike the removed global XTEST path.
            pressed = True
            try:
                native.send_button(target, position, True, deadline=deadline)
            except _SendNotAttempted:
                pressed = False
                raise
            native.sync()
        finally:
            native.ungrab(); native.sync()
        if time.monotonic()+hold_ms/1000 >= deadline:
            raise ContractError('Native gesture deadline expired after press')
        time.sleep(hold_ms/1000)
    finally:
        if pressed:
            cleanup_deadline = time.monotonic()+.5
            try:
                native.grab()
                if time.monotonic() >= cleanup_deadline: raise ContractError('Native cleanup deadline expired')
                native.confirm_owner(target)
                if time.monotonic() >= cleanup_deadline: raise ContractError('Native cleanup identity deadline expired')
                native.send_button(target, position, False, deadline=cleanup_deadline)
                native.sync(); released = True
            finally:
                native.ungrab(); native.sync()
    return {'pressed':pressed, 'released':released}


def _abandon_helper(child, *, may_own_control):
    """Allow scoped SIGTERM cleanup, then bound any stuck native connection."""
    def reap():
        try:
            child.terminate()
            try: child.communicate(timeout=.75 if may_own_control else .25)
            except subprocess.TimeoutExpired:
                # This backend holds no physical device state. Closing its X
                # connection also releases any server grab. No new release is
                # sent by the parent, and unconfirmed GLFW state stays UNKNOWN.
                child.kill(); child.communicate()
        finally:
            for stream in (child.stdin, child.stdout, child.stderr):
                if stream is not None: stream.close()
    thread = threading.Thread(target=reap, name='native-input-reaper', daemon=True)
    thread.start()
    return thread


def native_exchange(display, target, *, deadline, position=None, hold_ms=None):
    """Use only this package's helper; never execute a registry-supplied command."""
    validate_display(display); validate_target(target)
    remaining = deadline - time.monotonic()
    if not 0 < remaining <= 6: raise ContractError('Native operation deadline expired or unbounded')
    payload = {'display': display, 'target': target, 'deadline': deadline,
               'position': position, 'hold_ms': hold_ms}
    # Session secrets never enter argv, this protocol, environment additions, or CAS.
    child = subprocess.Popen([sys.executable, '-m', __name__, '--helper'],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        start_new_session=True)
    try:
        raw, _ = child.communicate(canonical(payload), timeout=remaining)
    except subprocess.TimeoutExpired as exc:
        # The helper gets a bounded scoped cleanup grace. No second process
        # is allowed to inject an unscoped "cleanup" release.
        _abandon_helper(child, may_own_control=position is not None)
        raise ContractError('Native helper deadline exceeded; release is unconfirmed') from exc
    except BaseException:
        _abandon_helper(child, may_own_control=position is not None)
        raise
    if child.returncode or len(raw) > 16384:
        raise ContractError('Native helper unavailable or completion uncertain')
    try: result = json.loads(raw)
    except (ValueError, TypeError) as exc: raise ContractError('Invalid native helper result') from exc
    if not isinstance(result, dict): raise ContractError('Invalid native helper envelope')
    return result


def _main():
    def interrupted(signum, frame):
        raise InterruptedError('Native helper interrupted')
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    native = None
    try:
        raw = sys.stdin.buffer.read(16385)
        if len(raw) > 16384: raise ContractError('Native request exceeds budget')
        payload = json.loads(raw); validate_target(payload['target'])
        if time.monotonic() >= payload['deadline']: raise ContractError('Expired native request')
        native = X11(payload['display'])
        if payload['position'] is None:
            native.grab()
            try: result = native.inspect(payload['target'])
            finally: native.ungrab(); native.sync()
        else:
            result = perform_gesture(native, payload['target'], payload['position'], payload['hold_ms'],
                                     deadline=payload['deadline'])
        sys.stdout.buffer.write(canonical(result)); sys.stdout.buffer.flush()
        return 0
    except Exception:
        return 2
    finally:
        if native is not None: native.close()


if __name__ == '__main__':
    raise SystemExit(_main() if sys.argv[1:] == ['--helper'] else 2)
