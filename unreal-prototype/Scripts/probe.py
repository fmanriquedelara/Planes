import unreal
import json
import pathlib

root = pathlib.Path(unreal.Paths.project_dir())
output = root / "artifacts"
output.mkdir(exist_ok=True)
names = ["InterchangeManager", "ImportAssetParameters", "MoviePipelinePrimaryConfig", "MoviePipelineMasterConfig", "MoviePipelineQueue", "MoviePipelineDeferredPassBase", "MoviePipelineImageSequenceOutput_PNG", "VolumetricCloud", "SkyAtmosphere", "CineCameraActor", "MovieSceneCameraCutTrack"]
result = {name: hasattr(unreal, name) for name in names}
for name in ["import_scene", "create_source_data"]:
    result[name] = str(getattr(unreal.InterchangeManager, name).__doc__)
result["engine_version"] = unreal.SystemLibrary.get_engine_version()
(output / "probe.json").write_text(json.dumps(result, indent=2))
unreal.log("PLANES_PROBE " + json.dumps(result))
