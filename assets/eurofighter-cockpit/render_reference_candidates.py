import bpy,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'EurofighterCockpit.blend'))
s=bpy.context.scene;c=s.camera;s.cycles.samples=8;s.render.resolution_x=600;s.render.resolution_y=740;s.render.resolution_percentage=100
poses={
 'near45':([-.5,0,.80],[.65,0,-.23],45),
 'high55':([-.65,0,1.10],[.60,0,-.27],55),
 'far110':([-2,0,2.4],[.45,0,-.25],110),
 'higher150':([-3,0,3.5],[.5,0,-.30],150)}
out=ROOT/'artifacts/camera-candidates';out.mkdir(parents=True,exist_ok=True)
for name,(loc,target,lens) in poses.items():
 c.location=loc;c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=lens;c.data.sensor_width=36;c.data.sensor_fit='HORIZONTAL'
 s.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
