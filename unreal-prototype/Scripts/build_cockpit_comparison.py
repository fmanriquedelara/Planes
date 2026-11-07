"""Build isolated Eurofighter comparison maps; never save the default study map."""
import json
import hashlib
import os
import pathlib
import sys
import unreal

ROOT = pathlib.Path(unreal.Paths.project_dir()).resolve()
REPO = ROOT.parent
sys.path.insert(0, str(ROOT / "Scripts"))
from study_audio import import_study_audio
DETAIL = os.environ.get("PLANES_COCKPIT_VARIANT", "detail") == "detail"
VARIANT = "detail" if DETAIL else "baseline"
MAP = "/Game/Maps/EurofighterCockpitStudy" if DETAIL else "/Game/Maps/EurofighterCockpitBaseline"
ASSET_ROOT = "/Game/EurofighterCockpitStudy"
OUT = ROOT / "artifacts" / "ue008" / VARIANT
OUT.mkdir(parents=True, exist_ok=True)
LEVEL = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTORS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ASSETS = unreal.AssetToolsHelpers.get_asset_tools()
ALTITUDE = 180000.0
EYE = unreal.Vector(650, 0, ALTITUDE + 122.5)


def log(message):
    unreal.log("COCKPIT_COMPARISON " + message)


def import_scene(source, destination):
    before = {a.get_path_name() for a in ACTORS.get_all_level_actors()}
    manager = unreal.InterchangeManager.get_interchange_manager_scripted()
    params = unreal.ImportAssetParameters()
    params.is_automated = True
    params.replace_existing = True
    if not manager.import_scene(destination, manager.create_source_data(str(source)), params):
        raise RuntimeError("Cannot import " + str(source))
    return [a for a in ACTORS.get_all_level_actors() if a.get_path_name() not in before]


def material(name, colour, roughness, metallic=0.0, opacity=None, emissive=False):
    path = ASSET_ROOT + "/Materials"
    mat = unreal.load_asset(path + "/" + name)
    if mat:
        return mat
    mat = ASSETS.create_asset(name, path, unreal.Material, unreal.MaterialFactoryNew())
    mel = unreal.MaterialEditingLibrary
    node = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector)
    node.set_editor_property("constant", unreal.LinearColor(*colour, 1))
    mel.connect_material_property(node, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR if emissive else unreal.MaterialProperty.MP_BASE_COLOR)
    for value, prop in [(roughness, unreal.MaterialProperty.MP_ROUGHNESS), (metallic, unreal.MaterialProperty.MP_METALLIC)]:
        scalar = mel.create_material_expression(mat, unreal.MaterialExpressionConstant)
        scalar.set_editor_property("r", value)
        mel.connect_material_property(scalar, "", prop)
    if opacity is not None:
        mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
        mat.set_editor_property("two_sided", True)
        scalar = mel.create_material_expression(mat, unreal.MaterialExpressionConstant)
        scalar.set_editor_property("r", opacity)
        mel.connect_material_property(scalar, "", unreal.MaterialProperty.MP_OPACITY)
    if emissive:
        mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def legend_material(cockpit_root):
    """Explicit paint decal material; stable alpha and UV0 across Interchange versions."""
    texture_paths = unreal.EditorAssetLibrary.list_assets(cockpit_root, recursive=True, include_folder=False)
    tex = next((unreal.load_asset(p) for p in texture_paths if p.rsplit('/', 1)[-1].split('.')[0].lower() == 'legends'), None)
    if not tex:
        raise RuntimeError("Missing label atlas")
    tex.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    unreal.EditorAssetLibrary.save_loaded_asset(tex)
    path = ASSET_ROOT + "/Materials"
    mat = unreal.load_asset(path + "/M_LabelPaint")
    if not mat:
        mat = ASSETS.create_asset("M_LabelPaint", path, unreal.Material, unreal.MaterialFactoryNew())
    mel = unreal.MaterialEditingLibrary
    mel.delete_all_material_expressions(mat)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
    mat.set_editor_property("two_sided", True)
    mat.set_editor_property("opacity_mask_clip_value", .15)
    sample = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample)
    sample.set_editor_property("texture", tex)
    mel.connect_material_property(sample, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(sample, "A", unreal.MaterialProperty.MP_OPACITY_MASK)
    scalar = mel.create_material_expression(mat, unreal.MaterialExpressionConstant)
    scalar.set_editor_property("r", .7)
    mel.connect_material_property(scalar, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


if DETAIL and not (REPO / "assets/eurofighter-cockpit/EurofighterCockpit.glb").exists():
    raise RuntimeError("Build the separate Blender cockpit asset first")
fit_source = REPO / "assets/eurofighter-cockpit/EF_AirframeFit.glb"
if DETAIL and not fit_source.exists():
    raise RuntimeError("Build the separate airframe fit derivative first")
input_hashes = {}
if DETAIL:
    snapshot_dir = OUT / "input"
    snapshot_dir.mkdir(exist_ok=True)
    for filename in ["EurofighterCockpit.glb", "EF_AirframeFit.glb"]:
        data = (REPO / "assets/eurofighter-cockpit" / filename).read_bytes()
        (snapshot_dir / filename).write_bytes(data)
        input_hashes[filename] = hashlib.sha256(data).hexdigest()
    fit_source = snapshot_dir / "EF_AirframeFit.glb"
source_map_file = ROOT / "Content/Maps/CockpitStudy.umap"
source_hash = hashlib.sha256(source_map_file.read_bytes()).hexdigest()
if not unreal.EditorAssetLibrary.does_asset_exist(MAP):
    if not LEVEL.load_level("/Game/Maps/CockpitStudy"):
        raise RuntimeError("Cannot load existing environment")
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if not unreal.EditorLoadingAndSavingUtils.save_map(world, MAP):
        raise RuntimeError("Cannot create isolated map " + MAP)
# SaveMap writes a copy without activating it. Explicitly load the destination.
if not LEVEL.load_level(MAP):
    raise RuntimeError("Cannot activate isolated map " + MAP)
assert unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_path_name().startswith(MAP + ".")
actors = list(ACTORS.get_all_level_actors())
rig = next(a for a in actors if "PlanesPilotRig" in [str(t) for t in a.tags])
camera = next(a for a in actors if "PlanesPilotCamera" in [str(t) for t in a.tags])
remove = []
for actor in actors:
    parent = actor.get_attach_parent_actor()
    while parent:
        if parent == rig:
            if actor != camera:
                remove.append(actor)
            break
        parent = parent.get_attach_parent_actor()
for actor in reversed(remove):
    ACTORS.destroy_actor(actor)
rig.set_editor_property("tags", ["PlanesPilotRig", "PlanesAircraftEurofighter"])
rig.set_actor_location(unreal.Vector(0, 0, ALTITUDE), False, False)
camera.set_actor_location(EYE, False, False)
camera.set_actor_rotation(unreal.Rotator(pitch=-4, yaw=0, roll=0), False)

source = REPO / "Godot/Planes/HighResEurofighter.glb"
aircraft = import_scene(source, ASSET_ROOT + "/Airframe")
glass = material("M_OriginalGlass", (.055, .10, .14), .1, opacity=.025, emissive=True)
hud_glass = material("M_OriginalHUD", (.04, .12, .08), .1, opacity=.015, emissive=True)
parts = []
hidden = []
for actor in aircraft:
    if actor.get_attach_parent_actor() is None:
        pos = actor.get_actor_location()
        scale = actor.get_actor_scale3d()
        actor.set_actor_scale3d(unreal.Vector(scale.x * .1, scale.y * .1, scale.z * .1))
        actor.set_actor_location(unreal.Vector(pos.x * .1, pos.y * .1, pos.z * .1 + ALTITUDE), False, False)
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        mesh = component.static_mesh
        mesh_name = mesh.get_name().lower() if mesh else ""
        names = []
        for slot in range(component.get_num_materials()):
            mat = component.get_material(slot)
            name = mat.get_name().lower() if mat else ""
            names.append(name)
            if name == "glass":
                component.set_material(slot, glass)
                component.set_editor_property("cast_shadow", False)
            elif name == "material":
                component.set_material(slot, hud_glass)
                component.set_editor_property("cast_shadow", False)
        duplicate = actor.get_actor_label().lower() == "object_8" or mesh_name == "object_2"
        # Detail replacement hides both authored cockpit copies and original HUD.
        replaced = DETAIL and (actor.get_actor_label().lower() in ("object_4", "object_6", "object_8", "object_8_001", "object_10")
                               or "material" in names)
        if duplicate or replaced:
            component.set_visibility(False, True)
            component.set_hidden_in_game(True, True)
            hidden.append(actor.get_actor_label())
        parts.append({"actor": actor.get_actor_label(), "mesh": mesh_name, "materials": names,
                      "visible": not (duplicate or replaced)})

detail_actors = []
fit_actors = []
bow_components = []
if DETAIL:
    # Interchange may preserve old material bindings while renaming changed textures.
    # A content-addressed namespace keeps every revision's geometry and art together.
    cockpit_root = ASSET_ROOT + "/Cockpit/Revision_" + input_hashes["EurofighterCockpit.glb"][:12]
    detail_actors = import_scene(snapshot_dir / "EurofighterCockpit.glb", cockpit_root)
    labels = legend_material(cockpit_root)
    graphite = material("M_CockpitGraphite_v7", (.008, .011, .012), .86, metallic=0.0)
    painted_panel = material("M_CockpitPanel_v7", (.095, .115, .11), .70, metallic=0.0)
    optics = material("M_CockpitOptics", (.06, .09, .08), .08, opacity=.015, emissive=True)
    bow_clear = material("M_CanopyBowClear", (.035, .055, .06), .8, opacity=.025, emissive=True)
    for actor in detail_actors:
        if actor.get_attach_parent_actor() is None:
            pos = actor.get_actor_location()
            actor.set_actor_location(pos + EYE, False, False)
        for component in actor.get_components_by_class(unreal.StaticMeshComponent):
            for slot in range(component.get_num_materials()):
                mat = component.get_material(slot)
                if not mat:
                    continue
                if mat.get_name().lower().startswith('ef_canopybow_'):
                    tags = list(component.get_editor_property('component_tags'))
                    if 'PlanesCanopyBow' not in [str(tag) for tag in tags]:
                        tags.append('PlanesCanopyBow')
                    component.set_editor_property('component_tags', tags)
                    bow_components.append(component.get_path_name())
                    if mat.get_name().lower() == 'ef_canopybow_graphite':
                        component.set_material(slot, graphite)
                    elif mat.get_name().lower() == 'ef_canopybow_panelgrey':
                        component.set_material(slot, painted_panel)
                    continue
                if mat.get_name().lower() == 'ef_graphite':
                    component.set_material(slot, graphite)
                elif mat.get_name().lower() == 'ef_panelgrey':
                    component.set_material(slot, painted_panel)
                elif mat.get_name().lower() == 'ef_legends':
                    component.set_material(slot, labels)
                    component.set_editor_property("cast_shadow", False)
                elif mat.get_name().lower() == 'ef_opticalglass':
                    component.set_material(slot, optics)
                    component.set_editor_property("cast_shadow", False)
    fit_actors = import_scene(fit_source, ASSET_ROOT + "/AirframeFit")
    for actor in fit_actors:
        if actor.get_attach_parent_actor() is None:
            pos = actor.get_actor_location()
            actor.set_actor_location(pos + unreal.Vector(0, 0, ALTITUDE), False, False)

for actor in aircraft + detail_actors + fit_actors:
    for component in actor.get_components_by_class(unreal.SceneComponent):
        component.set_mobility(unreal.ComponentMobility.MOVABLE)
    if actor.get_attach_parent_actor() is None:
        actor.attach_to_actor(rig, "None", unreal.AttachmentRule.KEEP_WORLD,
                              unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)

for path in unreal.EditorAssetLibrary.list_assets(ASSET_ROOT, recursive=True, include_folder=False):
    asset = unreal.load_asset(path)
    if isinstance(asset, unreal.StaticMesh):
        settings = asset.get_editor_property("nanite_settings")
        settings.enabled = False
        asset.set_editor_property("nanite_settings", settings)
unreal.EditorAssetLibrary.save_directory(ASSET_ROOT, only_if_is_dirty=True, recursive=True)
if not LEVEL.save_current_level():
    raise RuntimeError("Comparison map failed to save")
import_study_audio(ROOT)
assert hashlib.sha256(source_map_file.read_bytes()).hexdigest() == source_hash, "Default map changed unexpectedly"
report = {"engine": unreal.SystemLibrary.get_engine_version(), "map": MAP, "variant": VARIANT,
          "source_map_unchanged": "/Game/Maps/CockpitStudy", "eye_cm": [650, 0, 122.5],
          "altitude_cm": ALTITUDE, "pitch_deg": -4, "original_scale": .1,
          "detail_scale": 1.0, "parts": parts, "hidden": hidden,
          "detail_actor_count": len(detail_actors), "render_verified": False,
          "native_material_revision": "matte-paint-v7" if DETAIL else "original",
          "canopy_bow_components": bow_components,
          "canopy_bow_clear_material": ASSET_ROOT + "/Materials/M_CanopyBowClear.M_CanopyBowClear" if DETAIL else None,
          "input_sha256": input_hashes,
          "default_map_sha256_before_after": source_hash}
(OUT / "build.json").write_text(json.dumps(report, indent=2))
log("BUILD_COMPLETE " + json.dumps(report))
