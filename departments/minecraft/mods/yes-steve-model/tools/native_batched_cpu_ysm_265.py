"""Optional own-byte-tested batching; no existing backend is replaced.

Only emu_start calls are batched. Every native instruction still saves a CPU
context and journals stores. A following code hook validates the previous
instruction's destination BEFORE committing its writes. Models always execute
outside Unicorn, exactly once, with the legacy model-failure semantics.
"""
import threading
import time
from unicorn import UcError, UC_PROT_EXEC
from native_unicorn_guarded_ysm_265 import GuardedCPU, ModelHalt, REGS, FLAG_BITS, RETURN, SP
from native_jni_fixture_ysm_265 import JniGuardedCPU


class BatchedMixin:
    batch_size = 256
    trace_instructions = True

    def emit(self, *parts):
        if parts and parts[0] == 'INS' and not self.trace_instructions:
            return
        return super().emit(*parts)

    def _begin_instruction(self):
        self._batch_context = self.uc.context_save()
        self.journal = []
        self.writes = []
        self.pending = None
        self.return_fetch = False
        self.current_raw = b''

    def _commit_native(self, next_pc=None):
        nxt = self.reg('RIP') if next_pc is None else next_pc
        if self.returned_to_sentinel():
            for a, n in self.writes:
                self.commit_write(a, n)
            self.completed += 1
            self._batch_context = None
            self.fail('ENTRY_RETURN', nxt)
            return
        if not self.code_allowed(nxt):
            self.fail('EXTERNAL_OR_NULL_TARGET', nxt)
            return
        for a, n in self.writes:
            self.commit_write(a, n)
        self.completed += 1
        self._batch_context = None

    def _code(self, uc, address, size, user):
        # The prior transaction remains live until this target is validated.
        # In particular CALL's stack store must not commit on an invalid target.
        if self._batch_context is not None:
            if self.timed_out and not self.stop:
                self.fail('ENGINE_TIMEOUT', self.pc)
            if self.stop:
                return
            # Unicorn may replay a self-modifying store when it invalidates
            # the current translation block. count=1 exits at that boundary;
            # continuing in the same emu_start can apply a store legacy did not.
            # End the batch after ANY store to an executable image page.
            code_write = bool(self.writes) and any(self.pages.get(page, 0) & UC_PROT_EXEC
                             for a, n in self.writes
                             for page in range(a & ~4095, (a+n+4095) & ~4095, 4096))
            self._commit_native(address)
            if self.stop:
                return
            if code_write:
                self._batch_boundary = True
                uc.emu_stop()
                return
        self.pc = address
        if self.attempted >= self.limit:
            self.fail('INSTRUCTION_BUDGET', address)
            return
        if time.monotonic() > self.deadline:
            self.fail('TIME_BUDGET', address)
            return
        self._begin_instruction()
        # Outer MRO wrapper also intercepts JNI and callback gateway hooks.
        return super()._code(uc, address, size, user)

    def run(self, entry):
        if not isinstance(self.batch_size, int) or not 1 <= self.batch_size <= 65536:
            raise ValueError('Batch size must be an integer from 1 to 65536')
        self.reg('RIP', entry)
        self.deadline = time.monotonic() + self.seconds
        self.timed_out = False
        self._batch_context = None

        def timed_out():
            self.timed_out = True
            self.uc.emu_stop()

        timer = threading.Timer(self.seconds, timed_out)
        timer.daemon = True
        timer.start()
        try:
            while not self.stop:
                self.pc = self.reg('RIP')
                if self.attempted >= self.limit:
                    self.fail('INSTRUCTION_BUDGET', self.pc)
                    break
                if time.monotonic() > self.deadline:
                    self.fail('TIME_BUDGET', self.pc)
                    break
                if not self.code_allowed(self.pc):
                    self.fail('EXTERNAL_OR_NULL_TARGET', self.pc)
                    break
                self.pending = None
                self.return_fetch = False
                self._batch_boundary = False
                try:
                    self.uc.emu_start(self.pc, 0, count=min(self.batch_size, self.limit-self.attempted))
                except UcError as e:
                    if not self.stop and not self.return_fetch:
                        self.fail('ENGINE_EXCEPTION:' + str(e), self.pc)
                if not self.stop and self.timed_out:
                    self.fail('ENGINE_TIMEOUT', self.pc)
                if self.stop:
                    if self._batch_context is not None:
                        self.rollback(self._batch_context)
                        self._batch_context = None
                    break
                if self.pending:
                    # Legacy models are prevalidated, not native transactions:
                    # ModelHalt intentionally does not undo model-side state.
                    self._batch_context = None
                    try:
                        self.model(self.pending)
                    except ModelHalt:
                        break
                    if self.reg('RIP') == RETURN and self.reg('RSP') == SP+8:
                        self.completed += 1
                        self.fail('ENTRY_RETURN', RETURN)
                        break
                    if not self.stop:
                        self.completed += 1
                elif self._batch_context is not None:
                    self._commit_native()
                    if self.stop and self._batch_context is not None:
                        self.rollback(self._batch_context)
                        self._batch_context = None
                elif self._batch_boundary:
                    continue
                else:
                    # A return without a code hook is not a completed instruction.
                    self.fail('ENGINE_NO_INSTRUCTION', self.pc)
        finally:
            timer.cancel()
            timer.join(timeout=1)
        self._batch_report()
        return self.stop

    def _batch_report(self):
        fields = [('attempted',self.attempted),('completed',self.completed),('rollbacks',self.rollback_count),('modeled_copy_steps',self.modeled_copies),('opaque_byte_copies',self.opaque_copies),('virtual_clock_reads',self.clock_reads),('virtual_malloc_calls',self.malloc_calls),('heap_write_events',self.heap_writes),('virtual_fopen_calls',self.fopen_calls),('virtual_fgets_calls',self.fgets_calls),('virtual_fclose_calls',self.fclose_calls),('virtual_cpuid_calls',self.cpuid_calls),('virtual_protection_result_calls',self.protection_calls),('virtual_platform_calls',self.platform_calls),('virtual_dladdr_calls',self.dladdr_calls),('crc_blocks',self.crc_blocks),('crc_iterations',self.crc_iterations),('crc_logical_instructions',self.crc_logical_steps)]
        self.emit('COUNTS', *(f'{k}={v}' for k,v in fields))
        for name in (*REGS, *FLAG_BITS):
            self.emit('STOP_REGISTER', name, f'{self.reg(name):x}')
        self.report_preservation()


class BatchedGuarded(BatchedMixin, GuardedCPU):
    """Minimal guarded backend for independent own-byte fixtures."""


class BatchedJni(BatchedMixin, JniGuardedCPU):
    """Opt-in full JNI stack. Does not enable or configure any model itself."""
