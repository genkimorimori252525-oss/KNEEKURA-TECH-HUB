"""Small synchronous subprocess adapter, not a scheduler or shell service."""
from __future__ import annotations
import os
import signal
import subprocess
import tempfile
import time
from pathlib import Path
from .storage import ContractError


def clean_environment(extra: dict[str,str] | None = None) -> dict[str,str]:
    env = {k:v for k,v in os.environ.items() if k not in
           {'JAVA_TOOL_OPTIONS','_JAVA_OPTIONS','JDK_JAVA_OPTIONS','CLASSPATH','GRADLE_OPTS'} }
    env['LC_ALL'] = 'C'
    if extra:
        if any(not isinstance(k,str) or not isinstance(v,str) for k,v in extra.items()):
            raise ContractError('Environment entries must be strings')
        env.update(extra)
    return env


def run_process(argv: list[str], cwd: Path | str, *, timeout: float = 300,
                max_output_bytes: int = 8*1024*1024, env: dict | None = None) -> dict:
    """Only explicit callers invoke this; reads never dispatch a subprocess.

    Logs are bounded. Timeout/output-limit is not a successful completion even
    when the OS happened to observe exit 0. Child process groups are terminated.
    """
    if (not isinstance(argv,list) or not argv or any(not isinstance(a,str) or '\x00' in a for a in argv)
            or isinstance(timeout,bool) or not isinstance(timeout,(int,float)) or not 0<timeout<=7200
            or type(max_output_bytes) is not int or not 1<=max_output_bytes<=256*1024*1024):
        raise ContractError('Invalid bounded process request')
    started = time.monotonic(); timed_out=False; limited=False
    with tempfile.TemporaryFile() as output:
        process = subprocess.Popen(argv,cwd=str(cwd),stdin=subprocess.DEVNULL,
                                   stdout=output,stderr=subprocess.STDOUT,shell=False,
                                   env=clean_environment(env),start_new_session=os.name!='nt')
        try:
            while process.poll() is None:
                timed_out = time.monotonic()-started > timeout
                limited = os.fstat(output.fileno()).st_size > max_output_bytes
                if timed_out or limited: break
                time.sleep(0.02)
        finally:
            if os.name != 'nt':
                # The parent may already have exited while a daemonized child
                # still owns our process group and log descriptor.
                try: os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError: pass
            elif process.poll() is None:
                subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],
                               stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False,timeout=10)
                if process.poll() is None: process.kill()
            process.wait()
        size = os.fstat(output.fileno()).st_size
        limited = limited or size>max_output_bytes
        output.seek(0); data = output.read(max_output_bytes)
    return {'completed':not timed_out and not limited, 'exit_code':process.returncode,
            'timed_out':timed_out,'output_limited':limited, 'stdout':data,
            'output_bytes_observed':size, 'elapsed_seconds':time.monotonic()-started,
            'execution_layer':'LOCAL_SUBPROCESS_NOT_GAME_ATTESTATION'}
