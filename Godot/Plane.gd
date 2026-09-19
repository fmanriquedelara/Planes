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

var idxCamera = 0;

var lookSideFilt = 0;
var lookUpFilt = 0;

var m = 100

var g = 9.81

# Time constants [seconds]
var tau_roll := 0.1
var tau_pitch := 0.2
var tau_yaw := 0.2

@onready var engine_sound: AudioStreamPlayer3D = $EngineSound
@onready var gun_sound: AudioStreamPlayer3D = $GunSound
@onready var wing: MeshInstance3D = $Eurofighter/Sketchfab_model/root/GLTF_SceneRootNode/Airframe_0/Object_4
@onready var hud: Label = $CanvasLayer/Label
@onready var cameras : Array[Camera3D]=[$Camera3D, $CameraCockpit/Camera3D_cockpit]
var wing_material: ShaderMaterial


func _ready():
	position = Vector3(0, 10, 0)

	engine_sound.play()
	engine_sound.volume_db = -4.0

	# Crear ShaderMaterial
	wing_material = ShaderMaterial.new()

	# Crear shader
	var shader = Shader.new()

	var original := wing.mesh.surface_get_material(0) as BaseMaterial3D

	print("ALBEDO TEXTURE: ", original.albedo_texture)
	print("ALBEDO COLOR: ", original.albedo_color)
	print("METALLIC: ", original.metallic)
	print("ROUGHNESS: ", original.roughness)
	print("NORMAL: ", original.normal_texture)
	print("AO: ", original.ao_texture)
	print("EMISSION: ", original.emission_enabled)
	print("specular: ", original.metallic_specular)
	print("normal_scale: ", original.normal_scale)
	print("metallic_texture: ", original.metallic_texture)
	print("roughness_texture: ", original.roughness_texture)

	shader.code = """
shader_type spatial;

uniform sampler2D albedo_texture : source_color;
uniform sampler2D normal_texture;
uniform sampler2D metallic_roughness_texture;

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

void fragment() {

	// Albedo
	ALBEDO = texture(albedo_texture, UV).rgb;

	// Metallic + Roughness
	vec4 mr = texture(metallic_roughness_texture, UV);

	METALLIC = mr.b;
	ROUGHNESS = mr.g;

	// Specular
	SPECULAR = 0.5;

	// Normal map
	NORMAL_MAP = texture(normal_texture, UV).rgb;
	NORMAL_MAP_DEPTH = 1.0;
}

"""

	wing_material = ShaderMaterial.new()
	wing_material.shader = shader

	# Pasar las texturas originales al shader
	wing_material.set_shader_parameter(
		"albedo_texture",
		original.albedo_texture
	)

	wing_material.set_shader_parameter(
		"normal_texture",
		original.normal_texture
	)

	wing_material.set_shader_parameter(
		"metallic_roughness_texture",
		original.metallic_texture
	)

	# Asignar el shader
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

	if Input.is_action_pressed("Gun"):
		if not gun_sound.playing:
			gun_sound.play()
	else:
		gun_sound.stop()
		
		
	if Input.is_action_just_pressed("Change camera"):
		_updateCamera()
		
	_moveCamera(delta)
		
	hud.text = "Air speed: %.0f km/h \nAltitude %.0f" % [V * 3.6, position[1]]


func _update_dynamics(delta):
	var pitch = Input.get_axis("aPitchIncrease", "aPitchDecrease")
	var roll = Input.get_axis("aRolLeft", "aRollRight")
	var left = Input.get_action_strength("aRolLeft")
	var right = Input.get_action_strength("aRollRight")
	var rEngine = Input.get_axis("rBrake", "rEngine")
	var yaw = Input.get_axis("YawLeft", "YawRight")
	
	
	var wind_noise = 0.05 * 2 * (0.5-randf());
	var wind_noise_roll = 0.05 * 2 * (0.5-randf());
	
	var FliftAero = 0.5 * 1.25 * (V * V) * 200.0 * 0.000167 * (pitch + wind_noise)
	var FLat = 0
	var MRoll = 0.5 * 1.25 * (V * V) * 0.000167 * (roll + wind_noise_roll)
	
	
	var Flift = min(
		FliftAero,
		0.5 * 1.25 * (110 * 110) * 180.0 * 0.000167 * 1
	);
	
	
	Flift = max(
		FliftAero,
		-0.5 * 1.25 * (110 * 110) * 100.0 * 0.000167 * 1
	);
	
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
	var omega_z_cmd = Flift / safe_V
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

	var tip_deformationL_0 = (Flift/200 - MRoll) / 2000.0
	var tip_deformationR_0 = (Flift/200 + MRoll) / 2000.0

	
	
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

func _updateCamera():
	print('Hello')
	idxCamera = (idxCamera + 1)
	if idxCamera >= cameras.size():
		idxCamera = 0;
	
	cameras[idxCamera].make_current()
	
	
func _moveCamera(delta):
	var lookSide = Input.get_axis("LookLeft", "LookRight");
	var lookUp = Input.get_action_strength("Look up");
	var tau = 0.5;
	
	
	var der_lookSide = (lookSide - lookSideFilt) / tau;
	var der_lookUp   = (lookUp - lookUpFilt) / tau;
		
		
	lookSideFilt = lookSideFilt + delta  * der_lookSide;
	lookUpFilt = lookUpFilt + delta  * der_lookUp;
	
	cameras[idxCamera].rotation = Vector3(lookUpFilt,-lookSideFilt, 0.0);
	
		

func _integrate_attitude(delta):
	var angle = omega.length() * delta

	if angle > 0.000001:
		var axis = omega.normalized()
		var dq = Quaternion(axis, angle)

		# omega is in body coordinates
		attitude = (attitude * dq).normalized()

	global_transform.basis = Basis(attitude)
