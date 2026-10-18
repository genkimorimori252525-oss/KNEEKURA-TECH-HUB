#!/usr/bin/env python3
"""Review-only draft. CLI refuses the supplied NOT_EXECUTABLE lock.
No target invocation is performed by importing this module or by its fake tests.
"""
import hashlib
import io
import json
import os
from pathlib import Path
import re
import selectors
import signal
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import urllib.request
import urllib.error
import uuid
import zipfile

class Blocked(RuntimeError):
    """Public reporting uses only fixed stage/result codes, never this text."""

JAVA = '/usr/lib/jvm/msopenjdk-17/bin/java'
ARGS = 'libraries/net/minecraftforge/forge/1.20.1-47.4.0/unix_args.txt'
ARGS_SHA = '217db97d019a510fe29b299c2cd8496a8659033bffd416627137a4b59727c01e'
INSTALLER_URL = 'https://maven.minecraftforge.net/net/minecraftforge/forge/1.20.1-47.4.0/forge-1.20.1-47.4.0-installer.jar'
VERSION_URL = 'https://piston-meta.mojang.com/v1/packages/a5cf661d31d9dfcd3d1645be80f43954f63f63b0/1.20.1.json'
YSM_URL = 'https://cdn.modrinth.com/data/86xjpqqS/versions/Zqooxsd2/ysm-2.6.5-forge%2Bmc1.20.1-release.jar'
POLICY = 'Official pinned Forge installer in isolated bridge staging without YSM or credentials; verify declared installed library and processor output checksums; reject unknown launch files; freeze installed libraries before network-none control and YSM; no hermetic or independently enforced bootstrap-egress claim.'
MAX_LOG = 8 * 1024 * 1024
READY = re.compile(rb'Done \([0-9.]+s\)! For help, type "help"')
# EXPECTED_LOCK is generated from the review schema below, not loaded from untrusted input.
EXPECTED_LOCK = {'format': 'kneekura.ysm-runtime-lock.v1', 'status': 'REVIEWED_COMPLETE', 'unresolved': [], 'repository': 'genkimorimori252525-oss/KNEEKURA-TECH-HUB', 'visibility': 'public', 'harness_sha256': None, 'runner': 'ubuntu-24.04', 'platform': 'linux/amd64', 'runtime': {'vendor': 'Microsoft Build of OpenJDK', 'java_major': 17, 'image_repository': 'mcr.microsoft.com/openjdk/jdk', 'platform_manifest_sha256': 'b6507c825e40508fc9cbb5645c48396a77b71775620c6ce95dfe1c65da7e8549', 'config_sha256': '93c70e380d5945f4ad879fab2e195df2714ce3acb00cc70cbc0ec9b2f0513efc', 'publisher_metadata_url': 'https://learn.microsoft.com/en-us/java/openjdk/containers', 'preflight': {'launcher': '/usr/lib/jvm/msopenjdk-17/bin/java', 'require_major': 17, 'require_vendor_pattern': '.*Microsoft.*', 'require_nonempty_build': True, 'record_full_version_and_release_metadata': True, 'assert_control_and_ysm_identical': True, 'run_before_forge_or_ysm': True}}, 'versions': {'minecraft': '1.20.1', 'forge': '47.4.0', 'ysm': '2.6.5-forge+mc1.20.1'}, 'ysm_jar_sha256': '25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f', 'ysm_native_sha256': '15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22', 'actions': {'checkout_commit': '11d5960a326750d5838078e36cf38b85af677262'}, 'isolation': {'network': 'none', 'uid': 1001, 'read_only_root': True, 'drop_all_capabilities': True, 'no_new_privileges': True, 'memory_mib': 4096, 'cpus': 2, 'pids': 256, 'core_dumps': False}, 'output': {'mode': 'sanitized_job_logs_only', 'max_bytes': 65536, 'artifacts': False, 'cache': False}, 'limits': {'job_minutes': 25, 'startup_seconds': 180, 'steady_seconds': 20, 'shutdown_seconds': 30}, 'bootstrap': {'mode': 'trusted_official_installer_one_cohort_snapshot', 'forge_installer_sha256': 'f3f57465e2cbdc328193f77ba7f0c94cb64405f31ed556753d9275e8bdc06e2c', 'minecraft_version_manifest_sha256': 'e50169ba5c14ce07c82fb638118449c24f5eb5082e95005c480917aae3635be3', 'minecraft_server_publisher_sha1': '84194a2f286ef7c14ed7ce0090dba59902951553', 'minecraft_server_bytes': 47791053, 'installer_profile_sha256': 'f9d8985233e26cb1a6744176b1ff49e47d78e5f8d81c5027c967dcbcbfdaa9f4', 'reviewed_bootstrap_policy_sha256': 'becece2c6b95a0cefb14f60f3b4bff79d45566a151cdd6d55889bf15331e393a', 'verify_every_declared_checksum': True, 'reject_unknown_launch_inputs': True, 'installer_network': 'bridge_egress_trusted_official_installer', 'no_ysm_or_credentials_in_staging': True, 'requires_bundled_approval': True, 'frozen_snapshot_sha256_recorded_before_both_runs': True, 'same_snapshot_for_control_and_ysm': True, 'independent_hermetic_closure_claimed': False, 'bootstrap_egress_independently_enforced': False, 'reject_unexplained_installed_launch_files': True}}


# Only these authored values may reach public diagnostics. Never publish exception text.
STAGES = frozenset(('VALIDATE','HOST_PLATFORM','PREPARE','DOCKER_SECURITY',
    'ACQUIRE_INSTALLER','ACQUIRE_GAME_METADATA','IMAGE_PULL','IMAGE_VERIFY',
    'JVM_PREFLIGHT','INSTALLER','SNAPSHOT_VERIFY','ACQUIRE_YSM',
    'CONTROL_SETUP','CONTROL_RUN','YSM_SETUP','YSM_RUN','COMPLETE'))
BLOCKED_CODES = {
    'default seccomp unavailable':'SECCOMP_UNAVAILABLE',
    'command failed':'COMMAND_FAILED', 'command timeout':'COMMAND_TIMEOUT',
    'command output limit':'COMMAND_OUTPUT_LIMIT',
    'redirect not approved':'DOWNLOAD_REDIRECT', 'download size mismatch':'DOWNLOAD_SIZE',
    'bootstrap digest mismatch':'BOOTSTRAP_DIGEST', 'image identity mismatch':'IMAGE_IDENTITY',
    'JVM/network preflight failed':'JVM_PREFLIGHT_FAILED', 'JVM identity/build mismatch':'JVM_IDENTITY',
    'actual isolation mismatch':'ISOLATION_MISMATCH', 'seccomp disabled':'SECCOMP_DISABLED',
    'runner UID mismatch':'RUNNER_UID', 'host platform mismatch':'HOST_PLATFORM',
    'runner cancellation':'CANCELLED', 'publisher checksum mismatch':'PUBLISHER_CHECKSUM',
    'unknown installed launch file':'UNKNOWN_LAUNCH_FILE', 'missing launch dependency':'MISSING_LAUNCH_INPUT',
    'missing declared processor output':'MISSING_PROCESSOR_OUTPUT',
    'missing data-declared output':'MISSING_DECLARED_OUTPUT',
    'missing published mappings':'MISSING_MAPPINGS', 'snapshot changed':'SNAPSHOT_CHANGED',
    'YSM mismatch':'YSM_DIGEST', 'native mismatch':'NATIVE_DIGEST',
    'private log byte budget exceeded':'PRIVATE_LOG_LIMIT'}
ERROR_CODES = frozenset(BLOCKED_CODES.values()) | frozenset(('POLICY_REJECTED','INVALID_JSON',
    'HTTP_FAILURE','NETWORK_FAILURE','TIMEOUT','MISSING_FILE','PERMISSION_DENIED',
    'IO_FAILURE','MISSING_FIELD','DATA_SHAPE','INVALID_ARCHIVE','INTERNAL_ERROR'))


def error_code(exc):
    if isinstance(exc,Blocked):return BLOCKED_CODES.get(str(exc),'POLICY_REJECTED')
    if isinstance(exc,json.JSONDecodeError):return 'INVALID_JSON'
    if isinstance(exc,urllib.error.HTTPError):return 'HTTP_FAILURE'
    if isinstance(exc,urllib.error.URLError):return 'NETWORK_FAILURE'
    if isinstance(exc,(TimeoutError,subprocess.TimeoutExpired)):return 'TIMEOUT'
    if isinstance(exc,FileNotFoundError):return 'MISSING_FILE'
    if isinstance(exc,PermissionError):return 'PERMISSION_DENIED'
    if isinstance(exc,OSError):return 'IO_FAILURE'
    if isinstance(exc,KeyError):return 'MISSING_FIELD'
    if isinstance(exc,(TypeError,ValueError,IndexError)):return 'DATA_SHAPE'
    if isinstance(exc,zipfile.BadZipFile):return 'INVALID_ARCHIVE'
    return 'INTERNAL_ERROR'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def validate(raw, env, source):
    """Pure validation: before mkdir, acquisition, container materialization or EULA."""
    if env.get('ALLOW_ORIGINAL_YSM_EXECUTION') != 'true' or env.get('ACCEPT_MINECRAFT_EULA') != 'true':
        raise Blocked('both explicit consents required')
    commit = env.get('EXPECTED_COMMIT', '')
    if not re.fullmatch('[0-9a-f]{40}', commit) or commit != env.get('GITHUB_SHA'):
        raise Blocked('commit mismatch')
    required = {'GITHUB_REPOSITORY':'genkimorimori252525-oss/KNEEKURA-TECH-HUB',
                'GITHUB_REF':'refs/heads/main', 'GITHUB_EVENT_NAME':'workflow_dispatch',
                'REPOSITORY_VISIBILITY':'public', 'RUNNER_ENVIRONMENT':'github-hosted',
                'RUNNER_OS':'Linux', 'RUNNER_ARCH':'X64', 'ImageOS':'ubuntu24'}
    if any(env.get(k) != v for k, v in required.items()):
        raise Blocked('context mismatch')
    if digest(raw) != env.get('APPROVED_LOCK_SHA256'):
        raise Blocked('lock digest mismatch')
    # duplicate keys are rejected, rather than silently using the last occurrence.
    def unique(pairs):
        out = {}
        for k, v in pairs:
            if k in out: raise Blocked('duplicate JSON key')
            out[k] = v
        return out
    lock = json.loads(raw, object_pairs_hook=unique)
    expected = json.loads(json.dumps(EXPECTED_LOCK))
    expected['harness_sha256'] = digest(source)
    if lock != expected: raise Blocked('incomplete or changed reviewed lock')
    return lock


def sandbox(name, uid, network):
    if network not in ('none', 'bridge') or not re.fullmatch('[a-z0-9-]+', name):
        raise Blocked('invalid sandbox identity')
    return ['docker','create','--name',name,'--label','ysm.run='+name.rsplit('-',1)[0],
            '--platform=linux/amd64','--user',f'{uid}:{uid}', '--read-only',
            '--network='+network,'--cap-drop=ALL','--security-opt=no-new-privileges',
            '--memory=4g','--memory-swap=4g','--cpus=2','--pids-limit=256',
            '--ulimit=core=0','--log-driver=none','--ipc=private',
            '--tmpfs','/tmp:rw,exec,nosuid,nodev,size=536870912,mode=1777',
            '--env','HOME=/tmp','--env','TMPDIR=/tmp']


def outcome(code, timed_out, oom, ready):
    if oom: return 'OOM'
    if timed_out: return 'TIMEOUT'
    if code == 137: return 'CRASH_137'
    if code != 0: return 'NONZERO_EXIT'
    return 'PASS' if ready else 'NOT_READY'


def summary(report):
    # No target strings, paths, logs, exception messages or arbitrary keys are emitted.
    out = {'format':'ysm-server-smoke.v1', 'client_render':'NOT_RUN',
           'native_load':'NOT_OBSERVED','jni_registration':'NOT_OBSERVED',
           'worker_queue_execution':'NOT_OBSERVED','worker_drain':'NOT_OBSERVED'}
    if report.get('stage') in STAGES:out['stage']=report['stage']
    if report.get('error_code') in ERROR_CODES:out['error_code']=report['error_code']
    for phase in ('control','ysm'):
        r = report.get(phase, {})
        allowed = ('PASS','NOT_RUN','NOT_READY','CRASH_137','TIMEOUT','OOM','NONZERO_EXIT','BLOCKED')
        out[phase] = {'result':r.get('result') if r.get('result') in allowed else 'BLOCKED'}
        for key in ('exit_code','elapsed_seconds','ready_seconds','stop_seconds'):
            value = r.get(key)
            if type(value) in (int, float) and 0 <= value <= 100000:
                out[phase][key] = value
        for key in ('oom','timed_out','started'):
            if type(r.get(key)) is bool: out[phase][key] = r[key]
    for key in ('snapshot_sha256','lock_sha256','commit','harness_sha256'):
        value = report.get(key, '')
        if isinstance(value,str) and re.fullmatch('[0-9a-f]{40}|[0-9a-f]{64}',value): out[key] = value
    version=report.get('java_runtime_version','')
    if isinstance(version,str) and re.fullmatch('[A-Za-z0-9.+_-]{1,80}',version):
        out['java_runtime_version']=version;out['java_vendor']='Microsoft'
    if report.get('cleanup') in ('PASS','FAILED'):out['cleanup']=report['cleanup']
    return json.dumps(out, sort_keys=True, allow_nan=False)


def jvm_identity(raw):
    release=re.search(rb'^JAVA_RUNTIME_VERSION="([A-Za-z0-9.+_-]{1,80})"$',raw,re.M)
    runtime=re.search(rb'^\s*java.runtime.version = ([A-Za-z0-9.+_-]{1,80})$',raw,re.M)
    if (b'IMPLEMENTOR="Microsoft"' not in raw or not re.search(rb'^JAVA_VERSION="17\.[^"\n]+"$',raw,re.M)
        or not re.search(rb'^\s*java.vendor = Microsoft$',raw,re.M)
        or not release or not runtime or release[1]!=runtime[1]):
        raise Blocked('JVM identity/build mismatch')
    return release[1].decode('ascii')


def snapshot(root):
    rows=[]
    for p in sorted(root.rglob('*')):
        if p.is_symlink(): raise Blocked('symlink in snapshot')
        if p.is_dir(): continue
        if not p.is_file() or p.stat().st_nlink != 1: raise Blocked('nonregular snapshot member')
        rows.append([str(p.relative_to(root)),p.stat().st_size,digest(p.read_bytes())])
    if not rows: raise Blocked('empty snapshot')
    return digest(json.dumps(rows,separators=(',',':')).encode())


def run_pair(run, report=None):
    if report is None:report={}
    report.update(control={'result':'BLOCKED','started':False},ysm={'result':'NOT_RUN','started':False})
    report['control']=run('control')
    if report['control']['result']=='PASS':
        report['ysm']={'result':'BLOCKED','started':False}
        report['ysm']=run('ysm')
    return report


class IO:
    """Inject this boundary in tests. Never inherits runner tokens into child commands."""
    def __init__(self):
        self.env = {'PATH':'/usr/bin:/bin', 'HOME':'/tmp', 'LANG':'C.UTF-8', 'DOCKER_CONFIG':'/nonexistent'}

    def command(self, argv, timeout=60):
        # Commands here have small, bounded trusted output. Game output uses stream().
        p=subprocess.Popen(argv,env=self.env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        sel=selectors.DefaultSelector();sel.register(p.stdout,selectors.EVENT_READ)
        data=bytearray();deadline=time.monotonic()+timeout
        try:
            while sel.get_map():
                if time.monotonic()>deadline:raise Blocked('command timeout')
                for key,_ in sel.select(.1):
                    chunk=os.read(key.fileobj.fileno(),65536)
                    if not chunk:sel.unregister(key.fileobj);continue
                    data.extend(chunk)
                    if len(data)>MAX_LOG:raise Blocked('command output limit')
            return p.wait(timeout=5), bytes(data)
        finally:
            sel.close()
            if p.poll() is None:p.kill();p.wait(timeout=5)
            p.stdout.close()

    def download(self, url, size):
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self,*a,**k): raise Blocked('redirect not approved')
        with urllib.request.build_opener(NoRedirect).open(url,timeout=30) as r:
            data=r.read(size+1)
        if len(data)!=size: raise Blocked('download size mismatch')
        return data

    def stream(self, argv, name, log_path, startup=180, steady=20, shutdown=30):
        start=time.monotonic();ready_at=None;stop_at=None;timed=False;total=0;tail=b''
        p=subprocess.Popen(argv, env=self.env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        sel=selectors.DefaultSelector();sel.register(p.stdout,selectors.EVENT_READ)
        try:
            with log_path.open('xb') as log:
                while p.poll() is None:
                    now=time.monotonic()
                    if (ready_at is None and now-start>startup) or (stop_at is not None and now-stop_at>shutdown):
                        timed=True;break
                    if ready_at is not None and stop_at is None and now-ready_at>=steady:
                        try:p.stdin.write(b'stop\n');p.stdin.flush()
                        except BrokenPipeError:break
                        stop_at=now
                    for key,_ in sel.select(.1):
                        chunk=os.read(key.fileobj.fileno(),65536)
                        if not chunk:continue
                        total+=len(chunk)
                        if total>MAX_LOG:raise Blocked('private log byte budget exceeded')
                        log.write(chunk);tail=(tail+chunk)[-65536:]
                        if ready_at is None and READY.search(tail):ready_at=time.monotonic()
            if timed:self.command(['docker','kill',name])
            p.wait(timeout=15)
            _,raw=self.command(['docker','inspect',name]); state=json.loads(raw)[0]['State']
            code=state['ExitCode'];oom=state['OOMKilled']
            ready=ready_at is not None and stop_at is not None
            return {'result':outcome(code,timed,oom,ready),'exit_code':code,'oom':oom,'timed_out':timed,
                    'elapsed_seconds':round(time.monotonic()-start,3),
                    'ready_seconds':round(ready_at-start,3) if ready_at else None,
                    'stop_seconds':round(time.monotonic()-stop_at,3) if stop_at else None}
        finally:
            sel.close()
            if p.poll() is None:
                self.command(['docker','kill',name]);p.kill();p.wait(timeout=10)
            p.stdout.close();p.stdin.close()


def checked(io, argv, timeout=60):
    code,data=io.command(argv,timeout=timeout)
    if code:raise Blocked('command failed')
    return data


def cleanup(io, root, run_id, containers):
    # Inspect all ownership first; never use docker prune or broad label deletion.
    for name in containers:
        _,raw=io.command(['docker','inspect',name])
        if json.loads(raw)[0]['Config'].get('Labels',{}).get('ysm.run')!=run_id:
            raise Blocked('cleanup ownership mismatch')
    for name in containers:checked(io,['docker','rm','--force',name])
    if root.is_symlink() or root.name != 'ysm-smoke-'+run_id or root.parent != Path(tempfile.gettempdir()):
        raise Blocked('cleanup root mismatch')
    shutil.rmtree(root)


def inspect_sandbox(io,name,image,network,mounts):
    d=json.loads(checked(io,['docker','inspect',name]))[0];h=d['HostConfig'];c=d['Config']
    actual={(x['Source'],x['Destination'],x['RW']) for x in d['Mounts'] if x['Type']=='bind'}
    if (h['NetworkMode']!=network or not h['ReadonlyRootfs'] or h['Privileged']
        or h.get('PidMode') in ('host','container') or h.get('IpcMode')!='private'
        or h.get('PortBindings') or c.get('ExposedPorts') or h.get('Devices')
        or h.get('CapAdd') or h.get('CapDrop')!=['ALL']
        or not any(x in h.get('SecurityOpt',[]) for x in ('no-new-privileges','no-new-privileges=true'))
        or h['Memory']!=4*1024**3 or h['MemorySwap']!=4*1024**3
        or h['NanoCpus']!=2*10**9 or h['PidsLimit']!=256
        or c['User']!=f'{os.getuid()}:{os.getuid()}' or c['Image']!=image
        or actual!=set(mounts) or h.get('LogConfig',{}).get('Type')!='none'):
        raise Blocked('actual isolation mismatch')
    tmpfs=h.get('Tmpfs',{})
    if set(tmpfs) != ({'/tmp','/game'} if c.get('WorkingDir')=='/game' else {'/tmp'}):raise Blocked('unexpected tmpfs mounts')
    if c.get('WorkingDir')=='/game' and ('noexec' not in tmpfs['/game'] or 'size=1073741824' not in tmpfs['/game']):raise Blocked('game writable budget missing')
    if any('seccomp=unconfined' in x for x in h.get('SecurityOpt',[])):
        raise Blocked('seccomp disabled')
    if not any(x['Name']=='core' and x['Hard']==0 and x['Soft']==0 for x in h.get('Ulimits',[])):
        raise Blocked('core limit missing')


def acquire(io,root,lock,report=None):
    specs=[('installer.jar',INSTALLER_URL,6056587,lock['bootstrap']['forge_installer_sha256']),
           ('version.json',VERSION_URL,34974,lock['bootstrap']['minecraft_version_manifest_sha256'])]
    for name,url,size,sha in specs:
        if report is not None:report['stage']='ACQUIRE_INSTALLER' if name=='installer.jar' else 'ACQUIRE_GAME_METADATA'
        data=io.download(url,size)
        if digest(data)!=sha:raise Blocked('bootstrap digest mismatch')
        (root/name).write_bytes(data)
    # YSM is deliberately not acquired or mounted until staging has stopped.


def coordinate(value):
    value, sep, extension = value.partition('@')
    extension = extension if sep else 'jar'
    if not re.fullmatch('[a-z0-9]+',extension):raise Blocked('unknown artifact extension')
    parts=value.split(':')
    if len(parts) not in (3,4):raise Blocked('unknown Maven coordinate')
    group,artifact,version=parts[:3]; classifier='-'+parts[3] if len(parts)==4 else ''
    return group.replace('.','/')+'/'+artifact+'/'+version+'/'+artifact+'-'+version+classifier+'.'+extension


def verify_install(stage,installer,metadata,lock):
    """Verify published and declared generated checksums, without inventing derived hashes."""
    with zipfile.ZipFile(installer) as z:
        profile_raw=z.read('install_profile.json')
        if digest(profile_raw)!=lock['bootstrap']['installer_profile_sha256']:raise Blocked('profile mismatch')
        profile=json.loads(profile_raw);version=json.loads(z.read('version.json'))
        if (stage/ARGS).read_bytes()!=z.read('data/unix_args.txt'):raise Blocked('launch args changed')
    known={}
    def add(path,sha,alg='sha1',size=None):
        if path.startswith('/') or '..' in Path(path).parts:raise Blocked('unsafe metadata path')
        previous=known.setdefault(path,[])
        if any(a==alg and h!=sha for h,a,_ in previous):raise Blocked('conflicting published hash')
        previous.append((sha,alg,size))
    for meta in (profile,version,metadata):
        for lib in meta.get('libraries',[]):
            a=lib.get('downloads',{}).get('artifact')
            if a and a.get('sha1') and a.get('path'):add(a['path'],a['sha1'],'sha1',a.get('size'))
    data=profile['data']
    def resolve(v):
        for k,obj in data.items():v=v.replace('{'+k+'}',obj.get('server',''))
        if v.startswith("'") and v.endswith("'"):return v[1:-1]
        if v.startswith('[') and v.endswith(']'):return 'libraries/'+coordinate(v[1:-1])
        return v
    for processor in profile['processors']:
        if 'sides' in processor and 'server' not in processor['sides']:continue
        for path,sha in processor.get('outputs',{}).items():
            path=resolve(path);sha=resolve(sha)
            if not path.startswith('libraries/') or not re.fullmatch('[a-f0-9]{40}',sha):raise Blocked('unknown output checksum')
            if not (stage/path).is_file():raise Blocked('missing declared processor output')
            add(path[len('libraries/'):],sha)
    server=metadata['downloads']['server']
    server_path=stage/'minecraft_server.1.20.1.jar'
    # Official install profile provides the downloaded server path explicitly.
    expected=profile.get('serverJarPath')
    if expected:
        server_path=stage/expected.replace('{LIBRARY_DIR}','libraries').replace('{MINECRAFT_VERSION}','1.20.1')
    if not server_path.is_file():raise Blocked('server jar path unobserved')
    server_bytes=server_path.read_bytes()
    if len(server_bytes)!=lock['bootstrap']['minecraft_server_bytes'] or hashlib.sha1(server_bytes).hexdigest()!=lock['bootstrap']['minecraft_server_publisher_sha1']:
        raise Blocked('official server mismatch')
    add(str(server_path.relative_to(stage/'libraries')),server['sha1'],'sha1',server['size'])
    generated=set()
    for key,obj in data.items():
        path=resolve(obj.get('server',''))
        if path.startswith('libraries/'):
            rel=path[len('libraries/'):];generated.add(rel)
            if key+'_SHA' in data:
                if not (stage/path).is_file():raise Blocked('missing data-declared output')
                add(rel,resolve(data[key+'_SHA']['server']))
    maps=metadata.get('downloads',{}).get('server_mappings')
    if maps and 'MOJMAPS' in data:
        path=resolve(data['MOJMAPS']['server'])
        if not (stage/path).is_file():raise Blocked('missing published mappings')
        add(path[len('libraries/'):],maps['sha1'],'sha1',maps['size'])
    with zipfile.ZipFile(io.BytesIO(server_bytes)) as z:
        for list_name in ('META-INF/libraries.list','META-INF/versions.list'):
            for line in z.read(list_name).decode().splitlines():
                sha,coord,path=line.split('\t')
                # Libraries retain the bundle path; extracted server uses coordinate naming.
                add(path if 'libraries.list' in list_name else resolve(data['MC_UNPACKED']['server'])[len('libraries/'):],sha,'sha256')
    libraries=stage/'libraries'; snapshot(libraries)
    for p in libraries.rglob('*'):
        if not p.is_file():continue
        rel=str(p.relative_to(libraries))
        if rel in known:
            b=p.read_bytes()
            for sha,alg,size in known[rel]:
                if hashlib.new(alg,b).hexdigest()!=sha or (size is not None and len(b)!=size):raise Blocked('publisher checksum mismatch')
        elif rel in generated:
            pass  # Reviewed pinned processor inputs; derived bytes enter the snapshot receipt.
        elif rel in ('net/minecraftforge/forge/1.20.1-47.4.0/unix_args.txt',
                     'net/minecraftforge/forge/1.20.1-47.4.0/win_args.txt'):
            pass
        else:raise Blocked('unknown installed launch file')
    for lib in version.get('libraries',[]):
        artifact=lib.get('downloads',{}).get('artifact')
        if artifact and not (libraries/artifact['path']).is_file():raise Blocked('missing Forge runtime artifact')
    text=(stage/ARGS).read_text()
    for path in re.findall(r'libraries/[^\s:]+',text):
        if not (stage/path).is_file():raise Blocked('missing launch dependency')
    return snapshot(libraries)


def execute(lock, env, io_adapter, report=None):
    """Called only after pure validate(); adapters are injected for offline tests."""
    if report is None:report={}
    report['stage']='PREPARE'
    if os.getuid()!=lock['isolation']['uid']:raise Blocked('runner UID mismatch')
    run_id=uuid.uuid4().hex
    root=Path(tempfile.gettempdir())/('ysm-smoke-'+run_id);root.mkdir(mode=0o700)
    containers=[];image=lock['runtime']['image_repository']+'@sha256:'+lock['runtime']['platform_manifest_sha256']
    if report is None:report={}
    def create(phase,network,mounts,command,workdir='/tmp',interactive=False):
        name=run_id+'-'+phase
        argv=sandbox(name,os.getuid(),network)
        if interactive:argv+=['--interactive']
        if workdir=='/game':argv+=['--tmpfs',f'/game:rw,noexec,nosuid,nodev,size=1073741824,uid={os.getuid()},gid={os.getuid()},mode=0700']
        for src,dst,rw in mounts:argv+=['--mount',f'type=bind,src={src},dst={dst},'+('rw' if rw else 'readonly')]
        argv+=['--workdir',workdir,'--entrypoint',command[0],image,*command[1:]]
        checked(io_adapter,argv);containers.append(name)
        inspect_sandbox(io_adapter,name,image,network,mounts)
        return name
    try:
        report['stage']='DOCKER_SECURITY'
        security=json.loads(checked(io_adapter,['docker','info','--format','{{json .SecurityOptions}}']))
        if not any('name=seccomp' in x and 'profile=builtin' in x for x in security):raise Blocked('default seccomp unavailable')
        acquire(io_adapter,root,lock,report)
        report['stage']='IMAGE_PULL'
        checked(io_adapter,['docker','pull','--platform=linux/amd64',image],timeout=180)
        report['stage']='IMAGE_VERIFY'
        identity=json.loads(checked(io_adapter,['docker','image','inspect',image]))[0]
        if identity['Id']!='sha256:'+lock['runtime']['config_sha256'] or identity['Architecture']!='amd64' or identity['Os']!='linux':raise Blocked('image identity mismatch')
        # Harmless JVM/proc preflight; no Forge/YSM. Same immutable image in all phases.
        report['stage']='JVM_PREFLIGHT'
        probe=create('preflight','none',[],['/bin/sh','-c',
            'test "$(id -u)" != 0 && test "$(wc -l < /proc/net/route)" -eq 1 && cat /usr/lib/jvm/msopenjdk-17/release && exec '+JAVA+' -XshowSettings:properties -version'])
        # stdout + stderr are combined inside this fixed shell invocation only.
        # Java -XshowSettings writes stderr: use bounded attach capture via command below.
        code,raw=io_adapter.command(['docker','start','--attach',probe],timeout=30)
        # Release metadata is stdout; JVM stderr need not be trusted as a public string.
        if code:raise Blocked('JVM/network preflight failed')
        report['java_runtime_version']=jvm_identity(raw)
        (root/'jdk-private.txt').write_bytes(raw)
        report['stage']='INSTALLER'
        stage=root/'stage';stage.mkdir()
        inst=create('install','bridge',[(str(root/'installer.jar'),'/bootstrap/installer.jar',False),(str(stage),'/stage',True)],
                    [JAVA,'-Djava.io.tmpdir=/tmp','-jar','/bootstrap/installer.jar','--installServer','/stage'])
        # Trusted installer output remains private. No YSM bytes are in its mounted tree.
        checked(io_adapter,['docker','start','--attach',inst],timeout=600)
        report['stage']='SNAPSHOT_VERIFY'
        metadata=json.loads((root/'version.json').read_bytes())
        frozen=verify_install(stage,root/'installer.jar',metadata,lock)
        (root/'snapshot.sha256').write_text(frozen+'\n')
        # Make the shared verified dependency tree host-read-only before both runs.
        for p in (stage/'libraries').rglob('*'):p.chmod(0o555 if p.is_dir() else 0o444)
        (stage/'libraries').chmod(0o555)
        report['stage']='ACQUIRE_YSM'
        ysm=io_adapter.download(YSM_URL,63269843)
        if digest(ysm)!=lock['ysm_jar_sha256']:raise Blocked('YSM mismatch')
        with zipfile.ZipFile(io.BytesIO(ysm)) as z:
            native=z.read('META-INF/native/libysm-core.so')
            if digest(native)!=lock['ysm_native_sha256']:raise Blocked('native mismatch')
        def run(phase):
            report['stage']='CONTROL_SETUP' if phase=='control' else 'YSM_SETUP'
            if snapshot(stage/'libraries')!=frozen:raise Blocked('snapshot changed')
            game=root/phase;game.mkdir();(game/'mods').mkdir()
            (game/'eula.txt').write_text('eula=true\n')
            (game/'server.properties').write_text('server-ip=127.0.0.1\nenable-rcon=false\nenable-query=false\nonline-mode=true\nview-distance=2\nsimulation-distance=2\nlevel-seed=20261018\nmax-players=1\n')
            (game/'libraries').mkdir()
            if phase=='ysm':(game/'mods'/'ysm.jar').write_bytes(ysm)
            mounts=[(str(game),'/seed',False),(str(stage/'libraries'),'/game/libraries',False)]
            command=[JAVA,'-Xms512m','-Xmx2g','-Djava.io.tmpdir=/tmp','-XX:ErrorFile=/tmp/hs_err_pid%p.log','-XX:-CreateCoredumpOnCrash','@'+ARGS,'nogui']
            # Only /tmp is writable+executable; the game/world tmpfs is bounded+noexec.
            init='cp /seed/eula.txt /seed/server.properties /game/ && mkdir -p /game/mods && cp -a /seed/mods/. /game/mods/ && exec \"$@\"'
            name=create(phase,'none',mounts,['/bin/sh','-c',init,'ysm-init',*command],'/game',True)
            report['stage']='CONTROL_RUN' if phase=='control' else 'YSM_RUN'
            report[phase]['started']=True
            result=io_adapter.stream(['docker','start','--attach','--interactive',name],name,root/(phase+'.private.log'))
            result['started']=True
            return result
        report['snapshot_sha256']=frozen
        run_pair(run,report)
        report['stage']='COMPLETE'
        return report
    except Exception as exc:
        report['error_code']=error_code(exc)
        raise
    finally:
        # Restore permissions only in this run-owned tree to allow deletion.
        for p in root.rglob('*'):
            if p.is_dir() and not p.is_symlink():p.chmod(0o700)
        try:
            cleanup(io_adapter,root,run_id,containers);report['cleanup']='PASS'
        except Exception:
            report['cleanup']='FAILED';raise


def main():
    report={'stage':'VALIDATE'};success=False
    def interrupted(signum,frame):raise Blocked('runner cancellation')
    signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGINT,interrupted)
    try:
        if len(sys.argv)!=3 or sys.argv[1]!='--lock':raise Blocked('usage')
        raw=Path(sys.argv[2]).read_bytes()
        lock=validate(raw,os.environ,Path(__file__).read_bytes())
        report['stage']='HOST_PLATFORM'
        if os.uname().machine!='x86_64' or 'VERSION_ID="24.04"' not in Path('/etc/os-release').read_text():raise Blocked('host platform mismatch')
        report=execute(lock,os.environ,IO(),report)
        report.update(lock_sha256=digest(raw),harness_sha256=digest(Path(__file__).read_bytes()),commit=os.environ['GITHUB_SHA'])
        success=report['control']['result']=='PASS' and report['ysm']['result']=='PASS'
    except Exception as exc:
        report.setdefault('error_code',error_code(exc))
        # Exceptions may contain target output or private paths; never emit their text.
        report.setdefault('control',{'result':'BLOCKED'});report.setdefault('ysm',{'result':'NOT_RUN'})
    print(summary(report))
    return 0 if success else 1

if __name__=='__main__':sys.exit(main())
