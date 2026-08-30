extends Node3D

var time := 0.0
var V := 150.0

var attitude := Quaternion.IDENTITY
var omega := Vector3.ZERO

# Time constants [seconds]
var tau_roll := 0.1
var tau_pitch := 0.2
@onready var engine_sound: AudioStreamPlayer3D = $EngineSound

func _ready():
	position = Vector3(0, 10, 0)
	engine_sound.play()
	engine_sound.volume_db = -10.0


func _process(delta):
	time += delta

	_update_dynamics(delta)

	# Move forward
	var forward = attitude * Vector3(1, 0, 0)
	position -= forward * V * delta

	# Rotate
	_integrate_attitude(delta)
	
	var throttle = Input.get_axis("rBrake", "rEngine")

	engine_sound.volume_db = lerp(-20.0, 0.0, 1)


func _update_dynamics(delta):
	var pitch = Input.get_axis("aPitchIncrease", "aPitchDecrease")
	var roll = Input.get_axis("aRolLeft", "aRollRight")

	var safe_V = max(V, 0.01)

	# Desired angular rates
	var omega_x_cmd = -6.0 * roll
	var omega_z_cmd = 200.0 * pitch / safe_V

	# First-order roll dynamics
	var roll_alpha = 1.0 - exp(-delta / tau_roll)
	omega.x += (omega_x_cmd - omega.x) * roll_alpha

	# First-order pitch dynamics
	var pitch_alpha = 1.0 - exp(-delta / tau_pitch)
	omega.z += (omega_z_cmd - omega.z) * pitch_alpha

	# No yaw for now
	omega.y = 0.0


func _integrate_attitude(delta):
	var angle = omega.length() * delta

	if angle > 0.000001:
		var axis = omega.normalized()
		var dq = Quaternion(axis, angle)

		# omega is in body coordinates
		attitude = (attitude * dq).normalized()

	global_transform.basis = Basis(attitude)
