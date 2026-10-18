"""Authored fake fixtures only. No Docker, Java, downloads or target bytes."""
import hashlib
import copy
import io
import os
import zipfile
import urllib.error
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location('smoke', HERE / 'ysm_runtime_smoke.py')
m = importlib.util.module_from_spec(spec)
if spec.loader and spec.origin and Path(spec.origin).exists():
    spec.loader.exec_module(m)

class SmokeTests(unittest.TestCase):
    def test_implementation_exists(self):
        self.assertTrue(hasattr(m, 'validate'), 'approval validator not implemented')

    def test_gates_have_no_side_effects(self):
        if not hasattr(m, 'validate'): self.skipTest('implementation missing')
        for env in ({}, {'ALLOW_ORIGINAL_YSM_EXECUTION':'true'}, {'ACCEPT_MINECRAFT_EULA':'true'}):
            with self.assertRaises(m.Blocked): m.validate(b'{}', env, b'author code')

    def test_outcomes_distinguish_timeout_kill_oom(self):
        if not hasattr(m, 'outcome'): self.skipTest('implementation missing')
        self.assertEqual(m.outcome(137, False, False, True), 'CRASH_137')
        self.assertEqual(m.outcome(137, True, False, True), 'TIMEOUT')
        self.assertEqual(m.outcome(137, False, True, True), 'OOM')
        self.assertEqual(m.outcome(0, False, False, False), 'NOT_READY')
        self.assertEqual(m.outcome(0, False, False, True), 'PASS')

    def test_sandbox_argv(self):
        if not hasattr(m, 'sandbox'): self.skipTest('implementation missing')
        a = m.sandbox('owned-123', 1001, 'none')
        for flag in ['--read-only','--cap-drop=ALL','--security-opt=no-new-privileges','--network=none','--pids-limit=256','--memory=4g','--cpus=2','--ulimit=core=0','--log-driver=none']:
            self.assertIn(flag,a)
        self.assertFalse(any(x in a for x in ['--privileged','--pid=host','--network=host','-p']))

    def test_summary_drops_arbitrary_output(self):
        if not hasattr(m, 'summary'): self.skipTest('implementation missing')
        s=m.summary({'control':{'result':'PASS','raw':'::error::token /home/private\x1b[31m'},'secret':'password'})
        self.assertNotIn('token',s); self.assertNotIn('password',s);self.assertNotIn('::',s)
        self.assertIn('NOT_OBSERVED',s)

    def test_snapshot_rejects_symlinks_and_hashes(self):
        if not hasattr(m, 'snapshot'): self.skipTest('implementation missing')
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);(p/'a.jar').write_bytes(b'authored dummy')
            first=m.snapshot(p);self.assertEqual(first,m.snapshot(p))
            (p/'a.jar').write_bytes(b'changed');self.assertNotEqual(first,m.snapshot(p))
            (p/'escape').symlink_to('/etc/passwd')
            with self.assertRaises(m.Blocked):m.snapshot(p)

    def test_control_failure_blocks_target(self):
        if not hasattr(m, 'run_pair'): self.skipTest('implementation missing')
        calls=[]
        def fake(phase):
            calls.append(phase);return {'result':'CRASH_137'}
        result=m.run_pair(fake)
        self.assertEqual(calls,['control']);self.assertEqual(result['ysm']['result'],'NOT_RUN')

    def test_cleanup_only_owned_names(self):
        if not hasattr(m, 'cleanup'): self.skipTest('implementation missing')
        calls=[]
        class Fake:
            def command(self,argv,**kw):
                calls.append(argv)
                return 0, json.dumps([{'Config':{'Labels':{'ysm.run':'wrong'}}}]).encode()
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'owned';p.mkdir()
            with self.assertRaises(m.Blocked):m.cleanup(Fake(),p,'abc',['unrelated'])
            self.assertTrue(p.exists());self.assertFalse(any('rm' in a for a in calls))

class RegressionTests(unittest.TestCase):
    def approved(self):
        source=b'authored fake source';lock=copy.deepcopy(m.EXPECTED_LOCK)
        lock['harness_sha256']=m.digest(source)
        raw=json.dumps(lock).encode()
        env={'ALLOW_ORIGINAL_YSM_EXECUTION':'true','ACCEPT_MINECRAFT_EULA':'true',
             'EXPECTED_COMMIT':'a'*40,'GITHUB_SHA':'a'*40,
             'GITHUB_REPOSITORY':'genkimorimori252525-oss/KNEEKURA-TECH-HUB',
             'GITHUB_REF':'refs/heads/main','GITHUB_EVENT_NAME':'workflow_dispatch',
             'REPOSITORY_VISIBILITY':'public','RUNNER_ENVIRONMENT':'github-hosted',
             'RUNNER_OS':'Linux','RUNNER_ARCH':'X64','ImageOS':'ubuntu24',
             'APPROVED_LOCK_SHA256':m.digest(raw)}
        return raw,env,source

    def test_validated_data_and_every_context_guard(self):
        raw,env,source=self.approved()
        self.assertEqual(m.validate(raw,env,source)['status'],'REVIEWED_COMPLETE')
        for key in env:
            with self.subTest(key=key):
                bad=dict(env);bad[key]='wrong'
                with self.assertRaises(m.Blocked):m.validate(raw,bad,source)
        with self.assertRaises(m.Blocked):m.validate(raw,env,b'different source')

    def test_changed_missing_unknown_and_draft_lock_rejected(self):
        raw,env,source=self.approved();lock=json.loads(raw)
        for change in ('draft','missing','unknown','memory','image'):
            bad=copy.deepcopy(lock)
            if change=='draft':bad['status']='NOT_EXECUTABLE'
            if change=='missing':del bad['bootstrap']['installer_profile_sha256']
            if change=='unknown':bad['unknown']=True
            if change=='memory':bad['isolation']['memory_mib']=8192
            if change=='image':bad['runtime']['platform_manifest_sha256']='b'*64
            changed=json.dumps(bad).encode();e=dict(env);e['APPROVED_LOCK_SHA256']=m.digest(changed)
            with self.subTest(change=change),self.assertRaises(m.Blocked):m.validate(changed,e,source)

    def test_target_runs_only_after_pass_and_never_claims_native(self):
        calls=[]
        def run(phase):calls.append(phase);return {'result':'PASS'}
        r=m.run_pair(run)
        self.assertEqual(calls,['control','ysm'])
        report=json.loads(m.summary(r))
        self.assertEqual(report['native_load'],'NOT_OBSERVED')
        self.assertEqual(report['jni_registration'],'NOT_OBSERVED')
        self.assertEqual(report['worker_drain'],'NOT_OBSERVED')

    def test_target_exception_preserves_control_evidence(self):
        report={}
        def run(phase):
            if phase=='control':return {'result':'PASS','started':True}
            report[phase]['started']=True
            raise m.Blocked('fake failure after target launch')
        with self.assertRaises(m.Blocked):m.run_pair(run,report)
        result=json.loads(m.summary(report))
        self.assertEqual(result['control']['result'],'PASS')
        self.assertTrue(result['ysm']['started'])
        self.assertEqual(result['ysm']['result'],'BLOCKED')

    def test_exact_jvm_build_required(self):
        self.assertTrue(hasattr(m,'jvm_identity'))
        raw=b'IMPLEMENTOR="Microsoft"\nJAVA_VERSION="17.0.17"\nJAVA_RUNTIME_VERSION="17.0.17+10-LTS"\n    java.vendor = Microsoft\n    java.runtime.version = 17.0.17+10-LTS\n'
        self.assertEqual(m.jvm_identity(raw),'17.0.17+10-LTS')
        for bad in (raw.replace(b'17.0.17+10-LTS',b''),raw.replace(b'Microsoft',b'Other'),raw.replace(b'JAVA_VERSION="17.',b'JAVA_VERSION="21.')):
            with self.assertRaises(m.Blocked):m.jvm_identity(bad)

    def test_actual_isolation_inspection_rejects_relaxations(self):
        image='fake@sha256:'+'a'*64
        d={'Config':{'User':f'{os.getuid()}:{os.getuid()}','Image':image,'WorkingDir':'/tmp'},'Mounts':[],
           'HostConfig':{'NetworkMode':'none','ReadonlyRootfs':True,'Privileged':False,'PidMode':'',
                         'IpcMode':'private','CapDrop':['ALL'],'SecurityOpt':['no-new-privileges'],
                         'Memory':4*1024**3,'MemorySwap':4*1024**3,'NanoCpus':2*10**9,'PidsLimit':256,
                         'LogConfig':{'Type':'none'},'Tmpfs':{'/tmp':'rw,exec,size=536870912'},
                         'Ulimits':[{'Name':'core','Hard':0,'Soft':0}]}}
        class Fake:
            def __init__(self,doc):self.doc=doc
            def command(self,argv,**kw):return 0,json.dumps([self.doc]).encode()
        m.inspect_sandbox(Fake(d),'fake',image,'none',[])
        for key,value in [('NetworkMode','bridge'),('Privileged',True),('ReadonlyRootfs',False),('PidMode','host'),('CapAdd',['SYS_ADMIN']),('PortBindings',{'25565/tcp':[{}]}),('PidsLimit',0),('Memory',0),('SecurityOpt',['seccomp=unconfined'])]:
            bad=copy.deepcopy(d);bad['HostConfig'][key]=value
            with self.subTest(key=key),self.assertRaises(m.Blocked):m.inspect_sandbox(Fake(bad),'fake',image,'none',[])

    def test_fixed_diagnostics_preserve_early_blocker_without_raw_text(self):
        for payload,code,reason in [(b'[]',0,'SECCOMP_UNAVAILABLE'),(b'private-token ::error::',0,'INVALID_JSON'),(b'private-token /home/secret',1,'COMMAND_FAILED')]:
            calls=[]
            class Fake:
                def command(self,argv,**kw):calls.append(argv);return code,payload
                def download(self,*a):self.fail('download must not occur')
            lock=copy.deepcopy(m.EXPECTED_LOCK);lock['isolation']['uid']=os.getuid();report={}
            with self.assertRaises(Exception):m.execute(lock,{},Fake(),report)
            out=json.loads(m.summary(report))
            self.assertEqual(out.get('stage'),'DOCKER_SECURITY')
            self.assertEqual(out.get('error_code'),reason)
            self.assertEqual(out.get('cleanup'),'PASS')
            self.assertNotIn('private-token',json.dumps(out));self.assertNotIn('/home',json.dumps(out))
            self.assertEqual(len(calls),1)

    def test_unknown_diagnostic_strings_are_never_published(self):
        self.assertTrue(hasattr(m,'error_code'))
        self.assertEqual(m.error_code(m.Blocked('::error::secret /private')),'POLICY_REJECTED')
        out=m.summary({'stage':'::error::secret','error_code':'/private'})
        self.assertNotIn('::',out);self.assertNotIn('/private',out)

    def test_http_status_is_numeric_only_and_preserved_before_cleanup(self):
        for status in (403,404,429,503):
            class Fake:
                def command(self,argv,**kw):return 0,b'["name=seccomp,profile=builtin"]'
                def download(self,*a):raise urllib.error.HTTPError('https://private.invalid/secret',status,'SECRET ::error::',{'Authorization':'SECRET'},None)
            lock=copy.deepcopy(m.EXPECTED_LOCK);lock['isolation']['uid']=os.getuid();report={}
            with self.assertRaises(urllib.error.HTTPError):m.execute(lock,{},Fake(),report)
            out=json.loads(m.summary(report))
            self.assertEqual(out.get('stage'),'ACQUIRE_INSTALLER')
            self.assertEqual(out.get('error_code'),'HTTP_FAILURE')
            self.assertEqual(out.get('http_status'),status)
            self.assertEqual(out.get('cleanup'),'PASS')
            for secret in ('private.invalid','SECRET','Authorization','::error::'):
                self.assertNotIn(secret,json.dumps(out))
        for status in (-1,600,'403',True,None):
            self.assertNotIn('http_status',json.loads(m.summary({'http_status':status})))
        self.assertNotIn('http_status',json.loads(m.summary({'error_code':'NETWORK_FAILURE'})))

    def test_command_failure_diagnostics_are_fixed_and_bounded(self):
        self.assertTrue(hasattr(m,'record_error'))
        class Fake:
            def command(self,*a,**kw):return 23,b'SECRET ::error:: /private'
        report={}
        try:m.checked(Fake(),['docker','image','inspect','secret-image'])
        except m.Blocked as exc:m.record_error(report,exc)
        out=json.loads(m.summary(report))
        self.assertEqual(out.get('command_kind'),'DOCKER_IMAGE_INSPECT')
        self.assertEqual(out.get('command_exit_code'),23)
        self.assertNotIn('secret',json.dumps(out).lower())
        for bad in ({'command_kind':'secret','command_exit_code':'secret'},
                    {'command_kind':'DOCKER_INFO','command_exit_code':99999}):
            out=json.loads(m.summary(bad));self.assertNotIn('command_exit_code',out)
            self.assertNotIn('secret',json.dumps(out))

    def test_coordinate_extensions(self):
        self.assertEqual(m.coordinate('a.b:c:1:map@txt'),'a/b/c/1/c-1-map.txt')
        with self.assertRaises(m.Blocked):m.coordinate('unexplained')

    def test_cleanup_owned_and_no_broad_prune(self):
        calls=[];run_id='testowned'
        class Fake:
            def command(self,argv,**kw):
                calls.append(argv)
                return 0,json.dumps([{'Config':{'Labels':{'ysm.run':run_id}}}]).encode()
        p=Path(tempfile.gettempdir())/('ysm-smoke-'+run_id)
        self.assertFalse(p.exists());p.mkdir()
        m.cleanup(Fake(),p,run_id,[run_id+'-control'])
        self.assertFalse(p.exists());self.assertEqual(calls[-1],['docker','rm','--force',run_id+'-control'])

    def test_synthetic_installed_snapshot_checksum_and_unknown_files(self):
        # All JARs below are test-created ZIP/text, no original code or assets.
        with tempfile.TemporaryDirectory() as t:
            stage=Path(t)/'stage';lib=stage/'libraries';lib.mkdir(parents=True)
            unpacked=b'fake unpacked server';bundled=b'fake bundle library'
            buf=io.BytesIO()
            with zipfile.ZipFile(buf,'w') as z:
                z.writestr('META-INF/libraries.list',hashlib.sha256(bundled).hexdigest()+'\ta:b:1\ta/b/1/b-1.jar\n')
                z.writestr('META-INF/versions.list',hashlib.sha256(unpacked).hexdigest()+'\t1.20.1\t1.20.1/server.jar\n')
            server=buf.getvalue()
            profile={'serverJarPath':'{LIBRARY_DIR}/net/minecraft/server/{MINECRAFT_VERSION}/server-{MINECRAFT_VERSION}.jar',
                     'data':{'MC_UNPACKED':{'server':'[net.minecraft:server:1.20.1:unpacked]'},'MOJMAPS':{'server':'[net.minecraft:server:1.20.1:mappings@txt]'}},'processors':[],'libraries':[]}
            pr=json.dumps(profile).encode();args=b'libraries/a/b/1/b-1.jar'
            installer=Path(t)/'installer.jar'
            with zipfile.ZipFile(installer,'w') as z:
                z.writestr('install_profile.json',pr);z.writestr('version.json','{}');z.writestr('data/unix_args.txt',args)
            files={'net/minecraft/server/1.20.1/server-1.20.1.jar':server,
                   'net/minecraft/server/1.20.1/server-1.20.1-unpacked.jar':unpacked,
                   'a/b/1/b-1.jar':bundled,
                   'net/minecraft/server/1.20.1/server-1.20.1-mappings.txt':b'fake mappings',
                   m.ARGS[len('libraries/'):]:args}
            for name,data in files.items():
                p=lib/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
            sha=hashlib.sha1(server).hexdigest()
            metadata={'downloads':{'server':{'sha1':sha,'size':len(server)},'server_mappings':{'sha1':hashlib.sha1(b'fake mappings').hexdigest(),'size':13}},'libraries':[{'downloads':{'artifact':{'path':'a/b/1/b-1.jar','sha1':hashlib.sha1(bundled).hexdigest(),'size':len(bundled)}}}]}
            lock={'bootstrap':{'installer_profile_sha256':m.digest(pr),'minecraft_server_bytes':len(server),'minecraft_server_publisher_sha1':sha}}
            self.assertRegex(m.verify_install(stage,installer,metadata,lock),'^[a-f0-9]{64}$')
            mapping=lib/'net/minecraft/server/1.20.1/server-1.20.1-mappings.txt'
            mapping.write_bytes(b'bad mappings')
            with self.assertRaises(m.Blocked):m.verify_install(stage,installer,metadata,lock)
            mapping.write_bytes(b'fake mappings')
            (lib/'unknown.jar').write_bytes(b'unknown')
            with self.assertRaises(m.Blocked):m.verify_install(stage,installer,metadata,lock)
            (lib/'unknown.jar').unlink();(lib/'a/b/1/b-1.jar').write_bytes(b'tampered')
            with self.assertRaises(m.Blocked):m.verify_install(stage,installer,metadata,lock)
            (lib/'a/b/1/b-1.jar').write_bytes(bundled)
            profile['data'].update(PATCHED={'server':'[a:b:1:patched]'},PATCHED_SHA={'server':"'"+hashlib.sha1(b'patched').hexdigest()+"'"})
            pr=json.dumps(profile).encode();lock['bootstrap']['installer_profile_sha256']=m.digest(pr)
            with zipfile.ZipFile(installer,'w') as z:
                z.writestr('install_profile.json',pr);z.writestr('version.json','{}');z.writestr('data/unix_args.txt',args)
            with self.assertRaises(m.Blocked):m.verify_install(stage,installer,metadata,lock)
            del profile['data']['PATCHED'];del profile['data']['PATCHED_SHA']
            profile['processors']=[{'outputs':{'libraries/missing.jar':hashlib.sha1(b'missing').hexdigest()}}]
            pr=json.dumps(profile).encode();lock['bootstrap']['installer_profile_sha256']=m.digest(pr)
            with zipfile.ZipFile(installer,'w') as z:
                z.writestr('install_profile.json',pr);z.writestr('version.json','{}');z.writestr('data/unix_args.txt',args)
            with self.assertRaises(m.Blocked):m.verify_install(stage,installer,metadata,lock)

if __name__ == '__main__': unittest.main()
