import * as THREE from 'three';
import { atmosphereGLSL, terrainVertex, terrainFragment, oceanFragment, cloudVertex, cloudFragment } from './world-shaders.js';

function hash(x, z) {
  const n = Math.sin(x * 127.1 + z * 311.7) * 43758.5453;
  return n - Math.floor(n);
}
function noise(x, z) {
  const ix = Math.floor(x), iz = Math.floor(z);
  const fx = x - ix, fz = z - iz;
  const u = fx * fx * (3 - 2 * fx), v = fz * fz * (3 - 2 * fz);
  return THREE.MathUtils.lerp(THREE.MathUtils.lerp(hash(ix, iz), hash(ix + 1, iz), u), THREE.MathUtils.lerp(hash(ix, iz + 1), hash(ix + 1, iz + 1), u), v);
}
function terrainHeight(x, z) {
  const broad = noise(x * .000075, z * .000075) * .57 + noise(x * .00016 + 12, z * .00016) * .28 + noise(x * .00038, z * .00038 + 7) * .15;
  const ridge = 1 - Math.abs(noise(x * .00025 + 8, z * .00013) * 2 - 1);
  const woodedRidge = THREE.MathUtils.smoothstep(noise(x * .00008 + 3, z * .00009), .35, .75);
  const distant = THREE.MathUtils.smoothstep(-z, 12000, 38000);
  let height = 35 + broad * broad * 1250 + ridge * ridge * woodedRidge * (450 + distant * 750) + noise(x * .0012, z * .0012) * 55;
  const river = 2300 + Math.sin(z * .00019) * 2500 + Math.sin(z * .00061) * 420;
  const riverDistance = Math.abs(x - river);
  height *= THREE.MathUtils.smoothstep(riverDistance, 100, 500);
  height = THREE.MathUtils.lerp(12, height, THREE.MathUtils.smoothstep(riverDistance, 120, 350));
  const coast = -11000 + Math.sin(z * .00011) * 2400 + Math.sin(z * .00038) * 550;
  height -= (1 - THREE.MathUtils.smoothstep(x - coast, -1200, 1200)) * 1500;
  return height;
}

export function createWorld(scene, renderer) {
  const group = new THREE.Group();
  group.name = 'Procedural aerial world';
  scene.add(group);
  const resources = [];
  const timedMaterials = [];
  const clouds = [];
  const cloudShadowData = Array.from({ length: 12 }, () => new THREE.Vector4(0, 0, 1, 0));
  let cloudCover = .45;
  let weather = 'golden';
  let quality = 'high';
  const shared = {
    sunDirection: { value: new THREE.Vector3(-.6, .3, -.6).normalize() },
    skyZenith: { value: new THREE.Color('#082b59') },
    skyHorizon: { value: new THREE.Color('#6ca6b5') },
    sunTint: { value: new THREE.Color('#ffdcaa') },
    hazeDensity: { value: .000012 },
  };
  const material = (vertexShader, fragmentShader, extra = {}, settings = {}) => {
    const result = new THREE.ShaderMaterial({ vertexShader, fragmentShader, uniforms: { ...shared, ...extra }, ...settings });
    resources.push(result);
    if (result.uniforms.time) timedMaterials.push(result);
    return result;
  };
  const skyMaterial = material(/* glsl */ `varying vec3 rayPosition;void main(){rayPosition=position;vec4 clip=projectionMatrix*modelViewMatrix*vec4(position,1.0);gl_Position=clip.xyww;}`, /* glsl */ `${atmosphereGLSL}
    varying vec3 rayPosition;void main(){gl_FragColor=vec4(atmosphere(normalize(rayPosition)),1.0);
    #include <tonemapping_fragment>
    #include <colorspace_fragment>
    }`, {}, { side: THREE.BackSide, depthWrite: false, fog: false });
  const skyGeometry = new THREE.SphereGeometry(110000, 32, 16);
  const sky = new THREE.Mesh(skyGeometry, skyMaterial);
  sky.renderOrder = -100;
  sky.frustumCulled = false;
  group.add(sky);
  resources.push(skyGeometry);

  const terrainGeometry = new THREE.PlaneGeometry(180000, 180000, 512, 512);
  terrainGeometry.rotateX(-Math.PI / 2);
  const positions = terrainGeometry.attributes.position;
  for (let i = 0; i < positions.count; i++) positions.setY(i, terrainHeight(positions.getX(i), positions.getZ(i)));
  terrainGeometry.computeVertexNormals();
  const fullTerrainIndex = terrainGeometry.index;
  // Reuse heights/normals and vertex buffers; a cached stride-two index draws
  // one quarter as many triangles without rebuilding terrain on a UI change.
  const coarseIndices = new Uint32Array(256 * 256 * 6);
  let coarseOffset = 0;
  for (let z = 0; z < 512; z += 2) {
    for (let x = 0; x < 512; x += 2) {
      const a = z * 513 + x, b = (z + 2) * 513 + x;
      coarseIndices.set([a, b, a + 2, b, b + 2, a + 2], coarseOffset);
      coarseOffset += 6;
    }
  }
  const coarseTerrainIndex = new THREE.BufferAttribute(coarseIndices, 1);
  const terrain = new THREE.Mesh(terrainGeometry, material(terrainVertex, terrainFragment, { cloudShadows: { value: cloudShadowData } }));
  terrain.name = 'Rolling fields, woodland, roads and river';
  group.add(terrain);
  resources.push(terrainGeometry);

  const oceanGeometry = new THREE.PlaneGeometry(220000, 220000);
  oceanGeometry.rotateX(-Math.PI / 2);
  const ocean = new THREE.Mesh(oceanGeometry, material(terrainVertex, oceanFragment, { time: { value: 0 } }));
  ocean.position.y = 5;
  ocean.name = 'Coastal sea';
  group.add(ocean);
  resources.push(oceanGeometry);

  const cloudGeometry = new THREE.BoxGeometry(9000, 3600, 7800);
  resources.push(cloudGeometry);
  const cloudBanks = [
    [-7500, 3400, -9000, 12], [8500, 2900, -15000, 31],
    [-17000, 1800, -27000, 67], [2000, 4400, -33000, 89],
    [17000, 1700, -41000, 117],
    [-1200, 2800, -17000, 143], [14000, 3600, -7000, 171],
    [-19000, 2700, -15000, 193], [-6000, 2600, -44000, 217],
    [23000, 3300, -32000, 239], [-27000, 2400, -37000, 263],
    [7000, 2700, -50000, 291],
  ];
  for (const [x, y, z, seed] of cloudBanks) {
    const centre = new THREE.Vector3(x, y, z);
    const lobes = [];
    for (let i = 0; i < 7; i++) {
      const rx = hash(seed + i, 2), ry = hash(seed + i, 7), rz = hash(seed + i, 13);
      lobes.push(new THREE.Vector4((rx - .5) * 4700, (ry - .5) * 900, (rz - .5) * 3900, 800 + hash(seed + i, 23) * 1150));
    }
    const cloudMaterial = material(cloudVertex, cloudFragment, {
      boxCentre: { value: centre }, boxHalfSize: { value: new THREE.Vector3(4500, 1800, 3900) },
      lobes: { value: lobes }, time: { value: 0 }, marchSteps: { value: 80 }, coverStrength: { value: 1 }, sampleQuality: { value: 1 },
    }, { transparent: true, depthWrite: false, side: THREE.BackSide });
    const cloud = new THREE.Mesh(cloudGeometry, cloudMaterial);
    cloud.position.copy(centre);
    cloud.name = `Volumetric cloud bank ${seed}`;
    group.add(cloud);
    clouds.push({ mesh: cloud, material: cloudMaterial, baseY: y, seed });
  }

  // Direct light also illuminates the root application's imported cockpit.
  const sunlight = new THREE.DirectionalLight('#ffce8f', 3.3);
  sunlight.position.copy(shared.sunDirection.value).multiplyScalar(10000);
  sunlight.name = 'Warm late-afternoon sun';
  const fill = new THREE.HemisphereLight('#9bbcd6', '#363b28', .4);
  group.add(sunlight, fill);

  function updateCloudShadows(time = 0) {
    const sun = shared.sunDirection.value;
    clouds.forEach((entry, index) => {
      // Project each bank onto an approximate 350 m ground datum. This is a
      // soft landscape-scale cue, not a full volumetric light-transport shadow.
      const height = Math.max(entry.mesh.position.y - 350, 0);
      cloudShadowData[index].set(
        entry.mesh.position.x - time * 4 - sun.x * height / Math.max(sun.y, .15),
        entry.mesh.position.z - sun.z * height / Math.max(sun.y, .15),
        2850 + hash(entry.seed, 51) * 850,
        entry.mesh.visible ? entry.material.uniforms.coverStrength.value * .42 : 0,
      );
    });
  }

  function updateCloudCoverage() {
    const multiplier = weather === 'clouds' ? 1.65 : weather === 'clear' ? .65 : 1;
    const effective = THREE.MathUtils.clamp(cloudCover * multiplier, 0, 1);
    clouds.forEach((entry, index) => {
      const amount = THREE.MathUtils.clamp(effective * clouds.length - index, 0, 1);
      entry.mesh.visible = amount > .01;
      entry.material.uniforms.coverStrength.value = amount;
      entry.mesh.position.y = weather === 'clouds' ? 1700 + hash(entry.seed, 91) * 900 : entry.baseY;
      entry.material.uniforms.boxCentre.value.copy(entry.mesh.position);
    });
    updateCloudShadows();
  }
  updateCloudCoverage();

  return {
    sunDirection: shared.sunDirection.value,
    update(dt, time, cameraPosition) {
      sky.position.copy(cameraPosition);
      for (const entry of timedMaterials) entry.uniforms.time.value = time;
      updateCloudShadows(time);
    },
    setWeather(preset = 'golden') {
      weather = ['golden', 'clear', 'clouds'].includes(preset) ? preset : 'golden';
      const daylight = weather === 'clear';
      shared.sunDirection.value.set(-.6, daylight ? .85 : weather === 'clouds' ? .48 : .25, -.6).normalize();
      shared.skyHorizon.value.set(daylight ? '#78b2ca' : weather === 'clouds' ? '#87afbf' : '#6ca6b5');
      shared.skyZenith.value.set(daylight ? '#0b4585' : '#082b59');
      shared.sunTint.value.set(daylight ? '#fff0dc' : '#ffdaa0');
      shared.hazeDensity.value = daylight ? .000008 : weather === 'clouds' ? .000016 : .000012;
      sunlight.position.copy(shared.sunDirection.value).multiplyScalar(10000);
      sunlight.color.set(daylight ? '#fff0dc' : '#ffce8f');
      sunlight.intensity = daylight ? 3.5 : 3.3;
      fill.intensity = daylight ? .65 : .4;
      updateCloudCoverage();
    },
    setCloudCover(value) {
      cloudCover = THREE.MathUtils.clamp(Number(value) || 0, 0, 1);
      updateCloudCoverage();
    },
    setQuality(value = 'high') {
      quality = ['high', 'balanced', 'performance'].includes(value) ? value : 'high';
      const steps = quality === 'performance' ? 28 : quality === 'balanced' ? 40 : 80;
      const sampleQuality = quality === 'performance' ? .35 : quality === 'balanced' ? .65 : 1;
      for (const entry of clouds) {
        entry.material.uniforms.marchSteps.value = steps;
        entry.material.uniforms.sampleQuality.value = sampleQuality;
      }
      terrainGeometry.setIndex(quality === 'high' ? fullTerrainIndex : coarseTerrainIndex);
    },
    getPerformanceSettings() {
      return {
        quality,
        cloudRaySteps: quality === 'performance' ? 28 : quality === 'balanced' ? 40 : 80,
        cloudShadowSamples: quality === 'performance' ? 1 : quality === 'balanced' ? 2 : 3,
        cloudFineErosion: quality !== 'performance',
        terrainTriangles: quality === 'high' ? 524288 : 131072,
        activeCloudBanks: clouds.filter((entry) => entry.mesh.visible).length,
        cloudCover,
        weather,
      };
    },
    dispose() {
      scene.remove(group);
      for (const resource of resources) resource.dispose();
    },
  };
}
