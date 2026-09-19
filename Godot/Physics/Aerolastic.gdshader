shader_type spatial;

uniform float tip_deformation = 0.001;

void vertex() {
  VERTEX.z += tip_deformation  * VERTEX.y * VERTEX.y;
}
