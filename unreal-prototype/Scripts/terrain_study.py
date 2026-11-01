"""Original, bounded procedural coast mesh/material for the cockpit study."""
import math
import pathlib
import unreal


def height(x, y):
    broad = .5 + .5 * math.sin(x * .00013 + math.sin(y * .00008))
    ridge = .5 + .5 * math.sin(y * .00017 + math.sin(x * .00009) * 2)
    h = 65 + broad * ridge * 520 + 65 * math.sin(x * .00041) * math.sin(y * .00031)
    h = max(30, h)
    river = 1500 + math.sin(x * .00016) * 2600 + math.sin(x * .00048) * 300
    valley = min(1, abs(y - river) / 1100)
    h = 12 + (h - 12) * valley * valley * (3 - 2 * valley)
    coast = -12000 + math.sin(x * .00012) * 2200 + math.cos(x * .00036) * 400
    blend = min(1, max(0, (y - coast + 650) / 1300))
    return -180 + (h + 180) * blend * blend * (3 - 2 * blend)


def create_terrain(root, actors, assets):
    generated = pathlib.Path(root) / "Generated"
    generated.mkdir(exist_ok=True)
    obj = generated / "CoastalTerrain.obj"
    cells = 128
    with obj.open("w") as stream:
        stream.write("# Original procedural terrain, centimetres, Z up\no CoastalTerrain\n")
        for j in range(cells + 1):
            y = -50000 + 100000 * j / cells
            for i in range(cells + 1):
                x = -20000 + 100000 * i / cells
                stream.write("v {:.3f} {:.3f} {:.3f}\n".format(x * 100, -y * 100, height(x, y) * 100))
        for j in range(cells + 1):
            for i in range(cells + 1):
                stream.write("vt {:.6f} {:.6f}\n".format(i / cells, j / cells))
        for j in range(cells):
            for i in range(cells):
                a = j * (cells + 1) + i + 1
                b = a + 1
                c = a + cells + 1
                d = c + 1
                # Source Y is negated to account for the OBJ translator's Y flip.
                stream.write("f {0}/{0} {1}/{1} {2}/{2}\n".format(a, c, b))
                stream.write("f {0}/{0} {1}/{1} {2}/{2}\n".format(b, c, d))
    task = unreal.AssetImportTask()
    task.filename = str(obj)
    task.destination_path = "/Game/Environment"
    task.destination_name = "CoastalTerrain"
    task.automated = True
    task.replace_existing = True
    task.save = True
    assets.import_asset_tasks([task])
    mesh = next((unreal.load_asset(path) for path in task.imported_object_paths if isinstance(unreal.load_asset(path), unreal.StaticMesh)), None)
    if not mesh:
        raise RuntimeError("Procedural terrain OBJ import produced no StaticMesh")
    material = unreal.load_asset("/Game/Study/Materials/M_Countryside")
    if not material:
        material = assets.create_asset("M_Countryside", "/Game/Study/Materials", unreal.Material, unreal.MaterialFactoryNew())
        world = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionWorldPosition)
        custom = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionCustom)
        inp = unreal.CustomInput()
        inp.set_editor_property("input_name", "P")
        custom.set_editor_property("inputs", [inp])
        custom.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT3)
        custom.set_editor_property("code", """
struct Pattern {
 float hash(float2 p){return frac(sin(dot(p,float2(127.1,311.7)))*43758.5453);}
 float noise(float2 p){float2 i=floor(p),f=frac(p);f=f*f*(3-2*f);return lerp(lerp(hash(i),hash(i+float2(1,0)),f.x),lerp(hash(i+float2(0,1)),hash(i+1),f.x),f.y);}
};
Pattern n;
float2 p=P.xy*.01;
float2 farm=float2(p.x*.94-p.y*.342,p.x*.342+p.y*.94);
farm+=float2(n.noise(p*.0008),n.noise(p*.0008+17.3))*420;
float2 cell=floor(farm/600);
float seed=n.hash(cell);
float3 green=lerp(float3(.025,.065,.018),float3(.10,.17,.035),seed);
float3 earth=lerp(float3(.14,.075,.022),float3(.30,.21,.075),n.hash(cell+7.4));
float3 colour=lerp(green,earth,smoothstep(.5,.7,seed));
float2 f=frac(farm/600);
float border=min(min(f.x,1-f.x),min(f.y,1-f.y))*600;
colour=lerp(float3(.025,.045,.013),colour,smoothstep(1,6+fwidth(border),border));
float forest=smoothstep(.56,.74,n.noise(p*.0006));
colour=lerp(colour,float3(.015,.045,.018)*(.7+n.noise(p*.03)*.6),forest);
colour*=.8+n.noise(p*.006)*.4;
float road=abs(p.y+1900+sin(p.x*.0003)*700);
colour=lerp(colour,float3(.28,.25,.18),1-smoothstep(8,18,road));
float river=1500+sin(p.x*.00016)*2600+sin(p.x*.00048)*300;
float water=1-smoothstep(90,150,abs(p.y-river));
return lerp(colour,float3(.012,.06,.075),water);
""")
        unreal.MaterialEditingLibrary.connect_material_expressions(world, "", custom, "P")
        unreal.MaterialEditingLibrary.connect_material_property(custom, "", unreal.MaterialProperty.MP_BASE_COLOR)
        rough = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionConstant)
        rough.set_editor_property("r", .87)
        unreal.MaterialEditingLibrary.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
        unreal.MaterialEditingLibrary.recompile_material(material)
        unreal.EditorAssetLibrary.save_loaded_asset(material)
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 0))
    actor.set_actor_label("Procedural coast and countryside")
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.static_mesh_component.set_material(0, material)
    bounds = actor.get_actor_bounds(False)
    unreal.log("PLANES_TERRAIN bounds " + str(bounds))
    return {"mesh": mesh.get_path_name(), "cells": cells, "triangles": cells * cells * 2, "extent_km": 100, "original_procedural_content": True}
