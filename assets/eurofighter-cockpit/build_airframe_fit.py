"""Fit-only derivative: remove disconnected obsolete front canopy bow.
Source attribution and CC BY-NC-SA4.0 inherited; never overwrite original.
"""
import bpy,bmesh,json
from mathutils import Matrix
from pathlib import Path
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(ROOT.parents[1]/'Godot/Planes/HighResEurofighter.glb'))
o=bpy.data.objects['Object_4'];o.data.transform(o.matrix_world);o.matrix_world=Matrix.Identity(4)
for v in o.data.vertices:v.co*=.1
neighbors={v.index:set() for v in o.data.vertices}
for e in o.data.edges:a,b=e.vertices;neighbors[a].add(b);neighbors[b].add(a)
part={6744};todo=[6744]
while todo:
 for nxt in neighbors[todo.pop()]:
  if nxt not in part:part.add(nxt);todo.append(nxt)
assert len(part)==91, 'Source topology changed; re-inspect old bow island before removal'
coords=[o.data.vertices[i].co for i in part]
lo=[min(v[j] for v in coords) for j in range(3)];hi=[max(v[j] for v in coords) for j in range(3)]
assert 6.97<lo[0]<6.98 and 7.22<hi[0]<7.23 and 1.33<hi[2]<1.34
bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.verts[i] for i in part],context='VERTS');bm.to_mesh(o.data);bm.free();o.name='EF_AirframeFit'
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
bpy.ops.export_scene.gltf(filepath=str(ROOT/'EF_AirframeFit.glb'),export_format='GLB',use_selection=True,export_apply=True,export_yup=True)
o.data.calc_loop_triangles()
(ROOT/'airframe-fit-metrics.json').write_text(json.dumps({'source':'Godot/Planes/HighResEurofighter.glb','source_object':'Object_4','removed_vertices':91,'removed_bounds_min_m':lo,'removed_bounds_max_m':hi,'remaining_triangles':len(o.data.loop_triangles),'coordinates':'full aircraft metres; Blender +X forward,+Y left,+Z up; attach rig origin scale1','license':'CC BY-NC-SA 4.0, original author bohmerang'},indent=2))
