import bpy,json
from mathutils import Vector,Matrix
from pathlib import Path
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(ROOT.parents[1]/'Godot/Planes/HighResEurofighter.glb'))
report=[]
for o in bpy.context.scene.objects:
 if o.type!='MESH':continue
 o.data.transform(o.matrix_world);o.matrix_world=Matrix.Identity(4)
 for v in o.data.vertices:v.co*=.1
 color={'Object_4':(1,.04,.02,1),'Object_6':(.05,1,.02,1),'Object_12':(.1,.1,1,1)}.get(o.name,(.7,.7,.7,1))
 o.color=color
 if o.name not in ['Object_4','Object_6','Object_12']:o.hide_render=True
 neighbors={v.index:set() for v in o.data.vertices}
 for e in o.data.edges:a,b=e.vertices;neighbors[a].add(b);neighbors[b].add(a)
 unseen=set(neighbors)
 while unseen:
  start=unseen.pop();todo=[start];part={start}
  while todo:
   for nxt in neighbors[todo.pop()]:
    if nxt in unseen:unseen.remove(nxt);part.add(nxt);todo.append(nxt)
  coords=[o.data.vertices[i].co for i in part]
  lo=[min(v[j] for v in coords) for j in range(3)];hi=[max(v[j] for v in coords) for j in range(3)]
  if hi[0]>6 and lo[0]<8.6 and hi[2]>.9:
   report.append({'object':o.name,'seed':start,'verts':len(part),'min':lo,'max':hi})
(ROOT/'source-components.json').write_text(json.dumps(report,indent=2))
scene=bpy.context.scene
bpy.ops.object.camera_add(location=(6.5,0,1.225));cam=bpy.context.object;scene.camera=cam;cam.rotation_euler=Vector((1,0,-.07)).to_track_quat('-Z','Y').to_euler();cam.data.lens=18;cam.data.clip_start=.02
scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='OBJECT';scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.render.filepath=str(ROOT/'source-part-diagnostic.png');bpy.ops.render.render(write_still=True)
