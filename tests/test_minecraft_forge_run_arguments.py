"""Cached ForgeGradle's real task action, with only process execution captured.

No Minecraft JVM is started. Set GROOVY_JAR, FORGE_GRADLE_JAR and SRGUTILS_JAR
explicitly to local caches; the fixture never downloads dependencies.
"""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

import pytest

SCRIPT = Path('src/kneekura_tech_hub/minecraft/resources/kneekura-run.init.gradle')
CLIENT = ['--launchTarget', 'forgeclientuserdev', '--version', 'MOD_DEV',
          '--assetIndex', '{asset_index}', '--assetsDir', '{assets_root}', '--gameDir', '.',
          '--fml.forgeVersion', '47.4.6', '--fml.mcVersion', '1.20.1',
          '--fml.forgeGroup', 'net.minecraftforge', '--fml.mcpVersion', '20230612.114412',
          '--username', 'KneekuraTest', '--uuid', '57e9ec72-85ae-3dd2-8fb4-2672e58b0ffe']
RESOLVED_CLIENT = [s.replace('{asset_index}', '5').replace('{assets_root}', '/cached/assets') for s in CLIENT]
RESOLVED_CLIENT[RESOLVED_CLIENT.index('--gameDir') + 1] = '@RUN@'
CASES = [
    ('actual_client_defaults', 'runClient', [], CLIENT, [], RESOLVED_CLIENT),
    ('actual_server_defaults', 'runServer', [], ['--launchTarget', 'forgeserveruserdev', '--gameDir', '.', '--nogui'], [],
     ['--launchTarget', 'forgeserveruserdev', '--gameDir', '@RUN@', '--nogui', '--world', 'managed']),
    ('gametest_setup', 'runGameTestServer', [], ['--launchTarget', 'forgegametestserveruserdev', '--gameDir', '.'], [],
     ['--launchTarget', 'forgegametestserveruserdev', '--gameDir', '@RUN@']),
    ('all_sources_order', 'runClient', ['--ordinary', '{not_a_forge_token}'], ['--gameDir', '.', '--forge', '{lazy_value}'],
     [['--provider', '{not_a_forge_token}'], ['--last', 'value']],
     ['--ordinary', '{not_a_forge_token}', '--gameDir', '@RUN@', '--forge', 'resolved-lazy-1', '--provider', '{not_a_forge_token}', '--last', 'value']),
    ('provider_observes_all_setup', 'runClient', ['--ordinary', 'value'], ['--gameDir', '.'], [['@OBSERVE_ALL@'], ['--last', 'value']], ['--ordinary', 'value', '--gameDir', '@RUN@', '--setup', 'true:true:true:true', '--last', 'value']),
    ('provider_after_forge_setup', 'runClient', [], ['--gameDir', '.'], [['@OBSERVE@']], ['--gameDir', '@RUN@', '--observed-property', 'retained-resolved-lazy-1']),
    ('inline_game_directory', 'runClient', [], ['--gameDir=.'], [], ['--gameDir', '@RUN@']),
    ('no_directory_anywhere', 'runClient', ['--ordinary', 'value'], ['--forge', '{lazy_value}'], [['--provider', 'value']],
     ['--ordinary', 'value', '--forge', 'resolved-lazy-1', '--provider', 'value', '--gameDir', '@RUN@']),
    ('ordinary_forge_duplicate', 'runClient', ['--gameDir', 'owned'], ['--gameDir', '.'], [], None),
    ('forge_provider_duplicate', 'runClient', [], ['--gameDir', '.'], [['--gameDir', 'other']], None),
    ('forge_absolute_escape', 'runClient', [], ['--gameDir', '/production'], [], None),
    ('forge_relative_escape', 'runClient', [], ['--gameDir', '../other'], [], None),
    ('provider_escape', 'runClient', [], [], [['--gameDir', '/production']], None),
    ('forge_empty_directory', 'runClient', [], ['--gameDir='], [], None),
    ('wrong_working_directory', 'runClient', [], ['--gameDir', '.'], [], None),
    ('client_option_terminator', 'runClient', [], ['--'], [], None),
    ('server_option_terminator', 'runServer', [], ['--', '--world', 'managed'], [], None),
    ('provider_option_terminator', 'runClient', [], ['--gameDir', '.'], [['--']], None),
    ('forge_internal_duplicate', 'runClient', [], ['--gameDir', '.', '--gameDir=.'], [], None),
    ('forge_missing_directory', 'runClient', [], ['--gameDir'], [], None),
    ('forge_option_as_directory', 'runClient', [], ['--gameDir', '--width', '800'], [], None),
    ('expanded_token_duplicate', 'runClient', [], ['--gameDir', '.', '{game_option}', '.'], [], None),
    ('expanded_token_directory', 'runClient', [], ['{game_option}', '.'], [], ['--gameDir', '@RUN@']),
    ('matching_forge_world', 'runServer', [], ['--world=managed'], [], ['--world=managed']),
    ('conflicting_forge_world', 'runServer', [], ['--world', 'other'], [], None),
    ('missing_forge_world', 'runServer', [], ['--world'], [], None),
    ('cross_source_world_duplicate', 'runServer', ['--world', 'managed'], ['--world=managed'], [], None),
    ('provider_world_duplicate', 'runServer', [], ['--world', 'managed'], [['--world=managed']], None),
    ('forge_universe', 'runServer', [], ['--universe', '/production'], [], None),
    ('forge_inline_universe', 'runServer', [], ['--universe=/production'], [], None),
    ('forge_abbreviated_universe', 'runServer', [], ['--uni', '/production'], [], None),
    ('token_universe', 'runServer', [], ['{universe_option}', '/production'], [], None),
    ('lazy_then_rejected', 'runClient', [], ['--fixture', '{lazy_value}', '--gameDir', '.', '--gameDir', '.'], [], None),
    ('lazy_provider_failure', 'runClient', [], ['--fixture', '{lazy_value}'], [['@THROW@']], None),
    ('forge_abbreviated_world', 'runServer', [], ['--w', 'managed'], [], None),
]


@pytest.fixture(scope='module')
def actual_forge_results(tmp_path_factory):
    paths = {key: os.environ.get(key) for key in ('GROOVY_JAR', 'FORGE_GRADLE_JAR', 'SRGUTILS_JAR')}
    java, javac = shutil.which('java'), shutil.which('javac')
    if not java or not javac or any(not p or not Path(p).is_file() for p in paths.values()):
        pytest.skip('Explicit cached Gradle8.8/ForgeGradle6.0.54/srgutils and JDK required; no downloads')
    lib = Path(paths['GROOVY_JAR']).parent
    if not (lib/'gradle-core-8.8.jar').is_file() or Path(paths['FORGE_GRADLE_JAR']).name != 'ForgeGradle-6.0.54.jar':
        pytest.skip('Exact cached Gradle8.8 and ForgeGradle6.0.54 required')
    root = tmp_path_factory.mktemp('actual-forge-arguments')
    classes = root/'classes'; classes.mkdir()
    source = root/'CapturingMinecraftRunTask.java'
    # No exec override: Forge's actual action and JavaExec.copyTo both execute.
    # Only the final process action factory is replaced; there is no fallback.
    source.write_text('''package net.minecraftforge.gradle.common.util.runs;
import org.gradle.process.internal.ExecActionFactory;
public abstract class CapturingMinecraftRunTask extends MinecraftRunTask {
    public static ExecActionFactory captureFactory;
    @Override protected ExecActionFactory getExecActionFactory() {
        if (captureFactory == null) throw new AssertionError("Processes forbidden");
        return captureFactory;
    }
}
''')
    cp = os.pathsep.join([str(lib/'*'), str(lib/'plugins/*'), paths['FORGE_GRADLE_JAR'], paths['SRGUTILS_JAR'], str(classes)])
    compiled = subprocess.run([javac, '-cp', cp, '-d', str(classes), str(source)], capture_output=True, text=True, timeout=30)
    assert compiled.returncode == 0, compiled.stderr
    text = SCRIPT.read_text()
    closures = re.findall(r'^def kneekura(?:OwnedArguments|ApplyOwnedArguments) = \{.*?^\}\n', text, re.M|re.S)
    action = re.search(r'^\s*kneekuraApplyOwnedArguments\(task,.+$', text, re.M)
    assert len(closures) == 2 and action, 'Actual managed argument closure/action required'
    payload = root/'cases.json'; payload.write_text(json.dumps(CASES))
    harness = root/'Capture.groovy'
    harness.write_text('''
import groovy.json.JsonOutput
import groovy.json.JsonSlurper
import java.lang.reflect.Proxy
import org.gradle.testfixtures.ProjectBuilder
import org.gradle.process.CommandLineArgumentProvider
import org.gradle.process.ExecResult
import org.gradle.process.internal.DefaultJavaExecSpec
import org.gradle.process.internal.ExecActionFactory
import org.gradle.process.internal.JavaExecAction
import net.minecraftforge.gradle.common.util.RunConfig
import net.minecraftforge.gradle.common.util.runs.CapturingMinecraftRunTask
'''+'\n'.join(closures)+'''
def results = [:]
new JsonSlurper().parse(new File(args[0])).each { row ->
    def (id, taskName, ordinary, forgeArgs, providerRows, expected) = row
    def directory = new File(args[1],id); directory.mkdirs()
    def project = ProjectBuilder.builder().withProjectDir(directory).build()
    project.pluginManager.apply('java')
    def capture = project.objects.newInstance(DefaultJavaExecSpec)
    int executions = 0
    def finalArgs = []
    def execAction = Proxy.newProxyInstance(JavaExecAction.classLoader, [JavaExecAction] as Class[], { proxy, method, values ->
        if (method.name == 'execute') {
            finalArgs = new ArrayList(capture.args ?: [])
            capture.argumentProviders.each { provider -> finalArgs.addAll(provider.asArguments()) }
            def repeated = new ArrayList(capture.args ?: [])
            capture.argumentProviders.each { provider -> repeated.addAll(provider.asArguments()) }
            assert repeated == finalArgs
            executions++
            return [getExitValue:{0}, assertNormalExitValue:{null}, rethrowFailure:{null}] as ExecResult
        }
        method.invoke(capture, values)
    } as java.lang.reflect.InvocationHandler)
    CapturingMinecraftRunTask.captureFactory = [newJavaExecAction:{execAction}, newExecAction:{throw new AssertionError('Processes forbidden')}] as ExecActionFactory
    def fixtureTask = project.tasks.create(taskName, CapturingMinecraftRunTask)
    def run = new RunConfig(project, taskName == 'runClient' ? 'client' : 'server')
    def runDir = new File(directory, 'owned-run').canonicalFile
    def ownedWorld = 'managed'
    run.workingDirectory = (id == 'wrong_working_directory' ? new File(directory, 'unowned-run') : runDir).absolutePath
    run.args = forgeArgs
    run.token('asset_index', '5'); run.token('assets_root', '/cached/assets')
    run.token('game_option', '--gameDir'); run.token('universe_option', '--universe')
    int lazyCalls = 0; int unusedLazyCalls = 0
    run.lazyToken('lazy_value', { 'resolved-lazy-' + (++lazyCalls) } as java.util.function.Supplier)
    run.lazyToken('unused_value', { unusedLazyCalls++; throw new AssertionError('Unused token forced') } as java.util.function.Supplier)
    run.property('fixture.property', 'retained-{lazy_value}')
    run.environment('FIXTURE_ENV', 'retained-{lazy_value}')
    run.jvmArgs = ['-Dfixture.jvm=retained-{lazy_value}']
    run.source(project.sourceSets.main)
    fixtureTask.runConfig.set(run)
    fixtureTask.additionalClientArgs.set(['-Dfixture.client=retained-{lazy_value}'])
    fixtureTask.mainClass.set('never.launch.Game')
    fixtureTask.classpath(project.files('existing-classpath'))
    fixtureTask.setArgs(ordinary)
    def calls = providerRows.collect { 0 }
    providerRows.eachWithIndex { values, i ->
        fixtureTask.argumentProviders.add([asArguments:{calls[i]++; if (values == ['@THROW@']) throw new IllegalArgumentException('Provider rejected');
            if (values == ['@OBSERVE_ALL@']) return ['--setup', [
                fixtureTask.workingDir.canonicalFile == runDir,
                fixtureTask.systemProperties['fixture.property'] == 'retained-resolved-lazy-1',
                fixtureTask.args == ['--ordinary', 'value', '--gameDir', '.'],
                fixtureTask.argumentProviders.size() == providerRows.size()].join(':')]
            values == ['@OBSERVE@'] ? ['--observed-property', fixtureTask.systemProperties['fixture.property'] ?: 'MISSING'] : values}] as CommandLineArgumentProvider)
    }
    def before = [args:new ArrayList(fixtureTask.args), run_args:new ArrayList(run.args),
                  providers:new ArrayList(fixtureTask.argumentProviders), environment:new HashMap(run.environment),
                  lazy_tokens:new HashMap(run.lazyTokens)]
    String error = null
    fixtureTask.doFirst {
        '''+action.group().strip().replace('(task,', '(fixtureTask,').replace('worldName)', 'ownedWorld)')+'''
    }
    try {
        fixtureTask.actions.each { it.execute(fixtureTask) }
    } catch (Exception failure) {
        Throwable cause = failure
        while (cause.cause != null) cause = cause.cause
        error = cause.class.name + ': ' + cause.message
    }
    results[id] = [error:error, executions:executions, args:finalArgs,
        run_directory:runDir.absolutePath, working_directory:capture.workingDir.canonicalPath,
        run_args_preserved:run.args == forgeArgs,
        provider_calls:calls, lazy_calls:lazyCalls, unused_lazy_calls:unusedLazyCalls, main_class:capture.mainClass.orNull,
        properties:capture.systemProperties, environment_value:capture.environment['FIXTURE_ENV'],
        classpath:capture.classpath.files.collect{it.canonicalPath},
        expected_classpath:([project.file('existing-classpath')] + project.sourceSets.main.runtimeClasspath.files).collect{it.canonicalPath}.unique(),
        unchanged:[args:fixtureTask.args,run_args:run.args,providers:fixtureTask.argumentProviders,environment:run.environment,lazy_tokens:run.lazyTokens] == before]
}
println('KNEEKURA_CAPTURE='+JsonOutput.toJson(results))
System.exit(0)
''')
    result = subprocess.run([java, '--add-opens=java.base/java.lang=ALL-UNNAMED', '-cp', cp,
                             'groovy.ui.GroovyMain', str(harness), str(payload), str(root)],
                            capture_output=True, text=True, timeout=90)
    assert result.returncode == 0, result.stderr
    lines = [line.removeprefix('KNEEKURA_CAPTURE=') for line in result.stdout.splitlines() if line.startswith('KNEEKURA_CAPTURE=')]
    assert len(lines) == 1, result.stdout
    return json.loads(lines[0])


@pytest.mark.parametrize('case', CASES, ids=[case[0] for case in CASES])
def test_actual_forge_task_final_javaexec_spec_is_owned_and_preserves_setup(actual_forge_results, case):
    name, task, _, _, providers, expected = case
    result = actual_forge_results[name]
    if expected is None:
        assert result['error'] and 'IllegalArgumentException' in result['error'], result
        assert result['executions'] == 0, result
        assert result['unchanged'], result
    else:
        assert result['error'] is None, result
        assert result['executions'] == 1, result
        assert result['lazy_calls'] == 1, result
        actual = result['args']
        normalized = []
        i = 0
        while i < len(actual):
            arg = actual[i]
            if arg == '--gameDir' or arg.startswith('--gameDir='):
                value = arg.split('=', 1)[1] if '=' in arg else actual[i + 1]
                directory = (Path(result['working_directory']) / value).resolve()
                assert str(directory) == result['run_directory'], result
                normalized.extend(['--gameDir', str(directory)])
                i += 1 if '=' in arg else 2
            else:
                normalized.append(arg)
                i += 1
        assert normalized == [arg.replace('@RUN@', result['run_directory']) for arg in expected], result
        assert result['run_args_preserved'], result
        assert result['working_directory'] == result['run_directory']
        assert result['main_class'] == 'never.launch.Game'
        assert result['properties']['fixture.property'] == 'retained-resolved-lazy-1'
        assert result['properties']['fixture.jvm'] == 'retained-resolved-lazy-1'
        if task == 'runClient':
            assert result['properties']['fixture.client'] == 'retained-resolved-lazy-1'
        assert result['environment_value'] == 'retained-resolved-lazy-1'
        assert result['classpath'] == result['expected_classpath']
    assert result['unused_lazy_calls'] == 0, result
    assert result['provider_calls'] == [1] * len(providers), result
