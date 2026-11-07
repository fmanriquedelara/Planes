"""Read native cloud material parameters without editing engine content."""
import json
import pathlib
import unreal

material = unreal.load_asset("/Engine/EngineSky/VolumetricClouds/m_SimpleVolumetricCloud_Inst")
result = {"material": material.get_path_name(), "scalar": {}, "vector": {}}
for name in unreal.MaterialEditingLibrary.get_scalar_parameter_names(material):
    result["scalar"][str(name)] = unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(material, name)
for name in unreal.MaterialEditingLibrary.get_vector_parameter_names(material):
    value = unreal.MaterialEditingLibrary.get_material_instance_vector_parameter_value(material, name)
    result["vector"][str(name)] = [value.r, value.g, value.b, value.a]
output = pathlib.Path(unreal.Paths.project_dir()) / "artifacts" / "cloud-parameters.json"
output.write_text(json.dumps(result, indent=2))
unreal.log("PLANES_CLOUD_PARAMETERS " + json.dumps(result))
