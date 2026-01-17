import bpy
import os
import math
import sys

print("FFCL-polyconvertre - Craftland Optimizer\n")

# ---- User Input ----
input_path = input("Input 3D model path: ").strip()
output_name = input("Output file name (no extension): ").strip()

if not input_path:
    sys.exit("No input file provided.")

if not os.path.isabs(input_path):
    input_path = os.path.join(os.getcwd(), input_path)

output_path = os.path.join(os.path.dirname(input_path), output_name + ".fbx")

# ---- Reset Scene ----
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# ---- Import Model ----
ext = os.path.splitext(input_path)[1].lower()
if ext == ".fbx":
    bpy.ops.import_scene.fbx(filepath=input_path)
elif ext == ".obj":
    bpy.ops.import_scene.obj(filepath=input_path)
elif ext in [".glb", ".gltf"]:
    bpy.ops.import_scene.gltf(filepath=input_path)
else:
    sys.exit("Unsupported file format: " + ext)

# ---- Optimization Settings ----
ANGLE_LIMIT = 8 
MAX_TRIS = 4000

def get_triangle_count(obj):
    return len(obj.data.polygons)

# ---- Optimize Meshes ----
for obj in bpy.context.scene.objects:
    if obj.type != "MESH":
        continue

    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.dissolve_limited(
        angle_limit=math.radians(ANGLE_LIMIT),
        use_dissolve_boundaries=False
    )
    bpy.ops.mesh.remove_doubles()
    bpy.ops.mesh.delete_loose()
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')

    tris = get_triangle_count(obj)
    if tris > MAX_TRIS:
        ratio = MAX_TRIS / tris
        dec = obj.modifiers.new("HardCapDecimate", 'DECIMATE')
        dec.decimate_type = 'COLLAPSE'
        dec.ratio = ratio
        bpy.ops.object.modifier_apply(modifier=dec.name)

    bpy.ops.object.shade_flat()
    obj.select_set(False)

# ---- Merge Meshes ----
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
for m in meshes:
    m.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
bpy.ops.object.join()

# ---- Export ----
bpy.ops.export_scene.fbx(
    filepath=output_path,
    apply_scale_options='FBX_SCALE_ALL',
    use_mesh_modifiers=True,
    bake_space_transform=True
)

print("\nDone! Exported:", output_path)
