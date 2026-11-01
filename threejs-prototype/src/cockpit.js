import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { registerLegacyMaterials, suggestedGripenCamera } from './legacy-materials.js';
import { createFlightDisplay } from './displays.js';

function prepareDisplayGeometry(source, displays) {
  const geometry = source.clone();
  const position = geometry.attributes.position;
  const uv = geometry.attributes.uv;
  const indices = geometry.index ? Array.from(geometry.index.array) : Array.from({ length: position.count }, (_, i) => i);
  const parent = Array.from({ length: position.count }, (_, i) => i);
  const find = (i) => { while (parent[i] !== i) { parent[i] = parent[parent[i]]; i = parent[i]; } return i; };
  for (let i = 0; i < indices.length; i += 3) {
    parent[find(indices[i + 1])] = find(indices[i]);
    parent[find(indices[i + 2])] = find(indices[i]);
  }
  const parts = new Map();
  for (let i = 0; i < indices.length; i += 3) {
    const key = find(indices[i]);
    if (!parts.has(key)) parts.set(key, []);
    parts.get(key).push(...indices.slice(i, i + 3));
  }
  const materials = [], reordered = [];
  geometry.clearGroups();
  for (const triangles of parts.values()) {
    const vertices = [...new Set(triangles)];
    let minY = Infinity, maxY = -Infinity, minZ = Infinity, maxZ = -Infinity;
    for (const vertex of vertices) {
      minY = Math.min(minY, position.getY(vertex)); maxY = Math.max(maxY, position.getY(vertex));
      minZ = Math.min(minZ, position.getZ(vertex)); maxZ = Math.max(maxZ, position.getZ(vertex));
    }
    if (maxY - minY > .06 && maxZ - minZ > .06) {
      for (const vertex of vertices) uv.setXY(vertex, (maxY - position.getY(vertex)) / (maxY - minY), 1 - (position.getZ(vertex) - minZ) / (maxZ - minZ));
      const display = createFlightDisplay(maxZ - minZ > (maxY - minY) * 1.15 ? 1 : 0);
      displays.push(display); materials.push(display.material);
    } else {
      materials.push(new THREE.MeshBasicMaterial({ color: '#73a777', toneMapped: false }));
    }
    geometry.addGroup(reordered.length, triangles.length, materials.length - 1);
    reordered.push(...triangles);
  }
  geometry.setIndex(reordered);
  uv.needsUpdate = true;
  return { geometry, materials };
}

export async function loadCockpit(rig, { type = 'gripen', onProgress = () => {} } = {}) {
  const loader = registerLegacyMaterials(new GLTFLoader());
  const url = type === 'gripen' ? '/assets/gripen.glb' : '/assets/eurofighter.glb';
  const gltf = await loader.loadAsync(url, (event) => {
    if (event.total) onProgress(Math.round(event.loaded / event.total * 100));
  });
  const model = gltf.scene;
  model.name = type === 'gripen' ? 'Existing detailed Gripen cockpit' : 'Existing Eurofighter';
  model.rotation.y = Math.PI / 2;
  model.scale.setScalar(type === 'gripen' ? 1 : .04);
  const displays = [];
  model.traverse((object) => {
    if (!object.isMesh) return;
    object.castShadow = true;
    object.receiveShadow = true;
    if (/LandingOn|landing.?gear|wheel/i.test(object.name)) object.visible = false;
    if (type === 'gripen' && (Array.isArray(object.material) ? object.material : [object.material]).some(material => /^(jet_flame_diamonds|gunfire)$/.test(material.name))) object.visible = false;
    if (type === 'gripen' && !Array.isArray(object.material) && object.material.name === 'dynamic_mfd') {
      const prepared = prepareDisplayGeometry(object.geometry, displays);
      object.geometry = prepared.geometry; object.material = prepared.materials;
    }
    const materials = Array.isArray(object.material) ? object.material : [object.material];
    const replacements = materials.map((material) => {
      if (type === 'gripen' && material.name === 'dynamic_mfd') {
        const display = createFlightDisplay(displays.length); displays.push(display); return display.material;
      }
      if (type === 'gripen' && material.name === 'dynamic_mirror') {
        return new THREE.MeshStandardMaterial({ name: 'Dark reflective canopy mirror', color: '#526068', metalness: 1, roughness: .18, envMapIntensity: .7 });
      }
      if (type === 'gripen' && /^(saab_jas39a_inside|saab_jas39a_interior|mesh1)$/.test(material.name)) {
        material.color.set('#121b20'); material.roughness = .66; material.metalness = .18;
      }
      if (type === 'gripen' && material.name === 'saab_jas39a_cockpit') {
        material.color.set('#a0aaa9'); material.roughness = .62; material.metalness = .12;
      }
      if (type === 'gripen' && /^(dynamic_glass_chrome|empty_glass)$/.test(material.name)) {
        object.castShadow = false;
        return new THREE.MeshBasicMaterial({ name: 'Clear lightly tinted canopy glass', color: '#9ec5ce', transparent: true, opacity: .018, depthWrite: false, side: THREE.FrontSide });
      }
      if (material.map) material.map.anisotropy = 8;
      if (material.normalMap) material.normalMap.anisotropy = 4;
      material.envMapIntensity = .65;
      // Keep authored textures and gloss; only resolve transparent glass sorting.
      if (material.transparent) { material.depthWrite = false; material.side = THREE.DoubleSide; }
      return material;
    });
    object.material = Array.isArray(object.material) ? replacements : replacements[0];
  });
  rig.add(model);
  const eye = type === 'gripen' ? suggestedGripenCamera.position : [0, .49, -2.6];
  const seat = new THREE.Vector3(...eye);
  if (type === 'gripen') seat.y = .65;
  return { model, type, seat, pitch: -THREE.MathUtils.degToRad(4), label: type === 'gripen' ? 'SAAB JAS 39 · GRIPEN' : 'EUROFIGHTER TYPHOON', update(time, state) { for (const display of displays) display.update(time, state); } };
}
