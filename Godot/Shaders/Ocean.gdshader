shader_type spatial;
render_mode cull_back;

uniform vec4 horizon_colour : source_color = vec4(0.42, 0.62, 0.79, 1.0);
varying vec3 world_position;

void vertex() {
	world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec2 p = world_position.xz;
	// Broad swells plus wind ripples; analytic slopes avoid repeating textures.
	float warp = sin(dot(p, vec2(0.0009, 0.0013))) * 2.7;
	warp += sin(dot(p, vec2(-0.0017, 0.0007))) * 1.8;
	float a = dot(p, vec2(0.023, 0.011)) + warp + TIME * 0.7;
	float b = dot(p, vec2(-0.014, 0.038)) - warp * 1.3 + TIME * 0.95;
	float c = dot(p, vec2(0.19, 0.12)) + warp * 3.1 - TIME * 1.4;
	float filter_a = 1.0 - smoothstep(0.4, 1.5, fwidth(a));
	float filter_b = 1.0 - smoothstep(0.4, 1.5, fwidth(b));
	float filter_c = 1.0 - smoothstep(0.4, 1.5, fwidth(c));
	float ripple_fade = 1.0 - smoothstep(300.0, 2400.0, length(VERTEX));
	vec2 slope = vec2(0.023, 0.011) * cos(a) * 0.35 * filter_a;
	slope += vec2(-0.014, 0.038) * cos(b) * 0.2 * filter_b;
	slope += vec2(0.19, 0.12) * cos(c) * 0.07 * ripple_fade * filter_c;
	NORMAL = normalize((VIEW_MATRIX * vec4(normalize(vec3(-slope.x, 1.0, -slope.y)), 0.0)).xyz);
	float swell_tint = sin(warp * 0.4) * 0.5 + 0.5;
	ALBEDO = mix(vec3(0.018, 0.085, 0.125), vec3(0.02, 0.092, 0.133), swell_tint);
	METALLIC = 0.0;
	SPECULAR = 0.5;
	ROUGHNESS = 0.32 + 0.04 * swell_tint;
	// DaylightSky shares this exact linear colour below the horizon.
	FOG = vec4(horizon_colour.rgb, smoothstep(35000.0, 55000.0, length(VERTEX)));
}
