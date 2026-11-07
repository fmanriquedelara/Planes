"""Import the Godot gun sound used by the controller's held A button."""
import pathlib
import unreal


def import_study_audio(project_root):
    destination = "/Game/StudyAudio"
    if unreal.EditorAssetLibrary.does_asset_exist(destination + "/GunTrimmed"):
        return

    source = pathlib.Path(project_root).parent / "Godot" / "Sounds" / "GunTrimmed.wav"
    task = unreal.AssetImportTask()
    task.filename = str(source)
    task.destination_path = destination
    task.automated = True
    task.save = True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    if not unreal.EditorAssetLibrary.does_asset_exist(destination + "/GunTrimmed"):
        raise RuntimeError(f"Could not import {source}")
