shader_type spatial;

uniform float height_scale = 0.5;


void vertex() {
	// Displace vertices along the Y-axis using a simple sine wave based on position
	VERTEX.y += sin(VERTEX.x + TIME) * height_scale;
}
