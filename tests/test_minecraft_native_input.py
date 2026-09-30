"""Deterministic native-boundary fixtures, explicitly not live input acceptance."""
import copy
import importlib
import os
import time

import pytest

from kneekura_tech_hub.minecraft.storage import ContractError


def api():
    try:
        return importlib.import_module('kneekura_tech_hub.minecraft.native_input')
    except ImportError:
        pytest.fail('Selected native X11 input driver is not implemented')


class NativeFixture:
    def __init__(self):
        self.calls = []
        self.focus = True
        self.held = False
        self.pointer_target = True
        self.failure = None

    def grab(self): self.calls.append('grab')
    def ungrab(self): self.calls.append('ungrab')
    def close(self): self.calls.append('close')
    def inspect(self, target):
        self.calls.append('inspect')
        if not self.focus: raise ContractError('Wrong focus')
        return {'client_size': [640, 480], 'foreground': True}
    def any_held(self): return self.held
    def move(self, target, position): self.calls.append(('move', position))
    def pointer_on_target(self, target): return self.pointer_target
    def button(self, pressed):
        self.calls.append(('button', pressed))
        if pressed and self.failure: raise self.failure
    def sync(self): self.calls.append('sync')
    def confirm_owner(self, target): self.calls.append('confirm_owner')
    def send_button(self, target, position, pressed, *, deadline): self.button(pressed)


def test_native_gesture_rechecks_scope_under_grab_and_releases_once():
    native = NativeFixture()
    result = api().perform_gesture(native, {'client_size': [640, 480]}, [300, 200], 20,
                                   deadline=time.monotonic()+1)
    assert native.calls[0:2] == ['grab', 'inspect']
    assert [c for c in native.calls if isinstance(c, tuple) and c[0] == 'button'] == [('button', True), ('button', False)]
    assert native.calls[-2:] == ['ungrab', 'sync']
    assert result == {'pressed': True, 'released': True}


@pytest.mark.parametrize('failure', ['focus', 'held', 'viewport', 'occluded'])
def test_native_guard_failure_never_presses(failure):
    native = NativeFixture(); target = {'client_size': [640, 480]}
    if failure == 'focus': native.focus = False
    if failure == 'held': native.held = True
    if failure == 'viewport': target['client_size'] = [800, 600]
    if failure == 'occluded': native.pointer_target = False
    with pytest.raises(ContractError):
        api().perform_gesture(native, target, [300, 200], 20, deadline=time.monotonic()+1)
    assert ('button', True) not in native.calls
    assert ('button', False) not in native.calls
    assert 'ungrab' in native.calls


def test_native_uncertain_press_still_releases_owned_control_under_grab():
    native = NativeFixture(); native.failure = OSError('native write uncertain')
    with pytest.raises(OSError):
        api().perform_gesture(native, {'client_size': [640, 480]}, [300, 200], 20,
                              deadline=time.monotonic()+1)
    assert native.calls.index(('button', False)) < len(native.calls)-2
    assert [c for c in native.calls if c == ('button', False)] == [('button', False)]


def test_native_invalid_point_and_hold_rejected_without_native_contact():
    for point, hold in [([-1, 0], 20), ([640, 0], 20), ([0, 0], 251), ([True, 0], 10)]:
        native = NativeFixture()
        with pytest.raises(ContractError):
            api().perform_gesture(native, {'client_size': [640, 480]}, point, hold,
                                  deadline=time.monotonic()+1)
        assert native.calls == []


def test_native_missing_display_blocks_without_fallback():
    with pytest.raises(ContractError):
        api().native_exchange(':64999', {'process_id': os.getpid(), 'window_id': '42',
                              'process_start': api().process_start(os.getpid()), 'client_size': [640, 480]},
                              deadline=time.monotonic()+2)


def test_native_rejects_remote_display_and_process_identity():
    for display in ['evil:0', 'localhost:0', ':0;sh', '', ':99999999']:
        with pytest.raises(ContractError): api().validate_display(display)
    assert api().validate_display(':0') == ':0'
    assert api().validate_display(':1.0') == ':1.0'
    with pytest.raises(ContractError): api().process_start(True)


def test_observer_reports_real_linux_process_start_identity(tmp_path):
    import shutil
    import subprocess
    from pathlib import Path
    source = Path('departments/minecraft/mod-ai/forge-observer/src/main/java/org/kneekura/observer/LinuxClientIdentity.java')
    assert source.is_file(), 'Observer native PID reuse defense is missing'
    peer = tmp_path/'IdentityPeer.java'
    peer.write_text('''import org.kneekura.observer.LinuxClientIdentity;
public class IdentityPeer { public static void main(String[] args) throws Exception {
System.out.println(ProcessHandle.current().pid()+":"+LinuxClientIdentity.processStart());
System.out.flush(); Thread.sleep(5000);
}}''')
    subprocess.run([shutil.which('javac'),'--release','17','-d',str(tmp_path),str(source),str(peer)], check=True, capture_output=True)
    process = subprocess.Popen([shutil.which('java'),'-cp',str(tmp_path),'IdentityPeer'], stdout=subprocess.PIPE, text=True)
    try:
        pid, start = process.stdout.readline().strip().split(':')
        assert int(pid) == process.pid
        assert api().process_start(int(pid)) == start
    finally:
        process.terminate(); process.wait(timeout=5)


def test_client_probe_exposes_authenticated_native_handle_and_local_scope():
    from pathlib import Path
    text = Path('departments/minecraft/mod-ai/forge-observer/src/main/java/org/kneekura/observer/ClientProbe.java').read_text()
    assert 'GLFWNativeX11.glfwGetX11Window' in text
    assert 'LinuxClientIdentity.processStart()' in text
    assert '"native_input"' in text and '"client_size"' in text and 'GLFW.GLFW_FOCUSED' in text


def test_abandoned_targeted_helper_gets_bounded_scoped_cleanup_and_is_reaped(tmp_path):
    import subprocess
    import sys
    path = tmp_path/'released.txt'
    child = subprocess.Popen([sys.executable, '-c',
        'import pathlib,signal,sys,time; signal.signal(signal.SIGTERM,lambda *_: (pathlib.Path(sys.argv[1]).write_text("released"),sys.exit(0))); print("ready",flush=True); time.sleep(30)', str(path)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    assert child.stdout.readline().strip() == b'ready'
    thread = api()._abandon_helper(child, may_own_control=True)
    thread.join(timeout=2)
    assert not thread.is_alive() and child.returncode == 0
    assert path.read_text() == 'released'
    assert child.stdout.closed


def test_abandoned_read_only_helper_can_be_stopped_and_reaped():
    import subprocess
    import sys
    child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    thread = api()._abandon_helper(child, may_own_control=False)
    thread.join(timeout=2)
    assert not thread.is_alive() and child.returncode is not None
    assert child.stdout.closed


def test_physical_pointer_race_cannot_retarget_native_button_events():
    class PointerRace(NativeFixture):
        def __init__(self):
            super().__init__(); self.pointer = 'game'; self.deliveries = []
        def pointer_on_target(self, target):
            sampled = self.pointer == 'game'
            self.pointer = 'other-app'  # Physical motion is NOT blocked by XGrabServer.
            return sampled
        def button(self, pressed):
            self.deliveries.append((self.pointer, pressed))
        def send_button(self, target, position, pressed, *, deadline):
            self.deliveries.append((target['window_id'], pressed))
    native = PointerRace()
    api().perform_gesture(native, {'window_id':'game', 'client_size':[640,480]}, [300,200], 1,
                          deadline=time.monotonic()+1)
    assert native.deliveries == [('game', True), ('game', False)]


def test_blocking_preflight_cannot_mutate_after_native_deadline():
    native = NativeFixture()
    def slow_grab():
        native.calls.append('grab'); time.sleep(.16)
    native.grab = slow_grab
    with pytest.raises(ContractError):
        api().perform_gesture(native, {'client_size':[640,480]}, [300,200], 1,
                              deadline=time.monotonic()+.1)
    assert not any(isinstance(c, tuple) for c in native.calls)


def test_unresponsive_targeted_helper_is_killed_within_cleanup_budget():
    import subprocess
    import sys
    child = subprocess.Popen([sys.executable, '-c',
        'import signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); print("ready",flush=True); time.sleep(30)'],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    assert child.stdout.readline().strip() == b'ready'
    started = time.monotonic()
    thread = api()._abandon_helper(child, may_own_control=True)
    thread.join(timeout=2)
    assert not thread.is_alive() and child.returncode is not None
    assert time.monotonic()-started < 1.5


def test_targeted_xevent_addresses_only_exact_window_creator():
    import ctypes
    module = api()
    sends = []
    class Xlib:
        def XDefaultRootWindow(self, display): return 99
        def XTranslateCoordinates(self, display, source, root, x, y, rx, ry, child):
            ctypes.cast(rx,ctypes.POINTER(ctypes.c_int))[0] = 100+x
            ctypes.cast(ry,ctypes.POINTER(ctypes.c_int))[0] = 200+y
            return 1
        def XSendEvent(self, display, window, propagate, mask, value):
            event = ctypes.cast(value,ctypes.POINTER(module.XEvent)).contents.button
            sends.append((window,propagate,mask,event.type,event.window,event.button,event.x,event.y,event.state))
            return 1
    native = module.X11.__new__(module.X11); native.x = Xlib(); native.d = 123
    target = {'window_id':'42', 'client_size':[640,480]}
    native.send_button(target,[300,200],True,deadline=time.monotonic()+1)
    native.send_button(target,[300,200],False,deadline=time.monotonic()+1)
    assert sends == [(42,0,0,4,42,3,300,200,0),(42,0,0,5,42,3,300,200,1024)]


def test_slow_coordinate_translation_cannot_send_after_deadline():
    module = api()
    class Xlib:
        def XDefaultRootWindow(self, display): return 99
        def XTranslateCoordinates(self, *args): time.sleep(.12); return 1
        def XSendEvent(self, *args): pytest.fail('Native send after deadline')
    native = module.X11.__new__(module.X11); native.x=Xlib(); native.d=123
    with pytest.raises(ContractError):
        native.send_button({'window_id':'42'},[1,2],True,deadline=time.monotonic()+.05)


def test_expired_translation_does_not_create_a_release_without_a_press():
    import ctypes
    module=api(); sends=[]
    class Xlib:
        def XDefaultRootWindow(self, display): return 99
        def XTranslateCoordinates(self, *args): time.sleep(.16); return 1
        def XSendEvent(self,*args): sends.append(args); return 1
    x11=module.X11.__new__(module.X11); x11.x=Xlib(); x11.d=123
    native=NativeFixture(); native.send_button=x11.send_button
    with pytest.raises(ContractError):
        module.perform_gesture(native,{'window_id':'42','client_size':[640,480]},[320,240],1,
                               deadline=time.monotonic()+.1)
    assert sends==[]
