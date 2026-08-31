extends Node3D

var time := 0.0
var V := 100.0

var attitude := Quaternion.IDENTITY
var omega := Vector3.ZERO

var Cx = 0.8
var FEngineMax = 10000
var FEngineMean = 5000

var tip_deformationL = 0.0;
var der_tip_deformationL = 0.0;
var tip_deformationR = 0.0;
var der_tip_deformationR = 0.0;

var m = 100

var g = 9.81

# Time constants [seconds]
var tau_roll := 0.1
var tau_pitch := 0.2
var tau_yaw := 0.2

@onready var engine_sound: AudioStreamPlayer3D = $EngineSound
@onready var wing: MeshInstance3D = $Eurofighter/Sketchfab_model/root/GLTF_SceneRootNode/Airframe_0/Object_4

var wing_material: ShaderMaterial


func _ready():
	position = Vector3(0, 10, 0)

	engine_sound.play()
	engine_sound.volume_db = -4.0

	# Crear ShaderMaterial
	wing_material = ShaderMaterial.new()

	# Crear shader
	var shader = Shader.new()

	shader.code = """
shader_type spatial;

uniform float tip_deformationL = 0.0;
uniform float tip_deformationR = 0.0;

void vertex() {
	if (VERTEX.y > 0.0) {
		VERTEX.z += tip_deformationR
			* VERTEX.y
			* VERTEX.y;
	} else {
		VERTEX.z += tip_deformationL
			* VERTEX.y
			* VERTEX.y;
	}
}
"""

	wing_material.shader = shader

	# Asignar shader al ala
	wing.material_override = wing_material

	# Valor inicial
	wing_material.set_shader_parameter("tip_deformationL", 0.0)
	wing_material.set_shader_parameter("tip_deformationR", 0.0)

func _process(delta):
	time += delta

	_update_dynamics(delta)

	# Move forward
	var forward = attitude * Vector3(1, 0, 0)
	position -= forward * V * delta

	# Rotate
	_integrate_attitude(delta)

	var throttle = Input.get_axis("rBrake", "rEngine")

	engine_sound.volume_db = lerp(-8.0, 0.0, throttle)


func _update_dynamics(delta):
	var pitch = Input.get_axis("aPitchIncrease", "aPitchDecrease")
	var roll = Input.get_axis("aRolLeft", "aRollRight")
	var left = Input.get_action_strength("aRolLeft")
	var right = Input.get_action_strength("aRollRight")
	var rEngine = Input.get_axis("rBrake", "rEngine")
	var yaw = Input.get_axis("YawLeft", "YawRight")

	var Flift = 0.5 * 1.25 * (V * V) * 0.000167 * pitch
	var FLat = 0
	var MRoll = 0.5 * 1.25 * (V * V) * 0.000167 * roll

	var weight = m * g

	var Fweight_x = -weight * basis.x.y
	var Fweight_y = 0
	var Fweight_z = weight * basis.z.y

	var safe_V = max(V, 0.01)

	var F_drag = 0.5 * 1.25 * Cx * V * V
	var F_engine = FEngineMean + (FEngineMax - FEngineMean) * rEngine
	var FYaw = 30 * yaw + 0.005 * Fweight_z

	# Desired angular rates
	var omega_x_cmd = -6.0 * MRoll
	var omega_z_cmd = 200.0 * Flift / safe_V
	var omega_y_cmd = -FYaw / safe_V

	# First-order roll dynamics
	var roll_alpha = 1.0 - exp(-delta / tau_roll)
	omega.x += (omega_x_cmd - omega.x) * roll_alpha

	# First-order pitch dynamics
	var pitch_alpha = 1.0 - exp(-delta / tau_pitch)
	omega.z += (omega_z_cmd - omega.z) * pitch_alpha

	# First-order yaw dynamics
	var yaw_alpha = 1.0 - exp(-delta / tau_yaw)
	omega.y += (omega_y_cmd - omega.y) * yaw_alpha

	V += delta * (F_engine - F_drag - Fweight_x) / m

	# ------------------------------------
	# Enviar deformación al shader
	# ------------------------------------

	var tip_deformationL_0 = (Flift - MRoll) / 1000.0
	var tip_deformationR_0 = (Flift + MRoll) / 1000.0

	
	
	tip_deformationL = tip_deformationL + delta * der_tip_deformationL;
	der_tip_deformationL = der_tip_deformationL + delta * (5 * ( tip_deformationL_0 - tip_deformationL ) - 1 * der_tip_deformationL) / 0.1;
	tip_deformationR = tip_deformationR + delta * der_tip_deformationR;
	der_tip_deformationR = der_tip_deformationR + delta * (5 * ( tip_deformationR_0 - tip_deformationR ) - 1 * der_tip_deformationR) / 0.1;
	wing_material.set_shader_parameter(
		"tip_deformationL",
		tip_deformationL
	)

	wing_material.set_shader_parameter(
		"tip_deformationR",
		tip_deformationR
	)


func _integrate_attitude(delta):
	var angle = omega.length() * delta

	if angle > 0.000001:
		var axis = omega.normalized()
		var dq = Quaternion(axis, angle)

		# omega is in body coordinates
		attitude = (attitude * dq).normalized()

	global_transform.basis = Basis(attitude)
