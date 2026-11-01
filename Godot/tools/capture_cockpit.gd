extends SceneTree

# Run with a real GPU driver. --headless uses a dummy renderer in Godot 4.1.
const CAPTURE_SIZE := Vector2i(1280, 720)
const GAMEPLAY_FRAMES := 8
const SETTLE_FRAMES := 16
const COCKPIT_PATH := NodePath("Plane/CameraCockpit/Camera3D_cockpit")


func _initialize() -> void:
	root.unfocusable = true
	# Godot 4.1 cannot hide its main window. Minimizing also stalls rendering.
	# Keep the unfocusable window offscreen so the GPU render loop continues.
	root.position = Vector2i(-32000, -32000)
	_run_capture.call_deferred()


func _fail(message: String, code: int = 1) -> void:
	push_error("Cockpit capture failed: " + message)
	quit(code)


func _run_capture() -> void:
	if DisplayServer.get_name() == "headless" or RenderingServer.get_video_adapter_name().is_empty():
		_fail("A real rendering driver is required; do not use --headless.", 2)
		return

	var args := OS.get_cmdline_user_args()
	if args.size() > 3:
		_fail("Expected output PNG path, optional resolution, optional capture view.", 2)
		return
	var output_path := ProjectSettings.globalize_path("res://../artifacts/cockpit.png")
	if args.size() >= 1:
		output_path = args[0]
	var capture_size := CAPTURE_SIZE
	if args.size() >= 2:
		if args[1] == "1920x1080":
			capture_size = Vector2i(1920, 1080)
		elif args[1] != "1280x720":
			_fail("Resolution must be 1280x720 or 1920x1080.", 2)
			return
	var capture_view := "scene"
	if args.size() >= 3:
		capture_view = args[2]
	if not capture_view in ["scene", "inside-lower", "inside-upper"]:
		_fail("Unknown capture view.", 2)
		return
	# Repeat the game's random disturbance sequence across review captures.
	seed(604)
	if not output_path.is_absolute_path() or output_path.get_extension().to_lower() != "png":
		_fail("Output must be an absolute .png path.", 2)
		return
	output_path = output_path.simplify_path()
	var directory_error := DirAccess.make_dir_recursive_absolute(output_path.get_base_dir())
	if directory_error != OK:
		_fail("Cannot create output directory: " + error_string(directory_error))
		return

	var capture_viewport := SubViewport.new()
	capture_viewport.name = "CockpitCapture"
	capture_viewport.size = capture_size
	capture_viewport.own_world_3d = true
	capture_viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	capture_viewport.msaa_3d = int(ProjectSettings.get_setting("rendering/anti_aliasing/quality/msaa_3d", 0))
	root.add_child(capture_viewport)
	var packed_scene := load("res://Flight.tscn") as PackedScene
	if packed_scene == null:
		_fail("Could not load res://Flight.tscn.")
		return
	var flight_scene := packed_scene.instantiate()
	if flight_scene == null:
		_fail("Could not instantiate flight scene.")
		return
	capture_viewport.add_child(flight_scene)
	var cockpit := flight_scene.get_node_or_null(COCKPIT_PATH) as Camera3D
	if cockpit == null or capture_viewport.get_camera_3d() != cockpit:
		_fail("Default active camera is not the expected cockpit camera.")
		return
	if capture_view != "scene":
		var cloud_path := "CloudsLower" if capture_view == "inside-lower" else "CloudsUpper"
		var cloud := flight_scene.get_node_or_null(cloud_path) as Node3D
		var plane := flight_scene.get_node_or_null("Plane") as Node3D
		if cloud == null or plane == null:
			_fail("Requested cloud test volume is missing.")
			return
		plane.global_position.y = cloud.global_position.y

	# Allow the actual gameplay scripts to run briefly, then hold their transforms
	# while the sky/lighting renderer converges. No scene file is modified.
	for _frame in range(GAMEPLAY_FRAMES):
		await process_frame
	flight_scene.process_mode = Node.PROCESS_MODE_DISABLED
	for _frame in range(SETTLE_FRAMES):
		await process_frame
	await RenderingServer.frame_post_draw
	if capture_viewport.get_camera_3d() != cockpit:
		_fail("Active camera changed away from cockpit during capture.")
		return
	var image := capture_viewport.get_texture().get_image()
	if image == null or image.is_empty() or image.get_size() != capture_size:
		_fail("Rendered viewport image is missing or has incorrect dimensions.")
		return
	var image_error := image.save_png(output_path)
	if image_error != OK:
		_fail("Cannot save PNG: " + error_string(image_error))
		return

	var backend := "OpenGL (inferred from absence of RenderingDevice)"
	if RenderingServer.get_rendering_device() != null:
		backend = "Vulkan (RenderingDevice present in Godot 4.1)"
	var metadata := {
		"capture_kind": "actual Flight.tscn gameplay rendered in an offscreen SubViewport",
		"scene": "res://Flight.tscn",
		"image": output_path,
		"resolution": [capture_size.x, capture_size.y],
		"capture_view": capture_view,
		"random_seed": 604,
		"engine_version": Engine.get_version_info(),
		"display_driver": DisplayServer.get_name(),
		"render_backend": backend,
		"video_adapter": RenderingServer.get_video_adapter_name(),
		"video_adapter_api_version": RenderingServer.get_video_adapter_api_version(),
		"rendering_method_setting": ProjectSettings.get_setting("rendering/renderer/rendering_method", "forward_plus"),
		"msaa_3d": capture_viewport.msaa_3d,
		"camera_path": str(COCKPIT_PATH),
		"camera_fov_degrees": cockpit.fov,
		"camera_near": cockpit.near,
		"camera_far": cockpit.far,
		"camera_global_transform": _transform_data(cockpit.global_transform),
		"gameplay_process_frames": GAMEPLAY_FRAMES,
		"frozen_settle_frames": SETTLE_FRAMES,
		"limitations": [
			"Single still; not a motion stability or performance benchmark.",
			"Scene processing frozen after early gameplay; shader TIME may continue.",
			"Random disturbances are seeded; shader time/driver differences still prevent bit-identical captures.",
			"Root window is unfocusable and offscreen; image is a GPU viewport capture, not a desktop screenshot.",
			"Existing gameplay may log missing YawLeft input-action warnings; capture does not modify input bindings."
		]
	}
	var metadata_path := output_path.get_basename() + ".json"
	var metadata_file := FileAccess.open(metadata_path, FileAccess.WRITE)
	if metadata_file == null:
		_fail("PNG saved, but metadata could not be opened: " + error_string(FileAccess.get_open_error()))
		return
	metadata_file.store_string(JSON.stringify(metadata, "\t") + "\n")
	var metadata_error := metadata_file.get_error()
	metadata_file.close()
	if metadata_error != OK:
		_fail("PNG saved, but metadata write failed: " + error_string(metadata_error))
		return
	print("Cockpit capture saved: " + output_path)
	print("Capture metadata saved: " + metadata_path)
	capture_viewport.queue_free()
	await process_frame
	# Defer exit until coroutine locals (including loaded resources) are released.
	quit.call_deferred(0)


func _vector_data(value: Vector3) -> Array:
	return [value.x, value.y, value.z]


func _transform_data(value: Transform3D) -> Dictionary:
	return {
		"origin": _vector_data(value.origin),
		"basis_x": _vector_data(value.basis.x),
		"basis_y": _vector_data(value.basis.y),
		"basis_z": _vector_data(value.basis.z)
	}
