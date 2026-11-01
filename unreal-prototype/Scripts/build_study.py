"""Create the isolated visual-study map and a one-frame Movie Render Queue job."""
import json
import math
import pathlib
import sys
import unreal

ROOT = pathlib.Path(unreal.Paths.project_dir()).resolve()
REPO = ROOT.parent
OUT = ROOT / "artifacts"
OUT.mkdir(exist_ok=True)
ASSETS = unreal.AssetToolsHelpers.get_asset_tools()
LEVEL = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTORS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def log(message):
    unreal.log("PLANES_STUDY " + message)


def setp(obj, name, value):
    try:
        obj.set_editor_property(name, value)
        return True
    except Exception as error:
        log("OPTIONAL {}.{}: {}".format(obj.get_class().get_name(), name, error))
        return False


def spawn(cls, label, location=(0, 0, 0), rotation=(0, 0, 0)):
    actor = ACTORS.spawn_actor_from_class(cls, unreal.Vector(*location), unreal.Rotator(pitch=rotation[0], yaw=rotation[1], roll=rotation[2]))
    actor.set_actor_label(label)
    return actor


def flat_material(name, colour, roughness=.65, emissive=False, opacity=None, metallic=0):
    path = "/Game/Study/Materials/" + name
    mat = unreal.load_asset(path)
    if mat:
        return mat
    mat = ASSETS.create_asset(name, "/Game/Study/Materials", unreal.Material, unreal.MaterialFactoryNew())
    colour_node = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector)
    colour_node.set_editor_property("constant", unreal.LinearColor(*colour, 1))
    target = unreal.MaterialProperty.MP_EMISSIVE_COLOR if emissive else unreal.MaterialProperty.MP_BASE_COLOR
    unreal.MaterialEditingLibrary.connect_material_property(colour_node, "", target)
    scalar = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant)
    scalar.set_editor_property("r", roughness)
    unreal.MaterialEditingLibrary.connect_material_property(scalar, "", unreal.MaterialProperty.MP_ROUGHNESS)
    metal = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant)
    metal.set_editor_property("r", metallic)
    unreal.MaterialEditingLibrary.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    if emissive:
        setp(mat, "shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    if opacity is not None:
        setp(mat, "blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
        alpha = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant)
        alpha.set_editor_property("r", opacity)
        unreal.MaterialEditingLibrary.connect_material_property(alpha, "", unreal.MaterialProperty.MP_OPACITY)
        setp(mat, "two_sided", True)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def radar_material():
    path = "/Game/Study/Materials/M_PrototypeRadar"
    material = unreal.load_asset(path)
    if material:
        return material
    material = ASSETS.create_asset("M_PrototypeRadar", "/Game/Study/Materials", unreal.Material, unreal.MaterialFactoryNew())
    setp(material, "shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    uv = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionTextureCoordinate)
    custom = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionCustom)
    inp = unreal.CustomInput()
    inp.set_editor_property("input_name", "UV")
    custom.set_editor_property("inputs", [inp])
    custom.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    custom.set_editor_property("code", """
float2 p=UV*2-1;
float radius=length(p);
float rings=1-smoothstep(.01,.035,abs(frac(radius*3.0)-.5));
float cross=1-smoothstep(.006,.016,min(abs(p.x),abs(p.y)));
float rim=1-smoothstep(.012,.025,abs(radius-.92));
float contact=1-smoothstep(.008,.025,length(p-float2(.22,-.32)));
contact+=1-smoothstep(.008,.025,length(p-float2(-.42,.18)));
float sweep=pow(saturate(dot(normalize(p+float2(.0001,.0001)),normalize(float2(.5,.8)))),45.0)*.15;
float signal=(rings*.19+cross*.22+rim*.25+contact*.7+sweep)*step(radius,1);
return float3(25,850,120)*signal+float3(.1,1.0,.25);
""")
    unreal.MaterialEditingLibrary.connect_material_expressions(uv, "", custom, "UV")
    unreal.MaterialEditingLibrary.connect_material_property(custom, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


log("Creating map")
if unreal.EditorAssetLibrary.does_asset_exist("/Game/Maps/CockpitStudy"):
    if not LEVEL.load_level("/Game/Maps/CockpitStudy"):
        raise RuntimeError("Cannot load existing study map")
    for existing in list(ACTORS.get_all_level_actors()):
        if existing.get_class().get_name() not in ["WorldSettings", "DefaultPhysicsVolume"]:
            ACTORS.destroy_actor(existing)
else:
    if not LEVEL.new_level("/Game/Maps/CockpitStudy"):
        raise RuntimeError("Cannot create study map")
manager = unreal.InterchangeManager.get_interchange_manager_scripted()
source = manager.create_source_data(str(REPO / "Shark 600" / "saab_jas_39a_gripen_detailed_cockpit.glb"))
params = unreal.ImportAssetParameters()
params.is_automated = True
params.replace_existing = True
log("Importing Gripen scene")
if not manager.import_scene("/Game/Aircraft/Gripen", source, params):
    raise RuntimeError("Interchange Gripen scene import failed")
imported = list(ACTORS.get_all_level_actors())
log("Imported actors: " + str(len(imported)))
for path in unreal.EditorAssetLibrary.list_assets("/Game/Aircraft/Gripen", recursive=True, include_folder=False):
    asset = unreal.load_asset(path)
    if isinstance(asset, unreal.StaticMesh):
        settings = asset.get_editor_property("nanite_settings")
        if settings.enabled:
            settings.enabled = False
            asset.set_editor_property("nanite_settings", settings)
            unreal.EditorAssetLibrary.save_loaded_asset(asset)
AIRCRAFT_ALTITUDE = 180000.0
for actor in imported:
    if actor.get_attach_parent_actor() is None:
        p = actor.get_actor_location()
        actor.set_actor_location(unreal.Vector(p.x, p.y, p.z + AIRCRAFT_ALTITUDE), False, False)

dark = flat_material("M_InteriorDark", (.025, .035, .045), .7)
glass = flat_material("M_CanopyGlass", (.055, .10, .14), emissive=True, opacity=.025)
screen = radar_material()
hud_glass = flat_material("M_HUDGlass", (.04, .12, .08), emissive=True, opacity=.015)
mirror = flat_material("M_CanopyMirror", (.035, .05, .065), .24, metallic=1)
material_names = []
for actor in imported:
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        for slot in range(component.get_num_materials()):
            mat = component.get_material(slot)
            if not mat:
                continue
            name = mat.get_name().lower()
            material_names.append(name)
            if "jet_flame" in name or "gunfire" in name:
                component.set_visibility(False, True)
            elif name in ["dynamic_mfd_trans", "dynamic_glass_tone"]:
                component.set_material(slot, hud_glass)
                setp(component, "cast_shadow", False)
            elif "dynamic_glass" in name or "empty_glass" in name:
                component.set_material(slot, glass)
                setp(component, "cast_shadow", False)
            elif name == "dynamic_mfd":
                component.set_material(slot, screen)
            elif name == "dynamic_mirror":
                component.set_material(slot, mirror)
            elif name in ["saab_jas39a_inside", "saab_jas39a_interior", "mesh1"]:
                component.set_material(slot, dark)

log("Creating native atmosphere")
sun = spawn(unreal.DirectionalLight, "Warm low sun", rotation=(-23, -42, 0))
sun_component = sun.get_component_by_class(unreal.DirectionalLightComponent)
sun_component.set_intensity(45000)
sun_component.set_light_color(unreal.LinearColor(1, .84, .65, 1))
setp(sun_component, "atmosphere_sun_light", True)
setp(sun_component, "cast_cloud_shadows", True)
setp(sun_component, "light_source_angle", .65)
spawn(unreal.SkyAtmosphere, "Native atmospheric scattering")
sky = spawn(unreal.SkyLight, "Dynamic sky fill")
sky_component = sky.get_component_by_class(unreal.SkyLightComponent)
setp(sky_component, "real_time_capture", True)
sky_component.set_intensity(2)
cloud = spawn(unreal.VolumetricCloud, "Native volumetric cumulus")
cloud_component = cloud.get_component_by_class(unreal.VolumetricCloudComponent)
setp(cloud_component, "layer_bottom_altitude", 2.2)
setp(cloud_component, "layer_height", 2.8)
cloud_mat = unreal.load_asset("/Engine/EngineSky/VolumetricClouds/m_SimpleVolumetricCloud_Inst")
if cloud_mat:
    setp(cloud_component, "material", cloud_mat)

ocean_mat = flat_material("M_Sea", (.012, .06, .085), .2)
ocean = spawn(unreal.StaticMeshActor, "Ocean to horizon", location=(0, 0, 0))
ocean.static_mesh_component.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Plane"))
ocean.static_mesh_component.set_material(0, ocean_mat)
ocean.set_actor_scale3d(unreal.Vector(200000, 200000, 1))

sys.path.insert(0, str(ROOT / "Scripts"))
from terrain_study import create_terrain
terrain_report = create_terrain(ROOT, ACTORS, ASSETS)

camera = spawn(unreal.CineCameraActor, "PilotEye", location=(503, 0, AIRCRAFT_ALTITUDE + 65), rotation=(-4, 0, 0))
camera.set_editor_property("auto_activate_for_player", unreal.AutoReceiveInput.PLAYER0)
cc = camera.get_cine_camera_component()
filmback = cc.get_editor_property("filmback")
filmback.sensor_width = 36
filmback.sensor_height = 22.5
cc.set_editor_property("filmback", filmback)
cc.set_editor_property("current_focal_length", 18.0)
cc.set_editor_property("current_aperture", 8.0)
focus = cc.get_editor_property("focus_settings")
focus.focus_method = unreal.CameraFocusMethod.DISABLE
cc.set_editor_property("focus_settings", focus)
pp = cc.get_editor_property("post_process_settings")
setp(pp, "override_auto_exposure_method", True)
setp(pp, "auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
setp(pp, "override_auto_exposure_apply_physical_camera_exposure", True)
setp(pp, "auto_exposure_apply_physical_camera_exposure", True)
setp(pp, "override_camera_iso", True)
setp(pp, "camera_iso", 100.0)
setp(pp, "override_camera_shutter_speed", True)
setp(pp, "camera_shutter_speed", 128.0)
setp(pp, "override_depth_of_field_fstop", True)
setp(pp, "depth_of_field_fstop", 8.0)
setp(pp, "override_auto_exposure_bias", True)
setp(pp, "auto_exposure_bias", 0.0)
setp(pp, "override_auto_exposure_min_brightness", True)
setp(pp, "override_auto_exposure_max_brightness", True)
setp(pp, "auto_exposure_min_brightness", 10.5)
setp(pp, "auto_exposure_max_brightness", 10.5)
cc.set_editor_property("post_process_settings", pp)

log("Creating sequence and render configuration")
sequence = unreal.load_asset("/Game/Cinematics/CockpitSequence")
if not sequence:
    sequence = ASSETS.create_asset("CockpitSequence", "/Game/Cinematics", unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
sequence.set_display_rate(unreal.FrameRate(24, 1))
for old_binding in sequence.get_bindings():
    old_binding.remove()
for old_track in sequence.get_tracks():
    sequence.remove_track(old_track)
sequence.set_playback_start(0)
sequence.set_playback_end(2)
binding = sequence.add_possessable(camera)
cut_track = sequence.add_track(unreal.MovieSceneCameraCutTrack)
cut = cut_track.add_section()
cut.set_range(0, 2)
binding_id = unreal.MovieSceneObjectBindingID()
binding_id.set_editor_property("guid", binding.get_id())
cut.set_camera_binding_id(binding_id)
unreal.EditorAssetLibrary.save_loaded_asset(sequence)

config = unreal.load_asset("/Game/Cinematics/CockpitRender")
if not config:
    config = ASSETS.create_asset("CockpitRender", "/Game/Cinematics", unreal.MoviePipelinePrimaryConfig, unreal.MoviePipelinePrimaryConfigFactory())
output = config.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
output.output_directory = unreal.DirectoryPath(str(OUT))
output.output_resolution = unreal.IntPoint(1600, 1000)
output.file_name_format = "cockpit.{frame_number}"
output.use_custom_playback_range = True
output.custom_start_frame = 0
output.custom_end_frame = 1
config.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPassBase)
config.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_PNG)
aa = config.find_or_add_setting_by_class(unreal.MoviePipelineAntiAliasingSetting)
aa.temporal_sample_count = 4
aa.spatial_sample_count = 1
aa.engine_warm_up_count = 48
aa.render_warm_up_count = 24
unreal.EditorAssetLibrary.save_loaded_asset(config)
unreal.EditorAssetLibrary.save_directory("/Game", only_if_is_dirty=True, recursive=True)
if not LEVEL.save_current_level():
    raise RuntimeError("Study map failed to save")
camera_position = camera.get_actor_location()
report = {"engine": unreal.SystemLibrary.get_engine_version(), "imported_actors": len(imported), "materials": sorted(set(material_names)), "camera_location_cm": [camera_position.x, camera_position.y, camera_position.z], "map": "/Game/Maps/CockpitStudy", "sequence": sequence.get_path_name(), "render_config": config.get_path_name(), "terrain": terrain_report, "intended_capture_pipeline": "real GPU Movie Render Queue", "render_verified_by_build": False, "limitations": ["Visual study, not interactive flight physics", "Existing cockpit texture detail limits", "Synthetic radar displays are demonstration art, not flight data", "Procedural countryside is a bounded visual study, not mapped real terrain"]}
(OUT / "build-report.json").write_text(json.dumps(report, indent=2))
log("BUILD_COMPLETE " + json.dumps(report))
