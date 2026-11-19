import {
  buildFinalVertexReplayPlan,
  validateFinalVertexBuffer,
} from '/thin-final-vertex.js';

function fail(message) {
  throw new Error('Headless Thin Viewer: ' + message);
}

async function bytes(url) {
  const response = await fetch(url, { cache: 'no-store' });
  if (!response.ok) fail(url + ' -> HTTP ' + response.status);
  return new Uint8Array(await response.arrayBuffer());
}

function exactLength(value, length, label) {
  if (value.length !== length) fail(label + ' length ' + value.length + ' != ' + length);
}

function compileShader(gl, type, source, label) {
  const shader = gl.createShader(type);
  if (!shader) fail('cannot allocate ' + label + ' shader');
  gl.shaderSource(shader, source);
  gl.compileShader(shader);
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
    const log = gl.getShaderInfoLog(shader) || 'unknown shader compile error';
    gl.deleteShader(shader);
    fail(label + ' shader compile failed: ' + log);
  }
  return shader;
}

function createProgram(gl, pair) {
  const vertex = compileShader(gl, gl.VERTEX_SHADER, pair.vertex, 'vertex');
  const fragment = compileShader(gl, gl.FRAGMENT_SHADER, pair.fragment, 'fragment');
  const program = gl.createProgram();
  if (!program) fail('cannot allocate shader program');
  gl.attachShader(program, vertex);
  gl.attachShader(program, fragment);
  gl.linkProgram(program);
  gl.deleteShader(vertex);
  gl.deleteShader(fragment);
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
    const log = gl.getProgramInfoLog(program) || 'unknown program link error';
    gl.deleteProgram(program);
    fail('shader program link failed: ' + log);
  }
  return program;
}

function uniform(gl, program, name) {
  return gl.getUniformLocation(program, name);
}

function setMatrix4(gl, program, name, value) {
  const loc = uniform(gl, program, name);
  if (loc !== null) gl.uniformMatrix4fv(loc, false, new Float32Array(value));
}

function setMatrix3(gl, program, name, value) {
  const loc = uniform(gl, program, name);
  if (loc !== null) gl.uniformMatrix3fv(loc, false, new Float32Array(value));
}

function setVec3(gl, program, name, value) {
  const loc = uniform(gl, program, name);
  if (loc !== null) gl.uniform3fv(loc, new Float32Array(value));
}

function setVec4(gl, program, name, value) {
  const loc = uniform(gl, program, name);
  if (loc !== null) gl.uniform4fv(loc, new Float32Array(value));
}

function setFloat(gl, program, name, value) {
  const loc = uniform(gl, program, name);
  if (loc !== null) gl.uniform1f(loc, value);
}

function setInt(gl, program, name, value) {
  const loc = uniform(gl, program, name);
  if (loc !== null) gl.uniform1i(loc, value);
}

function depthFunc(gl, value) {
  const map = new Map([
    ['<', gl.LESS],
    ['<=', gl.LEQUAL],
    ['=', gl.EQUAL],
    ['==', gl.EQUAL],
    ['always', gl.ALWAYS],
  ]);
  const out = map.get(value);
  if (out === undefined) fail("unsupported depth function '" + value + "'");
  return out;
}

function blendEquation(gl, value) {
  if (value === 'add') return gl.FUNC_ADD;
  fail("unsupported blend equation '" + value + "'");
}

function blendFactor(gl, value) {
  const map = new Map([
    ['zero', gl.ZERO],
    ['one', gl.ONE],
    ['srcAlpha', gl.SRC_ALPHA],
    ['oneMinusSrcAlpha', gl.ONE_MINUS_SRC_ALPHA],
    ['dstAlpha', gl.DST_ALPHA],
    ['oneMinusDstAlpha', gl.ONE_MINUS_DST_ALPHA],
    ['srcColor', gl.SRC_COLOR],
    ['oneMinusSrcColor', gl.ONE_MINUS_SRC_COLOR],
    ['dstColor', gl.DST_COLOR],
    ['oneMinusDstColor', gl.ONE_MINUS_DST_COLOR],
  ]);
  const out = map.get(value);
  if (out === undefined) fail("unsupported blend factor '" + value + "'");
  return out;
}

function primitiveMode(gl, mode) {
  if (mode === 'TRIANGLES') return gl.TRIANGLES;
  if (mode === 'TRIANGLE_STRIP') return gl.TRIANGLE_STRIP;
  if (mode === 'TRIANGLE_FAN') return gl.TRIANGLE_FAN;
  fail("unsupported primitive mode '" + mode + "'");
}

function applyPipeline(gl, pipeline) {
  gl.enable(gl.DEPTH_TEST);
  gl.depthFunc(depthFunc(gl, pipeline.depth.testFunction));
  gl.depthMask(pipeline.depth.write === true);
  gl.colorMask(true, true, true, true);

  if (pipeline.cullMode === 'none') {
    gl.disable(gl.CULL_FACE);
  } else if (pipeline.cullMode === 'back') {
    gl.enable(gl.CULL_FACE);
    gl.cullFace(gl.BACK);
    gl.frontFace(gl.CCW);
  } else {
    fail("unsupported cull mode '" + pipeline.cullMode + "'");
  }

  if (pipeline.blend.enabled) {
    gl.enable(gl.BLEND);
    gl.blendEquation(blendEquation(gl, pipeline.blend.equation));
    gl.blendFunc(
      blendFactor(gl, pipeline.blend.srcFactor),
      blendFactor(gl, pipeline.blend.dstFactor),
    );
  } else {
    gl.disable(gl.BLEND);
  }
}

function samplerMinFilter(gl, bilinear, mipmap) {
  if (bilinear && mipmap) return gl.LINEAR_MIPMAP_LINEAR;
  if (bilinear) return gl.LINEAR;
  if (mipmap) return gl.NEAREST_MIPMAP_LINEAR;
  return gl.NEAREST;
}

function configureSampler(gl, info) {
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER,
    samplerMinFilter(gl, info.bilinear, info.mipmap));
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER,
    info.bilinear ? gl.LINEAR : gl.NEAREST);
  // Minecraft entity textures use ordinary normalized UVs. REPEAT is the OpenGL texture default;
  // keeping it explicit prevents browser defaults from becoming an accidental dependency.
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.REPEAT);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.REPEAT);
  if (info.mipmap) gl.generateMipmap(gl.TEXTURE_2D);
}


async function checkpoint(name) {
  const response = await fetch('/checkpoint?name=' + encodeURIComponent(name), { method: 'POST' });
  if (!response.ok) fail('checkpoint ' + name + ' -> HTTP ' + response.status);
}

async function main() {
  const jobResponse = await fetch('/job.json', { cache: 'no-store' });
  if (!jobResponse.ok) fail('job.json -> HTTP ' + jobResponse.status);
  const job = await jobResponse.json();

  const frameBytes = await bytes('/frame.bin');
  validateFinalVertexBuffer(job.frame, frameBytes);
  const plan = buildFinalVertexReplayPlan(job.frame, job.pack);

  const width = job.framebuffer.width;
  const height = job.framebuffer.height;
  const viewportWidth = job.framebuffer.viewportWidth;
  const viewportHeight = job.framebuffer.viewportHeight;
  if (!Number.isInteger(width) || !Number.isInteger(height) || width <= 0 || height <= 0) {
    fail('invalid framebuffer dimensions');
  }
  if (!Number.isInteger(viewportWidth) || !Number.isInteger(viewportHeight)
      || viewportWidth <= 0 || viewportHeight <= 0
      || viewportWidth > width || viewportHeight > height) {
    fail('invalid viewport dimensions');
  }

  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  await checkpoint('before-webgl2-context');
  const gl = canvas.getContext('webgl2', {
    alpha: true,
    antialias: false,
    depth: true,
    stencil: false,
    premultipliedAlpha: false,
    preserveDrawingBuffer: true,
    desynchronized: false,
  });
  if (!gl) fail('WebGL2 is unavailable');
  await checkpoint('webgl2-context');

  gl.pixelStorei(gl.UNPACK_ALIGNMENT, 1);
  gl.pixelStorei(gl.PACK_ALIGNMENT, 1);
  gl.disable(gl.SCISSOR_TEST);
  gl.disable(gl.POLYGON_OFFSET_FILL);
  gl.disable(gl.SAMPLE_ALPHA_TO_COVERAGE);
  gl.disable(gl.SAMPLE_COVERAGE);
  gl.depthRange(0, 1);

  const background = await bytes('/background.rgba');
  await checkpoint('background-rgba-fetched');
  exactLength(background, width * height * 4, 'background RGBA');
  const depthBytes = await bytes('/background.depth');
  await checkpoint('background-depth-fetched');
  exactLength(depthBytes, width * height * 4, 'background depth');
  const depthView = new DataView(
    depthBytes.buffer,
    depthBytes.byteOffset,
    depthBytes.byteLength,
  );
  const depth = new Float32Array(width * height);
  for (let i = 0; i < depth.length; i++) {
    const value = depthView.getFloat32(i * 4, true);
    if (!Number.isFinite(value) || value < 0 || value > 1) fail('invalid background depth');
    depth[i] = value;
  }

  await checkpoint('background-depth-parsed');

  const framebuffer = gl.createFramebuffer();
  const colorTexture = gl.createTexture();
  const depthTexture = gl.createTexture();
  if (!framebuffer || !colorTexture || !depthTexture) fail('cannot allocate framebuffer resources');

  gl.bindTexture(gl.TEXTURE_2D, colorTexture);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
  gl.texImage2D(
    gl.TEXTURE_2D, 0, gl.RGBA8,
    width, height, 0,
    gl.RGBA, gl.UNSIGNED_BYTE, background,
  );
  await checkpoint('background-color-uploaded');

  gl.bindTexture(gl.TEXTURE_2D, depthTexture);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
  gl.texImage2D(
    gl.TEXTURE_2D, 0, gl.DEPTH_COMPONENT32F,
    width, height, 0,
    gl.DEPTH_COMPONENT, gl.FLOAT, depth,
  );
  await checkpoint('background-depth-uploaded');

  gl.bindFramebuffer(gl.FRAMEBUFFER, framebuffer);
  gl.framebufferTexture2D(
    gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, colorTexture, 0,
  );
  gl.framebufferTexture2D(
    gl.FRAMEBUFFER, gl.DEPTH_ATTACHMENT, gl.TEXTURE_2D, depthTexture, 0,
  );
  gl.drawBuffers([gl.COLOR_ATTACHMENT0]);
  const fbStatus = gl.checkFramebufferStatus(gl.FRAMEBUFFER);
  if (fbStatus !== gl.FRAMEBUFFER_COMPLETE) {
    fail('framebuffer incomplete: 0x' + fbStatus.toString(16));
  }
  await checkpoint('framebuffer-complete');

  gl.viewport(0, 0, viewportWidth, viewportHeight);

  const textureMap = new Map();
  await checkpoint('before-sampler0-textures');
  for (const texture of job.textures) {
    const rgba = await bytes(texture.url);
    exactLength(rgba, texture.width * texture.height * 4, texture.path + ' RGBA');
    const handle = gl.createTexture();
    if (!handle) fail('cannot allocate texture ' + texture.path);
    gl.bindTexture(gl.TEXTURE_2D, handle);
    gl.texImage2D(
      gl.TEXTURE_2D, 0, gl.RGBA8,
      texture.width, texture.height, 0,
      gl.RGBA, gl.UNSIGNED_BYTE, rgba,
    );
    textureMap.set(texture.path, handle);
  }

  const vertexBuffer = gl.createBuffer();
  if (!vertexBuffer) fail('cannot allocate final-vertex buffer');
  gl.bindBuffer(gl.ARRAY_BUFFER, vertexBuffer);
  gl.bufferData(gl.ARRAY_BUFFER, frameBytes, gl.STATIC_DRAW);

  for (const group of plan.groups) {
    const program = createProgram(gl, group.shader);
    gl.useProgram(program);
    applyPipeline(gl, group.pipeline);

    gl.bindBuffer(gl.ARRAY_BUFFER, vertexBuffer);
    for (let location = 0; location < group.attributes.length; location++) {
      const attribute = group.attributes[location];
      gl.enableVertexAttribArray(location);
      gl.vertexAttribPointer(
        location,
        attribute.components,
        gl.FLOAT,
        false,
        plan.strideBytes,
        attribute.offsetFloats * 4,
      );
    }

    setMatrix4(gl, program, 'uModelToWorld', plan.modelToWorldMatrix);
    setMatrix3(gl, program, 'uModelNormalToWorld', plan.modelNormalToWorldMatrix);
    setMatrix4(gl, program, 'uModelView', plan.globalShaderState.modelViewMatrix);
    setMatrix4(gl, program, 'uProjection', plan.globalShaderState.projectionMatrix);
    setMatrix3(
      gl, program, 'uInverseViewRotation',
      plan.globalShaderState.inverseViewRotationMatrix,
    );
    setVec3(gl, program, 'uLight0', plan.globalShaderState.directionalLights[0]);
    setVec3(gl, program, 'uLight1', plan.globalShaderState.directionalLights[1]);
    setVec4(gl, program, 'uShaderColor', plan.globalShaderState.shaderColor);
    setFloat(gl, program, 'uFogStart', plan.globalShaderState.fog.start);
    setFloat(gl, program, 'uFogEnd', plan.globalShaderState.fog.end);
    setVec4(gl, program, 'uFogColor', plan.globalShaderState.fog.color);
    setInt(
      gl, program, 'uFogShape',
      plan.globalShaderState.fog.shape === 'sphere' ? 0 : 1,
    );

    const textureHandle = textureMap.get(group.sampler0.texture);
    if (!textureHandle) fail('missing decoded Sampler0 texture ' + group.sampler0.texture);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, textureHandle);
    configureSampler(gl, group.sampler0);
    setInt(gl, program, 'uSampler0', 0);

    if (group.primitive.indices) {
      const indices = new Uint32Array(
        group.primitive.indices.map((index) => group.vertexStart + index),
      );
      const indexBuffer = gl.createBuffer();
      if (!indexBuffer) fail('cannot allocate quad expansion index buffer');
      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, indexBuffer);
      gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, indices, gl.STATIC_DRAW);
      gl.drawElements(gl.TRIANGLES, indices.length, gl.UNSIGNED_INT, 0);
      gl.deleteBuffer(indexBuffer);
    } else {
      gl.drawArrays(
        primitiveMode(gl, group.primitive.mode),
        group.vertexStart,
        group.vertexCount,
      );
    }

    const error = gl.getError();
    if (error !== gl.NO_ERROR) {
      fail(group.groupId + ' produced GL error 0x' + error.toString(16));
    }
    gl.deleteProgram(program);
  }

  gl.finish();
  const out = new Uint8Array(width * height * 4);
  gl.readPixels(0, 0, width, height, gl.RGBA, gl.UNSIGNED_BYTE, out);
  const readError = gl.getError();
  if (readError !== gl.NO_ERROR) fail('gl.readPixels failed: 0x' + readError.toString(16));

  const debug = gl.getExtension('WEBGL_debug_renderer_info');
  const vendor = debug
    ? gl.getParameter(debug.UNMASKED_VENDOR_WEBGL)
    : gl.getParameter(gl.VENDOR);
  const renderer = debug
    ? gl.getParameter(debug.UNMASKED_RENDERER_WEBGL)
    : gl.getParameter(gl.RENDERER);

  const query = new URLSearchParams({
    width: String(width),
    height: String(height),
    vendor: String(vendor || ''),
    renderer: String(renderer || ''),
    version: String(gl.getParameter(gl.VERSION) || ''),
    shadingLanguage: String(gl.getParameter(gl.SHADING_LANGUAGE_VERSION) || ''),
  });
  const response = await fetch('/result?' + query.toString(), {
    method: 'POST',
    headers: { 'content-type': 'application/octet-stream' },
    body: out,
  });
  if (!response.ok) fail('result upload -> HTTP ' + response.status);
}

try {
  await main();
} catch (error) {
  try {
    await fetch('/error', {
      method: 'POST',
      headers: { 'content-type': 'text/plain; charset=utf-8' },
      body: error && error.stack ? error.stack : String(error),
    });
  } catch {}
  throw error;
}
