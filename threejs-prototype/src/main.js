import * as THREE from 'three';
import { Sky } from 'three/addons/objects/Sky.js';
import { createWorld } from './world.js';
import { loadCockpit } from './cockpit.js';
import { RenderBudget } from './render-budget.js';
import './style.css';

const $ = (id) => document.getElementById(id);
const query = new URLSearchParams(location.search);
const capture = query.has('capture');
const canvas = $('flight');
const state = { paused: capture, time: capture ? 12 : 0, speed: 100, position: new THREE.Vector3(0, 1800, 3000), yaw: 0, pitch: 0, roll: 0, lookX: 0, lookY: 0, view: 'pilot', ready: false, quality: 'performance', preset: 'golden' };
const keys = new Set();
const errors = [];
let renderer, world, cockpit, environmentTarget;

try {
  const context = canvas.getContext('webgl2', { antialias: true, alpha: false, powerPreference: 'high-performance' });
  if (!context) throw new Error('WebGL 2 is not available.');
  renderer = new THREE.WebGLRenderer({ canvas, context, antialias: true, alpha: false, powerPreference: 'high-performance', reversedDepthBuffer: Boolean(context.getExtension('EXT_clip_control')) });
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1;
  renderer.setPixelRatio(Math.min(devicePixelRatio, 1.6));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFShadowMap;
} catch (error) {
  $('loading').hidden = true;
  $('error').hidden = false;
  $('error').textContent = 'This prototype needs WebGL 2. Enable hardware acceleration in your browser and reload. ' + error.message;
  throw error;
}

const scene = new THREE.Scene();
scene.background = new THREE.Color('#9fbdc9');
const camera = new THREE.PerspectiveCamera(68, innerWidth / innerHeight, .1, 100000);
const rig = new THREE.Group();
scene.add(rig);
world = createWorld(scene, renderer);

// A physical sky is used only for PBR image-based lighting. The visible world
// uses its own shared atmosphere so terrain, water and cloud haze agree.
function refreshEnvironment() {
  const envScene = new THREE.Scene();
  const envSky = new Sky();
  envSky.scale.setScalar(450000);
  envSky.material.uniforms.turbidity.value = state.preset === 'daylight' ? 3 : 6;
  envSky.material.uniforms.rayleigh.value = 2;
  envSky.material.uniforms.mieCoefficient.value = .005;
  envSky.material.uniforms.mieDirectionalG.value = .8;
  envSky.material.uniforms.sunPosition.value.copy(world.sunDirection).multiplyScalar(10000);
  envScene.add(envSky);
  const pmrem = new THREE.PMREMGenerator(renderer);
  const previous = environmentTarget;
  environmentTarget = pmrem.fromScene(envScene, .05, .1, 500000);
  scene.environment = environmentTarget.texture;
  previous?.dispose();
  pmrem.dispose(); envSky.geometry.dispose(); envSky.material.dispose();
}
refreshEnvironment();
scene.environmentIntensity = .4;

const sunlight = scene.getObjectByName('Warm late-afternoon sun');
if (sunlight) {
  sunlight.castShadow = true;
  sunlight.shadow.mapSize.set(2048, 2048);
  Object.assign(sunlight.shadow.camera, { near: 2, far: 160, left: -12, right: 12, top: 12, bottom: -12 });
  sunlight.shadow.normalBias = .025;
  sunlight.shadow.bias = -.00015;
  scene.add(sunlight.target);
}

const pose = new THREE.Euler(0, 0, 0, 'YXZ');
const aircraftRotation = new THREE.Quaternion();
const localRotation = new THREE.Quaternion();
const forward = new THREE.Vector3();
const target = new THREE.Vector3();
const chaseTarget = new THREE.Vector3();
const budget = new RenderBudget(renderer.getContext(), scale => { renderer.setPixelRatio(scale); resize(); });
let frameTimestamp = performance.now();
let lastTelemetry = 0, fpsTime = 0, frameCount = 0;
let shadowTime = -Infinity;
renderer.shadowMap.autoUpdate = false;

function setQuality(value) {
  if (!['high', 'balanced', 'performance'].includes(value)) value = 'performance';
  state.quality = value;
  $('quality').value = value;
  const scale = Math.min(devicePixelRatio, value === 'high' ? 1.6 : 1);
  renderer.setPixelRatio(scale);
  renderer.shadowMap.enabled = value !== 'balanced';
  if (sunlight) {
    const size = value === 'high' ? 2048 : 1024;
    if (sunlight.shadow.mapSize.x !== size) {
      sunlight.shadow.map?.dispose(); sunlight.shadow.map = null;
      sunlight.shadow.mapSize.set(size, size);
    }
  }
  world.setQuality?.(value);
  budget.configure(value === 'performance', scale);
  shadowTime = -Infinity; renderer.shadowMap.needsUpdate = true;
  resize();
}

function resize() {
  renderer.setSize(innerWidth, innerHeight, false);
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
}
addEventListener('resize', resize);
resize();

function reset() {
  state.position.set(0, state.preset === 'clouds' ? 3700 : 1800, 3000);
  state.yaw = state.pitch = state.roll = state.lookX = state.lookY = 0;
  state.speed = 100;
  shadowTime = -Infinity;
}
function setView(view) {
  state.view = view;
  $('pilot-view').classList.toggle('active', view === 'pilot');
  $('chase-view').classList.toggle('active', view === 'chase');
  $('pilot-view').setAttribute('aria-pressed', String(view === 'pilot'));
  $('chase-view').setAttribute('aria-pressed', String(view === 'chase'));
  state.lookX = state.lookY = 0;
  shadowTime = -Infinity;
}
function setPaused(value) {
  state.paused = value;
  $('pause').innerHTML = value ? '▶ <span>RESUME</span>' : 'Ⅱ <span>PAUSE</span>';
  $('pause').setAttribute('aria-label', value ? 'Resume flight' : 'Pause flight');
}
function setFov(value) {
  camera.fov = Number(value);
  camera.updateProjectionMatrix();
  $('fov').value = String(value);
  $('fov-value').value = `${value}°`;
}
function setPreset(value) {
  state.preset = value;
  world.setWeather?.(value === 'daylight' ? 'clear' : value);
  refreshEnvironment();
  shadowTime = -Infinity;
  $('preset').value = value;
  if (value === 'clouds') state.position.y = 3700;
  else state.position.y = 1800;
  $('scene-title').innerHTML = `<span>${value === 'clouds' ? '02 / THE CLOUDLINE' : '01 / THE COAST'}</span><p>${value === 'clouds' ? 'Leave the world a little further below.' : 'A little closer to the real thing.'}</p>`;
}
$('pilot-view').onclick = () => setView('pilot');
$('chase-view').onclick = () => setView('chase');
$('pause').onclick = () => setPaused(!state.paused);
$('preset').onchange = (event) => setPreset(event.target.value);
$('settings-toggle').onclick = () => {
  $('settings').hidden = !$('settings').hidden;
  $('settings-toggle').setAttribute('aria-expanded', String(!$('settings').hidden));
};
$('close-settings').onclick = () => { $('settings').hidden = true; $('settings-toggle').setAttribute('aria-expanded', 'false'); };
$('fov').oninput = (event) => setFov(event.target.value);
$('exposure').oninput = (event) => { renderer.toneMappingExposure = Number(event.target.value) / 100; $('exposure-value').value = renderer.toneMappingExposure.toFixed(2); };
$('cloud-cover').oninput = (event) => { const value = Number(event.target.value) / 100; $('cloud-value').value = `${event.target.value}%`; world.setCloudCover?.(value); };
$('quality').onchange = (event) => setQuality(event.target.value);
$('fullscreen').onclick = async () => { if (document.fullscreenElement) await document.exitFullscreen(); else await document.documentElement.requestFullscreen(); };

let dragging = false, pointerX = 0, pointerY = 0;
canvas.addEventListener('pointerdown', (event) => { dragging = true; pointerX = event.clientX; pointerY = event.clientY; canvas.setPointerCapture(event.pointerId); $('hint').style.opacity = '.35'; });
canvas.addEventListener('pointermove', (event) => {
  if (!dragging) return;
  state.lookX = THREE.MathUtils.clamp(state.lookX - (event.clientX - pointerX) * .003, -1.3, 1.3);
  state.lookY = THREE.MathUtils.clamp(state.lookY - (event.clientY - pointerY) * .0025, -.5, .7);
  pointerX = event.clientX; pointerY = event.clientY;
});
canvas.addEventListener('pointerup', () => { dragging = false; });
canvas.addEventListener('pointercancel', () => { dragging = false; });
canvas.addEventListener('dblclick', () => { state.lookX = state.lookY = 0; });
addEventListener('keydown', (event) => {
  if (event.target.matches('input, select')) return;
  if (event.target.matches('button') && ['Space', 'Enter'].includes(event.code)) return;
  if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Space'].includes(event.code)) event.preventDefault();
  keys.add(event.code);
  if (event.repeat) return;
  if (event.code === 'Space') setPaused(!state.paused);
  if (event.code === 'KeyR') reset();
  if (event.code === 'KeyH') document.body.classList.toggle('ui-hidden');
  if (event.code === 'KeyC') setView(state.view === 'pilot' ? 'chase' : 'pilot');
});
addEventListener('keyup', (event) => keys.delete(event.code));
addEventListener('blur', () => { keys.clear(); dragging = false; });
canvas.addEventListener('webglcontextlost', (event) => { event.preventDefault(); $('error').hidden = false; $('error').textContent = 'The graphics context was interrupted. Reload the page to restore the scene.'; });

function animate() {
  requestAnimationFrame(animate);
  const currentTimestamp = performance.now();
  const activeStart = currentTimestamp;
  const elapsedFrame = (currentTimestamp - frameTimestamp) / 1000;
  frameTimestamp = currentTimestamp;
  const dt = Math.min(elapsedFrame, .05);
  if (!state.paused && state.ready) {
    state.time += dt;
    const bank = (keys.has('ArrowLeft') ? 1 : 0) - (keys.has('ArrowRight') ? 1 : 0);
    const pitch = (keys.has('ArrowUp') ? 1 : 0) - (keys.has('ArrowDown') ? 1 : 0);
    state.roll = THREE.MathUtils.damp(state.roll, bank * .65, 2, dt);
    state.pitch = THREE.MathUtils.clamp(state.pitch + pitch * dt * .15, -.35, .35);
    state.yaw += bank * dt * .13;
    state.speed = THREE.MathUtils.clamp(state.speed + ((keys.has('KeyW') ? 1 : 0) - (keys.has('KeyS') ? 1 : 0)) * dt * 15, 45, 220);
    pose.set(state.pitch, state.yaw, state.roll);
    aircraftRotation.setFromEuler(pose);
    forward.set(0, 0, -1).applyQuaternion(aircraftRotation);
    state.position.addScaledVector(forward, state.speed * dt);
    state.position.y = THREE.MathUtils.clamp(state.position.y, 1350, 6500);
  }
  pose.set(state.pitch, state.yaw, state.roll);
  rig.position.copy(state.position);
  rig.quaternion.setFromEuler(pose);
  if (cockpit) {
    if (state.view === 'pilot') {
      camera.position.copy(cockpit.seat).applyQuaternion(rig.quaternion).add(state.position);
      pose.set(cockpit.pitch + state.lookY, state.lookX, 0, 'YXZ');
      localRotation.setFromEuler(pose);
      camera.quaternion.copy(rig.quaternion).multiply(localRotation);
    } else {
      target.set(Math.sin(state.lookX) * 18, 5 + state.lookY * 9, Math.cos(state.lookX) * 18).applyQuaternion(rig.quaternion).add(state.position);
      camera.position.copy(target);
      camera.lookAt(chaseTarget.copy(state.position).addScaledVector(forward.set(0, 1, -3), 1));
    }
  } else {
    camera.position.copy(state.position);
    camera.lookAt(state.position.x, state.position.y - 200, state.position.z - 3000);
  }
  if (sunlight) {
    sunlight.position.copy(state.position).addScaledVector(world.sunDirection, 80);
    sunlight.target.position.copy(state.position);
    sunlight.target.updateMatrixWorld();
    // Cached shadow texels remain valid for shared rig/light translation, but
    // their projection must still follow the aircraft on every frame.
    sunlight.updateMatrixWorld();
    sunlight.shadow.updateMatrices(sunlight);
    const shadowInterval = state.quality === 'performance' ? 1 / 30 : 1 / 60;
    if (shadowTime === -Infinity || (!state.paused && state.time - shadowTime >= shadowInterval)) {
      renderer.shadowMap.needsUpdate = true;
      shadowTime = state.time;
    }
  }
  world.update(dt, state.time, camera.position);
  cockpit?.update(state.time, state);
  budget.begin();
  renderer.render(scene, camera);
  budget.end(performance.now() - activeStart, elapsedFrame * 1000);
  fpsTime += elapsedFrame; frameCount++;
  if (fpsTime > .8) { $('fps').textContent = `${Math.round(frameCount / fpsTime)} FPS${state.quality === 'performance' ? ' / 120 TARGET' : ''}`; fpsTime = 0; frameCount = 0; }
  if (currentTimestamp - lastTelemetry > 200) {
    $('speed').innerHTML = `${Math.round(state.speed * 3.6)}<span> KM/H</span>`;
    $('altitude').innerHTML = `${Math.round(state.position.y).toLocaleString('en-GB')}<span> M</span>`;
    $('heading').innerHTML = `${String(Math.round((THREE.MathUtils.radToDeg(-state.yaw) + 360) % 360)).padStart(3, '0')}<span> °</span>`;
    lastTelemetry = currentTimestamp;
  }
}
animate();

window.__flightTest = {
  get ready() { return state.ready; }, errors,
  get state() { return { position: state.position.toArray(), fov: camera.fov, view: state.view, paused: state.paused, model: cockpit?.type, seat: cockpit?.seat.toArray(), cameraPitch: cockpit?.pitch, look: [state.lookX, state.lookY], preset: state.preset, quality: state.quality, exposure: renderer.toneMappingExposure, pixelRatio: renderer.getPixelRatio(), reversedDepth: renderer.capabilities.reversedDepthBuffer, performance: budget.snapshot(), worldQuality: world.getPerformanceSettings?.(), renderer: renderer.info.render }; },
  pause: setPaused, setView, setFov, setPreset, setQuality,
  beginTimingCapture() { budget.beginCapture(); },
  endTimingCapture() { return budget.endCapture(); },
  getPixelRatio() { return renderer.getPixelRatio(); },
  setCamera(values) { if (!cockpit) return; if (values.height !== undefined) cockpit.seat.y = values.height; if (values.forward !== undefined) cockpit.seat.z = values.forward; if (values.pitch !== undefined) cockpit.pitch = THREE.MathUtils.degToRad(values.pitch); if (values.fov) setFov(values.fov); },
  hideUI(value = true) { document.body.classList.toggle('ui-hidden', value); },
  pick(x = 0, y = .65) {
    const ray = new THREE.Raycaster(); ray.setFromCamera(new THREE.Vector2(x, y), camera);
    return ray.intersectObjects(rig.children, true).slice(0, 8).map(hit => ({ distance: hit.distance, object: hit.object.name, material: hit.object.material.name, opacity: hit.object.material.opacity, transparent: hit.object.material.transparent, side: hit.object.material.side, facing: ray.ray.direction.dot(hit.face.normal.clone().applyNormalMatrix(new THREE.Matrix3().getNormalMatrix(hit.object.matrixWorld))) }));
  },
};

try {
  cockpit = await loadCockpit(rig, { type: query.get('model') === 'eurofighter' ? 'eurofighter' : 'gripen', onProgress: (percent) => { $('loading-detail').textContent = `Loading cockpit · ${percent}%`; } });
  if (query.has('height')) cockpit.seat.y = Number(query.get('height'));
  if (query.has('forward')) cockpit.seat.z = Number(query.get('forward'));
  if (query.has('pitch')) cockpit.pitch = THREE.MathUtils.degToRad(Number(query.get('pitch')));
  setFov(query.get('fov') || 68);
  state.ready = true;
  setQuality(query.get('quality') || 'performance');
  setPaused(state.paused);
  $('status-text').textContent = `AUTOPILOT · ${cockpit.label}`;
  $('loading').classList.add('ready');
  if (query.has('clean')) document.body.classList.add('ui-hidden');
  setTimeout(() => { $('loading').hidden = true; }, 700);
} catch (error) {
  errors.push(error.message);
  $('loading').hidden = true;
  $('error').hidden = false;
  $('error').textContent = 'The cockpit could not be loaded. The environment is still running. Reload the page or try ?model=eurofighter. ' + error.message;
  console.error(error);
}
