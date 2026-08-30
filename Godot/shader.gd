shader_type spatial;

render_mode unshaded, blend_mix, depth_draw_never, cull_disabled;

// Textura de ruido.
// Puedes asignar cualquier NoiseTexture2D aquí.
uniform sampler2D noise_texture;

// Intensidad de la distorsión.
uniform float distortion_strength : hint_range(0.0, 0.2) = 0.035;

// Velocidad del movimiento del aire caliente.
uniform float distortion_speed : hint_range(0.0, 10.0) = 1.5;

// Escala del ruido.
uniform float noise_scale : hint_range(0.1, 10.0) = 2.0;

// Transparencia general.
uniform float haze_strength : hint_range(0.0, 1.0) = 0.08;


void fragment()
{
	// Coordenadas de pantalla.
	vec2 screen_uv = SCREEN_UV;

	// Ruido animado.
	vec2 noise_uv = UV * noise_scale;

	noise_uv += vec2(
		TIME * distortion_speed,
		TIME * distortion_speed * 0.35
	);

	vec2 noise = texture(noise_texture, noise_uv).rg;

	// Convertimos 0..1 a -1..1
	noise = noise * 2.0 - 1.0;

	// Distorsión de pantalla.
	vec2 distortion = noise * distortion_strength;

	screen_uv += distortion;

	// Color que hay detrás del escape.
	vec3 background = texture(
		screen_texture,
		screen_uv
	).rgb;

	// Más intensidad cerca del centro del escape.
	vec2 centered_uv = UV - vec2(0.5);

	float distance_from_center = length(centered_uv);

	float mask = 1.0 - smoothstep(
		0.0,
		0.7,
		distance_from_center
	);

	// Haze muy ligero.
	vec3 haze_color = vec3(
		0.8,
		0.85,
		0.9
	);

	vec3 final_color = mix(
		background,
		haze_color,
		haze_strength * mask
	);

	ALBEDO = final_color;

	// Necesitamos transparencia para que el efecto
	// se mezcle con lo que hay detrás.
	ALPHA = mask * haze_strength;
}
