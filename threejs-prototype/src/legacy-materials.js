import { Color, MeshPhysicalMaterial, SRGBColorSpace } from 'three';

const EXTENSION = 'KHR_materials_pbrSpecularGlossiness';

// Runtime compatibility for the repository's existing detailed Gripen GLB.
// This preserves its diffuse art and approximates the old BRDF with Three's
// physical dielectric model; it is not an exact specular/glossiness conversion.
class LegacySpecularGlossinessMaterial extends MeshPhysicalMaterial {
  constructor(parameters) {
    super(parameters);
    this.userData.legacySpecularGlossiness = true;
  }

  onBeforeCompile(shader) {
    if (!this.roughnessMap) return;
    shader.uniforms.legacyGlossiness = { value: this.userData.legacyGlossiness ?? 1 };
    shader.fragmentShader = `uniform float legacyGlossiness;\n${shader.fragmentShader}`;
    // Old extension stores gloss in alpha, not roughness in green. Factors and
    // texture multiply before inversion: r = 1 - (glossFactor * glossAlpha).
    shader.fragmentShader = shader.fragmentShader.replace(
      '#include <roughnessmap_fragment>',
      `float roughnessFactor = roughness;
       #ifdef USE_ROUGHNESSMAP
         vec4 legacySample = texture2D(roughnessMap, vRoughnessMapUv);
         roughnessFactor = 1.0 - legacyGlossiness * legacySample.a;
       #endif`
    );
  }

  customProgramCacheKey() {
    return this.roughnessMap ? 'legacy-spec-gloss-alpha-v1' : 'legacy-spec-gloss-factor-v1';
  }
}

/** Register before loader.load/loadAsync. Returns the same loader for chaining. */
export function registerLegacyMaterials(loader) {
  loader.register((parser) => ({
    name: EXTENSION,

    getMaterialType(index) {
      if (parser.json.materials[index]?.extensions?.[EXTENSION]) {
        return LegacySpecularGlossinessMaterial;
      }
      return null;
    },

    async extendMaterialParams(index, params) {
      const legacy = parser.json.materials[index]?.extensions?.[EXTENSION];
      if (!legacy) return;

      const diffuse = legacy.diffuseFactor ?? [1, 1, 1, 1];
      const glossiness = legacy.glossinessFactor ?? 1;
      // glTF numeric factors are linear. Only colour textures receive sRGB decode.
      params.color = new Color().setRGB(diffuse[0], diffuse[1], diffuse[2]);
      params.opacity = diffuse[3];
      params.metalness = 0;
      params.roughness = 1 - glossiness;
      params.specularIntensity = 1;
      params.specularColor = new Color().fromArray(legacy.specularFactor ?? [1, 1, 1]);
      params.userData = { ...(params.userData ?? {}), legacyGlossiness: glossiness };

      const textures = [];
      if (legacy.diffuseTexture) {
        textures.push(parser.assignTexture(params, 'map', legacy.diffuseTexture, SRGBColorSpace));
      }
      if (legacy.specularGlossinessTexture) {
        textures.push(parser.assignTexture(params, 'specularColorMap', legacy.specularGlossinessTexture, SRGBColorSpace));
        // Alpha is not colour-decoded, so the shared texture can serve both roles.
        textures.push(parser.assignTexture(params, 'roughnessMap', legacy.specularGlossinessTexture, SRGBColorSpace));
      }
      await Promise.all(textures);
    }
  }));
  return loader;
}

// Seat calibrated inside the cockpit using actual browser renders. FOV/near
// remain suggested starting values; the application owns its final lens settings.
// The GLB itself rotates Z-up into Y-up and scales by 1.0928488. Do not repeat
// that intrinsic transform. Its +X nose needs this additional yaw to face -Z.
export const suggestedGripenCamera = Object.freeze({
  modelYaw: Math.PI / 2,
  modelScale: 1,
  position: Object.freeze([0, 0.65, -5.03]),
  forward: Object.freeze([0, 0, -1]),
  fov: 70,
  near: 0.025,
  calibrated: true
});
