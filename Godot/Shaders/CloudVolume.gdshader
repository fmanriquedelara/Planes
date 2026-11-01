shader_type spatial;
// Draw exit faces so the box remains visible when the camera enters its volume.
// AABB intersection below still starts the march at the near entry (or camera).
render_mode unshaded, blend_mix, depth_draw_never, depth_test_disabled, cull_front;

uniform sampler2D scene_depth : hint_depth_texture, filter_nearest, repeat_disable;
uniform vec4 horizon_colour : source_color = vec4(0.42, 0.62, 0.79, 1.0);
uniform vec3 volume_center = vec3(0.0, 1000.0, 0.0);
uniform vec3 volume_half_size = vec3(40000.0, 350.0, 40000.0);
uniform float coverage = 0.48;
uniform vec3 sun_direction = vec3(0.682, 0.616, 0.394);
varying vec3 world_position;

float hash3(vec3 p) {
	p = fract(p * 0.1031);
	p += dot(p, p.yzx + 33.33);
	return fract((p.x + p.y) * p.z);
}

float noise3(vec3 p) {
	vec3 cell = floor(p);
	vec3 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(mix(hash3(cell), hash3(cell + vec3(1, 0, 0)), f.x),
		mix(hash3(cell + vec3(0, 1, 0)), hash3(cell + vec3(1, 1, 0)), f.x), f.y),
		mix(mix(hash3(cell + vec3(0, 0, 1)), hash3(cell + vec3(1, 0, 1)), f.x),
		mix(hash3(cell + vec3(0, 1, 1)), hash3(cell + vec3(1, 1, 1)), f.x), f.y), f.z);
}

float fbm(vec3 p) {
	float value = noise3(p) * 0.55;
	value += noise3(p * 2.03 + 17.1) * 0.27;
	value += noise3(p * 4.09 + 31.7) * 0.13;
	value += noise3(p * 8.13 + 7.3) * 0.05;
	return value;
}

float density_at(vec3 p, float footprint) {
	float height = (p.y - volume_center.y) / volume_half_size.y;
	if (abs(height) >= 1.0) { return 0.0; }
	vec3 wind_position = p + vec3(TIME * 4.0, 0.0, TIME * 1.2);
	vec3 warp_position = wind_position * 0.0017;
	vec3 warp = vec3(noise3(warp_position), noise3(warp_position + 31.7), noise3(warp_position + 67.3));
	wind_position += (warp - 0.5) * 210.0;
	vec2 cell = floor(wind_position.xz / 2400.0);
	float body = -1.0;
	// A jittered cellular field of overlapping ellipsoids gives each bank a real
	// rounded silhouette. Fine FBM only erodes the surface, not its main shape.
	for (int z = -1; z <= 1; z++) {
		for (int x = -1; x <= 1; x++) {
			vec2 index = cell + vec2(float(x), float(z));
			float seed = hash3(vec3(index, 13.7));
			float occupied = smoothstep(coverage, coverage + 0.09, seed);
			if (occupied < 0.01) { continue; }
			float r1 = hash3(vec3(index, 29.3));
			float r2 = hash3(vec3(index, 47.1));
			float radius = 380.0 + r1 * 1100.0;
			vec2 centre_xz = (index + vec2(0.08 + r1 * 0.84, 0.08 + r2 * 0.84)) * 2400.0;
			vec3 centre = vec3(centre_xz.x, volume_center.y - 230.0 + r2 * 400.0, centre_xz.y);
			vec3 radius_xyz = vec3(radius, radius * (0.32 + r2 * 0.3), radius * (0.6 + seed * 0.5));
			float distance_field = length((wind_position - centre) / radius_xyz);
			vec3 lobe_offset = vec3(radius * (r2 - 0.5), radius * (0.1 + r1 * 0.28), radius * (seed - 0.5));
			distance_field = min(distance_field, length((wind_position - centre - lobe_offset) / (radius_xyz * (0.5 + r2 * 0.3))));
			lobe_offset = vec3(radius * (0.4 - r1), radius * (0.15 + r2 * 0.3), radius * (0.5 - r2));
			distance_field = min(distance_field, length((wind_position - centre - lobe_offset) / (radius_xyz * (0.4 + seed * 0.4))));
			body = max(body, (1.0 - distance_field) * occupied);
		}
	}
	float filter_width = clamp(footprint / 1300.0, 0.0, 0.22);
	if (body <= -filter_width) { return 0.0; }
	float erosion = fbm(wind_position * 0.005) * 0.26;
	float boundary = 1.0 - smoothstep(0.82, 1.0, abs(height));
	return smoothstep(-filter_width, 0.4 + filter_width, body - erosion) * boundary;
}

void vertex() {
	world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	// Haze is integrated at each cloud sample below, not at the distant box
	// exit face. Override environment fog to avoid applying it a second time.
	FOG = vec4(0.0);
	vec3 origin = INV_VIEW_MATRIX[3].xyz;
	vec3 ray = normalize(world_position - origin);
	vec3 inverse_ray = sign(ray + vec3(0.0000001)) / max(abs(ray), vec3(0.000001));
	vec3 t0 = (volume_center - volume_half_size - origin) * inverse_ray;
	vec3 t1 = (volume_center + volume_half_size - origin) * inverse_ray;
	vec3 near_t = min(t0, t1);
	vec3 far_t = max(t0, t1);
	float entry = max(max(near_t.x, near_t.y), max(near_t.z, 0.0));
	float exit_t = min(min(far_t.x, far_t.y), far_t.z);
	// Godot 4.1 Vulkan has a [0,1] non-reversed depth range. The fallback
	// supports Compatibility's [-1,1] NDC range as well.
	float depth = texture(scene_depth, SCREEN_UV).r;
	vec3 ndc = vec3(SCREEN_UV * 2.0 - 1.0, depth);
	if (OUTPUT_IS_SRGB) { ndc.z = depth * 2.0 - 1.0; }
	vec4 opaque_view = INV_PROJECTION_MATRIX * vec4(ndc, 1.0);
	float opaque_distance = length(opaque_view.xyz / opaque_view.w);
	exit_t = min(min(exit_t, opaque_distance), 16000.0);
	if (exit_t <= entry) { discard; }
	float segment = exit_t - entry;
	float transmittance = 1.0;
	vec3 accumulated = vec3(0.0);
	for (int i = 0; i < 96; i++) {
		// Near-biased quadrature spends samples on nearby readable billows.
		// Filter density by the integration footprint rather than exposing
		// distant discrete slices or adding unaccumulated pixel noise.
		float u = (float(i) + 0.5) / 96.0;
		float distance_t = entry + segment * pow(u, 1.4);
		float step_size = segment * 1.4 * pow(u, 0.4) / 96.0;
		vec3 sample_position = origin + ray * distance_t;
		float distance_fade = 1.0 - smoothstep(6500.0, 16000.0, distance_t);
		float density = density_at(sample_position, step_size) * distance_fade;
		if (density > 0.005) {
			vec3 toward_sun = normalize(sun_direction);
			float shadow = density_at(sample_position + toward_sun * 100.0, 40.0) * 0.5;
			shadow += density_at(sample_position + toward_sun * 320.0, 80.0);
			shadow += density_at(sample_position + toward_sun * 700.0, 140.0) * 1.5;
			float direct_light = exp(-shadow * 1.8);
			float phase = pow(max(dot(ray, toward_sun), 0.0), 8.0) * 0.4;
			vec3 cloud_colour = vec3(0.12, 0.18, 0.27) + vec3(0.98, 0.94, 0.86) * direct_light * (0.85 + phase);
			float haze = 1.0 - exp(-distance_t * 0.00002);
			cloud_colour = mix(cloud_colour, horizon_colour.rgb, haze);
			float opacity = 1.0 - exp(-density * step_size * 0.006);
			accumulated += transmittance * opacity * cloud_colour;
			transmittance *= 1.0 - opacity;
		}
		if (transmittance < 0.015) { break; }
	}
	ALPHA = clamp(1.0 - transmittance, 0.0, 1.0);
	ALBEDO = accumulated / max(ALPHA, 0.0001);
}
