extends Node3D

var time := 0.0
var V := 100.0

var attitude := Quaternion.IDENTITY
var omega := Vector3.ZERO

var Cx = 0.8;
var FEngineMax = 10000;
var FEngineMean = 5000;

var m = 100;

var g = 9.81;

# Time constants [seconds]
var tau_roll := 0.1
var tau_pitch := 0.2
var tau_yaw := 0.2
@onready var engine_sound: AudioStreamPlayer3D = $EngineSound

func _ready():
	position = Vector3(0, 10, 0)
	engine_sound.play()
	engine_sound.volume_db = -4.0


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
	var yaw   = Input.get_axis("YawLeft", "YawRight")
	
	var Flift = 0.5 * 1.25 * (V*V) * 0.000167 * pitch;
	var FLat = 0;
	var MRoll = 0.5 * 1.25 * (V*V) * 0.000167 * roll;
	
	var weight = m * g;
	
	var Fweight_x = - weight * basis.x.y;
	var Fweight_y = 0;
	var Fweight_z = weight * basis.z.y;
	
	
	var safe_V = max(V, 0.01)
	
	var F_drag = 0.5*1.25 *Cx*V*V;
	var F_engine = FEngineMean + (FEngineMax - FEngineMean) * rEngine;	
	var FYaw = 30 * yaw + 0.005*Fweight_z;

	# Desired angular rates
	var omega_x_cmd = -6.0 * MRoll
	var omega_z_cmd = 200.0 * Flift / safe_V
	var omega_y_cmd = - FYaw / safe_V;
	
	print(basis.z.y)

	# First-order roll dynamics
	var roll_alpha = 1.0 - exp(-delta / tau_roll)
	omega.x += (omega_x_cmd - omega.x) * roll_alpha

	# First-order pitch dynamics
	var pitch_alpha = 1.0 - exp(-delta / tau_pitch)
	omega.z += (omega_z_cmd - omega.z) * pitch_alpha

	# No yaw for now
	var yaw_alpha = 1.0 - exp(-delta / tau_yaw)
	omega.y += (omega_y_cmd - omega.y) * yaw_alpha
	
	V += delta * (F_engine-F_drag-Fweight_x) / m;
	
	print(V)


func _integrate_attitude(delta):
	var angle = omega.length() * delta

	if angle > 0.000001:
		var axis = omega.normalized()
		var dq = Quaternion(axis, angle)

		# omega is in body coordinates
		attitude = (attitude * dq).normalized()

	global_transform.basis = Basis(attitude)
