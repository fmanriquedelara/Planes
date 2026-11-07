import bpy,json
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
D=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(D.parent.parent/'EurofighterCockpit.blend'))
s=bpy.context.scene
for o in s.objects:
 if o.type=='MESH':
  o.color=(.02,.68,.85,1)
  if 'OpticalGlass' in o.name:o.hide_render=True
s.render.engine='BLENDER_WORKBENCH';s.display.shading.color_type='OBJECT';s.display.shading.light='STUDIO';s.display.shading.show_cavity=True;s.display.render_aa='8'
s.render.film_transparent=True;s.render.resolution_x=499;s.render.resolution_y=615;s.render.resolution_percentage=100;s.render.image_settings.color_mode='RGBA'
cam=s.camera;cam.data.sensor_fit='HORIZONTAL';cam.data.sensor_width=36;cam.data.shift_x=0;cam.data.shift_y=-.09
trials=[('compromise',(-.35,0,1.0),(.65,0,-.22),42)]
report=[]
for name,loc,target,lens in trials:
 cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens
 s.render.filepath=str(D/(name+'.png'));bpy.ops.render.render(write_still=True)
 item=dict(name=name,location_m=loc,target_m=target,lens_mm=lens,landmarks=[])
 for n,p in [('bowtop',(.93,0,.315)),('leftscreen',(.809,.235,-.302)),('rightscreen',(.809,-.235,-.302)),('hudbar',(.724,0,-.108)),('cushionrear',(-.04,0,-.62)),('cushionfront',(.61,0,-.62))]:
  q=world_to_camera_view(s,cam,Vector(p));item['landmarks'].append([n,q.x*499,(1-q.y)*615])
 report.append(item)
(D/'compromise.json').write_text(json.dumps(report,indent=2))

