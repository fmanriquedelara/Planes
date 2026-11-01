shader_type sky;
render_mode disable_fog;

// Ocean.gdshader uses this identical source-colour horizon and a full far fade.
// Avoid TIME/POSITION so a stationary daylight cubemap is not rebuilt each frame.
uniform vec4 horizon_colour : source_color = vec4(0.42, 0.62, 0.79, 1.0);
uniform vec4 zenith_colour : source_color = vec4(0.075, 0.22, 0.48, 1.0);

void sky() {
	vec3 direction = normalize(EYEDIR);
	// The first two degrees and the lower hemisphere share exactly the same
	// colour as distant water, including below the finite ocean's clipped edge.
	// Smooth derivatives at the horizon avoid the visible collar produced by a
	// fractional power at zero. Preserve a small constant ocean-matching region.
	float rayleigh_height = smoothstep(0.02, 0.65, max(direction.y, 0.0));
	COLOR = mix(horizon_colour.rgb, zenith_colour.rgb, rayleigh_height);
	if (LIGHT0_ENABLED) {
		vec3 toward_sun = -normalize(LIGHT0_DIRECTION);
		float alignment = clamp(dot(direction, toward_sun), 0.0, 1.0);
		float above_horizon = smoothstep(0.04, 0.18, direction.y);
		float mie_halo = pow(alignment, 96.0) * 0.12;
		float sun_disc = smoothstep(cos(0.006), cos(0.0042), alignment) * 5.0;
		COLOR += LIGHT0_COLOR * min(LIGHT0_ENERGY, 3.0) * (mie_halo + sun_disc) * above_horizon;
	}
}
