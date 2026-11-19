/** Native derived drawing is independent of deep Decision hooks and always explicit. */
export function motionOverlayLaunchEnvironment(config) {
  if(config.motionOverlay!=null&&typeof config.motionOverlay!=='boolean')throw new TypeError('motionOverlay must be boolean');
  return {KNEEKURA_DEBUG_MOTION_OVERLAY:config.motionOverlay===true?'1':'0'};
}
