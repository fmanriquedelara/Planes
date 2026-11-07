import bpy,json
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=r'C:\Repositories\Planes\Godot\Planes\HighResEurofighter.glb')
for o in bpy.context.scene.objects:
 if o.type=='MESH':
  pts=[o.matrix_world @ Vector(v) for v in o.bound_box]
  print('BOUND',o.name,o.data.name,[round(min(p[i] for p in pts)*.1,3) for i in range(3)],[round(max(p[i] for p in pts)*.1,3) for i in range(3)], [m.name for m in o.data.materials])
