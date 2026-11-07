"""Build an original, reference-informed Eurofighter cockpit in Blender 3.6.
Coordinates: metres, +X forward, +Y pilot-left, +Z up, origin pilot eye.
Run with --background --factory-startup --python this_file.
"""
import bpy, math, json, random, struct
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True)
random.seed(42)
scene=bpy.context.scene; scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=1
def mat(name,color,rough=.5,metal=0,emission=0):
 m=bpy.data.materials.new(name);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 if emission:p.inputs['Emission'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emission
 m.diffuse_color=(*color,1);return m
graphite=mat('EF_Graphite',(0.008,.011,.012),.64,.15)
panel=mat('EF_PanelGrey',(.095,.115,.11),.52,.25)
rubber=mat('EF_Rubber',(.003,.004,.004),.79)
metal=mat('EF_Hardware',(.19,.22,.21),.42,.72)
fabric=mat('EF_OliveFabric',(.16,.18,.075),.91)
harness=mat('EF_Harness',(.19,.26,.22),.82)
yellow=mat('EF_SafetyYellow',(.83,.53,.035),.51)
red=mat('EF_SafetyRed',(.55,.035,.025),.48)
green=mat('EF_InstrumentLight',(.08,.55,.09),.4,0,.7)
glass=mat('EF_OpticalGlass',(.23,.36,.32),.09,.0)
p=glass.node_tree.nodes.get('Principled BSDF');p.inputs['Alpha'].default_value=.045;p.inputs['Transmission'].default_value=0;p.inputs['Specular'].default_value=.12;p.inputs['IOR'].default_value=1.46
glass.blend_method='BLEND';glass.use_screen_refraction=True;glass.show_transparent_back=True
def texmat(name,filename,alpha=False,emit=0):
 m=mat(name,(.7,.7,.7),.48)
 nodes=m.node_tree.nodes;p=nodes.get('Principled BSDF');t=nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(ROOT/'textures'/filename));m.node_tree.links.new(t.outputs['Color'],p.inputs['Base Color'])
 if alpha:
  m.node_tree.links.new(t.outputs['Alpha'],p.inputs['Alpha']);m.blend_method='CLIP';m.alpha_threshold=.35
 if emit:m.node_tree.links.new(t.outputs['Color'],p.inputs['Emission']);p.inputs['Emission Strength'].default_value=emit
 return m
display=texmat('EF_DisplayArt','instruments.png',emit=.32)
legend=texmat('EF_Legends','legends.png',True)
for m,file in [(fabric,'olive-weave.png'),(harness,'harness-weave.png')]:
 p=m.node_tree.nodes.get('Principled BSDF');t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(ROOT/'textures'/file));m.node_tree.links.new(t.outputs['Color'],p.inputs['Base Color'])
legends=json.loads((ROOT/'textures'/'legends.json').read_text())
def assign(o,m):o.data.materials.append(m);return o
def bevel(o,w=.002,segments=2):
 if w:
  o.data.use_auto_smooth=True
  b=o.modifiers.new('Manufactured edge radii','BEVEL');b.width=w;b.segments=segments
  n=o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL');n.keep_sharp=True
 return o
def box(name,loc,size,m=panel,b=.002):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=size
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);assign(o,m);bevel(o,b);return o
def mesh(name,verts,faces,m):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);scene.collection.objects.link(o);assign(o,m);return o
def cylinder(name,loc,radius,depth,m=metal,axis=(0,0,1),vertices=16):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=loc);o=bpy.context.object;o.name=name;o.rotation_euler=Vector(axis).to_track_quat('Z','Y').to_euler();assign(o,m);bevel(o,min(.001,radius*.15));return o
def ellipsoid(name,loc,size,m):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,location=loc);o=bpy.context.object;o.name=name;o.scale=size;assign(o,m)
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 for p in o.data.polygons:p.use_smooth=True
 return o
def tube(name,points,r,m=graphite,res=2):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=1;c.bevel_depth=r;c.bevel_resolution=res
 s=c.splines.new('POLY');s.points.add(len(points)-1)
 for p,v in zip(s.points,points):p.co=(*v,1)
 o=bpy.data.objects.new(name,c);scene.collection.objects.link(o);assign(o,m);return o
def quad(name,verts,m,uv=None):
 o=mesh(name,verts,[(0,1,2,3)],m)
 if uv:
  layer=o.data.uv_layers.new()
  for i,u in enumerate(uv):layer.data[i].uv=u
 return o
def face(name,x,y,z,w,h,m,uv=None):
 return quad(name,[(x,y+w/2,z-h/2),(x,y-w/2,z-h/2),(x,y-w/2,z+h/2),(x,y+w/2,z+h/2)],m,uv)
def label(t,x,y,z,h=.008,top=False):
 r=legends.get(t)
 if not r:return
 w=h*(r[2]-r[0])/(r[3]-r[1]);uv=[(r[0]/2048,1-r[3]/2048),(r[2]/2048,1-r[3]/2048),(r[2]/2048,1-r[1]/2048),(r[0]/2048,1-r[1]/2048)]
 if not top:face('Legend '+t,x,y,z,w,h,legend,uv)
 else:quad('Legend '+t,[(x-h/2,y+w/2,z),(x-h/2,y-w/2,z),(x+h/2,y-w/2,z),(x+h/2,y+w/2,z)],legend,uv)
def screw(x,y,z,axis=(-1,0,0),r=.0035):
 cylinder('Captive quarter-turn fastener',(x,y,z),r,.002,metal,axis,12)
 if axis==(-1,0,0):box('Fastener slot',(x-.0013,y,z),(.0005,r*1.3,.0007),rubber,0)
def front_button(x,y,z,w=.017,h=.015,text=None):
 box('Recessed key surround',(x+.003,y,z),(.008,w+.004,h+.004),rubber,.001)
 box('Tactile pushbutton',(x-.003,y,z),(.009,w,h),graphite,.0012)
 if text:label(text,x-.010,y,z,h*.38)
def knob(x,y,z,r=.009):
 cylinder('Knurled rotary control',(x,y,z),r,.018,graphite,(-1,0,0),24)
 for i in range(12):
  a=i*math.tau/12;box('Knurl',(x,y+r*math.sin(a),z+r*math.cos(a)),(.012,.0015,.0015),rubber,.0003)
 box('Rotary index',(x-.010,y,z+r*.35),(.0005,.0013,r*.7),metal,0)
# Revision 6: user-reference geometry, shared helpers/materials above.
exec(compile((ROOT/'geometry_v6.py').read_text(),str(ROOT/'geometry_v6.py'),'exec'))
# Convert and collapse per-material meshes for low section/draw count.
asset_objects=[o for o in scene.objects if o.type in {'MESH','CURVE'}]
bpy.ops.object.select_all(action='DESELECT')
for o in asset_objects:o.select_set(True)
bpy.context.view_layer.objects.active=asset_objects[0]
bpy.ops.object.convert(target='MESH')
for m in list(bpy.data.materials):
 parts=[o for o in scene.objects if o.type=='MESH' and len(o.data.materials)==1 and o.data.materials[0]==m]
 if not parts:continue
 bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();parts[0].name=m.name+'_Assembly'
 bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
assets=[o for o in scene.objects if o.type=='MESH']
for o in assets:
 o.data.calc_loop_triangles()
 if o.data.materials[0]==glass:o.visible_shadow=False
 if o.data.materials[0]==fabric:
  for uv in o.data.uv_layers.active.data:uv.uv*=8
pts=[o.matrix_world@Vector(v) for o in assets for v in o.bound_box]
stats={'coordinate_system':'Blender +X forward, +Y pilot-left, +Z up; metres; origin pilot eye','unreal_attachment_cm':[650,0,122.5],'source_fit_scale':.1,'bounds_min_m':[min(p[i] for p in pts) for i in range(3)],'bounds_max_m':[max(p[i] for p in pts) for i in range(3)],'triangles':sum(len(o.data.loop_triangles) for o in assets),'mesh_sections':len(assets),'materials':[o.data.materials[0].name for o in assets],'textures':[{'name':'instruments.png','size':[1536,512]},{'name':'legends.png','size':[2048,2048]}],'engine_authoring':bpy.app.version_string,'limitations':['Reference-informed visual model, not engineering survey','Illustrative static display art; no working avionics','No photographic pixels used as textures','Performance must be measured in Unreal']}
stats['textures']=[]
for file in sorted((ROOT/'textures').glob('*.png')):
 width,height=struct.unpack('>II',file.read_bytes()[16:24])
 stats['textures'].append({'name':file.name,'size':[width,height],'source_png_bytes':file.stat().st_size,'decoded_rgba8_bytes':width*height*4})
stats['texture_source_png_bytes']=sum(t['source_png_bytes'] for t in stats['textures'])
stats['texture_decoded_rgba8_bytes']=sum(t['decoded_rgba8_bytes'] for t in stats['textures'])
stats['texture_full_mip_chain_rgba8_estimate_bytes']=round(stats['texture_decoded_rgba8_bytes']*4/3)
stats['texture_memory_note']='Conservative decoded RGBA8 estimate, not measured VRAM. Unreal compression, mips and residency differ; 1536x512 display atlas is non-power-of-two.'
(ROOT/'asset-metrics.json').write_text(json.dumps(stats,indent=2))
for image in bpy.data.images:
 if image.filepath:image.pack()
bpy.ops.object.select_all(action='DESELECT')
for o in assets:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(ROOT/'EurofighterCockpit.glb'),export_format='GLB',use_selection=True,export_apply=True,export_yup=True)
# Neutral studio evidence, explicitly separate from Unreal evidence.
world=bpy.data.worlds.new('Neutral daylight studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.34,.43,.55,1);world.node_tree.nodes['Background'].inputs[1].default_value=.3;scene.world=world
def area(name,loc,energy,size,target):
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=energy;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
area('Large daylight key',(-1,1.2,2.0),180,3,(.4,0,-.4));area('Front fill',(-1,-1,1),60,2,(.5,0,-.4))
bpy.ops.object.camera_add(location=(0,0,0));cam=bpy.context.object;cam.name='PilotEye_Reference';scene.camera=cam
cam.rotation_euler=Vector((1,0,-math.tan(math.radians(4)))).to_track_quat('-Z','Y').to_euler();cam.data.lens=18;cam.data.sensor_width=36;cam.data.sensor_fit='HORIZONTAL';cam.data.clip_start=.025
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.view_settings.view_transform='Filmic';scene.view_settings.look='Medium High Contrast';scene.view_settings.exposure=-.15;scene.render.image_settings.file_format='PNG'
scene.render.filepath=str(ROOT/'preview-pilot.png')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'EurofighterCockpit.blend'))
bpy.ops.render.render(write_still=True)
reference_cameras={
 'front':{'location_m':[-.35,0,1.05],'target_m':[.65,0,-.43],'lens_mm':45,'sensor_width_mm':36,'sensor_fit':'HORIZONTAL','resolution':[998,1230]},
 'oblique':{'location_m':[-.12,-.53,.95],'target_m':[.60,0,-.27],'lens_mm':39,'sensor_width_mm':36,'sensor_fit':'HORIZONTAL','resolution':[1125,1500]}}
(ROOT/'reference-cameras.json').write_text(json.dumps(reference_cameras,indent=2))
for name,cfg in reference_cameras.items():
 cam.location=cfg['location_m'];cam.rotation_euler=(Vector(cfg['target_m'])-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=cfg['lens_mm'];cam.data.sensor_width=cfg['sensor_width_mm'];cam.data.sensor_fit=cfg['sensor_fit']
 scene.render.resolution_x,scene.render.resolution_y=cfg['resolution'];scene.render.filepath=str(ROOT/('preview-reference-'+name+'.png'));bpy.ops.render.render(write_still=True)
print('COCKPIT_METRICS',json.dumps(stats))
