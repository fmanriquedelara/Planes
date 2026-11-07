"""Run with Blender 3.6 --background --python this_file.py. Source is read only."""
import bpy, json, hashlib
from pathlib import Path
from mathutils import Vector, Matrix

HERE=Path(__file__).resolve().parent
ASSET=HERE.parent
REPO=ASSET.parent.parent
SOURCE=ASSET/'EurofighterCockpit.blend'
source_hash=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
base=bpy.context.scene
base.name='Comparison base'
for obj in list(base.objects):
    if obj.type in {'CAMERA','LIGHT'}: bpy.data.objects.remove(obj,do_unlink=True)
for obj in base.objects:
    if obj.type=='MESH':
        obj.color=(.02,.68,.85,1)
        # The transparent windscreen/combiner panes would mask the hardware in
        # a solid comparison pass. Their modeled structural edges stay visible.
        if 'OpticalGlass' in obj.name: obj.hide_render=True; obj.hide_set(True)
config=json.loads((HERE/'camera-fit.json').read_text())
entries=config.get('cameras',config)
refs={'front':'front.png','oblique':'oblique.png','hud-day':'detail-pass/hud-day.png'}
report={'source_blend_sha256':source_hash,'source_glb_sha256':hashlib.sha256((ASSET/'EurofighterCockpit.glb').read_bytes()).hexdigest(),'geometry_modified':False,'glass_panes_hidden_for_comparison':True,'cameras':entries}
for name,relative in refs.items():
    cfg=entries[name]
    scene=base.copy();scene.name='Compare '+name
    bpy.context.window.scene=scene
    data=bpy.data.cameras.new('Reference '+name)
    cam=bpy.data.objects.new('Reference '+name,data);scene.collection.objects.link(cam)
    cam.location=cfg['location_m']
    if 'camera_matrix_columns' in cfg: cam.rotation_euler=Matrix(cfg['camera_matrix_columns']).transposed().to_euler()
    elif 'rotation_euler_rad' in cfg: cam.rotation_euler=cfg['rotation_euler_rad']
    else: cam.rotation_euler=(Vector(cfg['target_m'])-cam.location).to_track_quat('-Z','Y').to_euler()
    data.lens=cfg['lens_mm'];data.sensor_width=36;data.sensor_fit='HORIZONTAL'
    data.shift_x=cfg.get('shift_x',0);data.shift_y=cfg.get('shift_y',0)
    data.clip_start=.01;data.clip_end=100
    photo=bpy.data.images.load(str(REPO/'references/eurofighter-cockpit/user'/relative),check_existing=True)
    photo.pack()
    data.show_background_images=True
    bg=data.background_images.new();bg.image=photo;bg.alpha=.5;bg.display_depth='FRONT';bg.frame_method='FIT'
    scene.camera=cam
    scene.render.engine='BLENDER_WORKBENCH'
    scene.display.shading.light='STUDIO';scene.display.shading.studiolight_rotate_z=.4
    scene.display.shading.color_type='OBJECT';scene.display.shading.show_shadows=True
    scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH'
    scene.display.shading.curvature_ridge_factor=1.4;scene.display.shading.curvature_valley_factor=1.2
    scene.display.shading.show_specular_highlight=False
    scene.display.render_aa='16'
    scene.render.film_transparent=True
    scene.view_settings.view_transform='Standard';scene.view_settings.look='Medium High Contrast';scene.view_settings.exposure=0
    scene.render.resolution_x,scene.render.resolution_y=cfg.get('resolution',list(photo.size))
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
    scene.render.filepath=str(HERE/(name+'-model.png'))
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                area.spaces.active.region_3d.view_perspective='CAMERA'
                area.spaces.active.shading.type='SOLID'
                area.spaces.active.shading.color_type='OBJECT'
    bpy.ops.render.render(write_still=True)
bpy.context.window.scene=bpy.data.scenes['Compare front']
bpy.data.scenes.remove(base)
bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'comparison.blend'))
(HERE/'comparison-report.json').write_text(json.dumps(report,indent=2))
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==source_hash
