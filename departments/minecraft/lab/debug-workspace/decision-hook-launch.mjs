import path from 'node:path';

/** Explicit debug-only development hooks; never added to normal or default debug launches. */
export function decisionHookLaunchOptions(config,repoRoot) {
  if(config.decisionHooks!=null && typeof config.decisionHooks!=='boolean')throw new TypeError('decisionHooks must be boolean');
  if(config.decisionHooks!==true)return {extraArgs:[],env:{KNEEKURA_DEBUG_DECISION_HOOKS:'0',KNEEKURA_DEBUG_DECISION_RESOURCES:''}};
  if(!/^(gradlew|gradle)(\.bat|\.cmd|\.exe)?$/i.test(path.basename(config.launch.command)))throw new TypeError('GRADLE_DEBUG_LAUNCH_REQUIRED');
  const bridge=path.join(repoRoot,'debug-workspace','forge-bridge');
  let init=path.join(bridge,'decision-hooks.init.gradle');
  if(config.launch.shell===true){
    if(/[&|<>^()%!;`$\r\n"]/.test(init))throw new TypeError('UNSAFE_DECISION_INIT_SHELL_PATH');
    if(/\s/.test(init))init='"'+init+'"';
  }
  return {extraArgs:['--init-script',init],env:{KNEEKURA_DEBUG_DECISION_HOOKS:'1',
    KNEEKURA_DEBUG_DECISION_RESOURCES:path.join(bridge,'src','main','resources')}};
}
