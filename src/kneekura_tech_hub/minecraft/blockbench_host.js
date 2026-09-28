/* Adapter for the reviewed sosadly command closure. No filesystem export APIs.
 * API sources and live-acceptance limitations are recorded in M2-WRITER.md.
 */
function createAssetHost(config) {
  'use strict';
  let texture = null;
  function projects() {
    if (typeof isApp === 'undefined' || !isApp || typeof ModelProject === 'undefined'
        || !Array.isArray(ModelProject.all) || typeof Plugins === 'undefined' || !Array.isArray(Plugins.all)) {
      throw new Error('A known disposable desktop environment is required');
    }
    const loaded = Plugins.all.filter(p => p.installed && !p.disabled);
    if (loaded.length !== 1 || loaded[0].id !== PLUGIN_ID) throw new Error('Unexpected installed plugin');
    return ModelProject.all;
  }
  function nativeObject() {
    return Codecs.project.compile({raw: true, bitmaps: true, absolute_paths: false, reference_images: false});
  }
  return {
    epoch() {
      if (!globalThis.crypto || !globalThis.crypto.getRandomValues) throw new Error('Secure random epoch unavailable');
      return Array.from(globalThis.crypto.getRandomValues(new Uint8Array(24)), n => n.toString(16).padStart(2, '0')).join('');
    },
    assertEmpty() {
      if (projects().length !== 0 || (typeof Project !== 'undefined' && Project)) throw new Error('Editor is not empty');
    },
    project() { return Project; },
    assertOwned(owner) {
      const all = projects();
      if (all.length !== 1 || all[0] !== owner || Project !== owner || Format.id !== 'java_block'
          || Project.save_path || Project.export_path) throw new Error('Project scope changed');
    },
    async createProject(c) {
      await commands.new_project({format: 'java_block', name: 'kneekura_' + c.session_id,
        texture_width: c.texture_size[0], texture_height: c.texture_size[1]});
    },
    async createTexture(c) {
      const created = await commands.create_texture({name: c.asset_id.split(':')[1].split('/').pop() + '.png',
        width: c.texture_size[0], height: c.texture_size[1], data_url: c.texture_data_url, particle: true});
      texture = Texture.all.find(t => t.uuid === created.uuid);
      if (!texture) throw new Error('Texture identity missing');
      const [namespace, resourcePath] = c.asset_id.split(':');
      texture.namespace = namespace;
      texture.uv_width = c.texture_size[0]; texture.uv_height = c.texture_size[1];
      texture.folder = 'item' + (resourcePath.includes('/') ? '/' + resourcePath.slice(0, resourcePath.lastIndexOf('/')) : '');
    },
    assertTexture() {
      if (Texture.all.length !== 1 || Texture.all[0] !== texture || !texture.img
          || !texture.img.complete || texture.img.naturalWidth !== config.texture_size[0]
          || texture.img.naturalHeight !== config.texture_size[1]) throw new Error('Texture bitmap is not ready');
    },
    async createCubes(c) {
      const cubes = c.blueprint.cubes.map(cube => ({name: cube.name, from: cube.from, to: cube.to,
        autouv: 0, box_uv: false,
        faces: Object.fromEntries(['north','south','east','west','up','down'].map(face =>
          [face, {uv: cube.uv.slice(), texture: texture.uuid}]))}));
      await commands.add_cubes({cubes});
    },
    async setDisplay(c) {
      if (typeof DisplayMode === 'undefined' || typeof DisplayMode.loadJSON !== 'function') throw new Error('Display API unavailable');
      Project.parent = ''; Project.front_gui_light = false;
      DisplayMode.loadJSON(c.blueprint.display);
      Canvas.updateAll();
    },
    async fingerprint() {
      // compile emits no writes; explicit options exclude paths, editor state and history.
      // Reject changing codec output conservatively, rather than accepting mixed generations.
      return JSON.stringify(nativeObject());
    },
    async exportBytes() {
      if (!Format.codec || Format.codec !== Codecs.java_block) throw new Error('Unexpected Java codec');
      const native = nativeObject();
      const compiled = await Promise.resolve(Format.codec.compile());
      return {native: JSON.stringify(native), model: typeof compiled === 'string' ? compiled : JSON.stringify(compiled),
        texture: texture.getDataURL()};
    },
    async screenshot(view) {
      const actual = view === 'isometric' ? 'isometric_right_front' : view;
      const shot = await commands.screenshot({view: actual, width: 512, height: 512, annotate: false});
      if (!shot || typeof shot.data_url !== 'string') throw new Error('Missing screenshot bytes');
      return shot.data_url;
    }
  };
}
