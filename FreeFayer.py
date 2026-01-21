#!/usr/bin/env python3
"""
FFCL-PolyConv – Craftland Low-Poly Optimizer
Version 1.1.0 – Blender 5.0 compatibility fixes + final stats
"""

import bpy
import sys
import math
from pathlib import Path
import bmesh

# ────────────────────────────────────────────────────────────────
# CONFIG
# ────────────────────────────────────────────────────────────────
VERSION = "1.1.0"
WORK_SCALE     = 100.0
SAFETY_SCALE   = 1.0
DEFAULT_MAX_TRIS = 4000
MERGE_DISTANCE = 0.0001
ALLOWED_EXT    = {".fbx", ".obj", ".glb", ".gltf"}
DISSOLVE_ANGLE = math.radians(5.0)

# ────────────────────────────────────────────────────────────────
# CUSTOM HELP
# ────────────────────────────────────────────────────────────────
if "--help" in sys.argv or "-h" in sys.argv:
    print(f"""
FFCL-PolyConv – Craftland Low-Poly Optimizer
Version {VERSION} | Blender {bpy.app.version_string}
───────────────────────────────────────────────

Usage examples:
    blender --background --python freefayer.py -- --input model.fbx --max-tris 2500
    blender --background --python freefayer.py -- --input prop.glb --output prop_low --max-tris 1200

Arguments:
    --input           REQUIRED      Path to input file (.fbx, .obj, .glb, .gltf)
    --output          optional      Output name (no .fbx)
                                    Default: <input>_optimized
    --max-tris        optional      Target triangle count
                                    Default: 4000 (recommended 800–7000)
    --apply-transforms optional    Bake location + rotation
                                    (usually keep original pivot)
    --join            optional      Merge meshes into one object
                                    WARNING: often breaks textures/materials
                                    Default: OFF

Notes:
    • --join is OFF by default to avoid texture & material errors
    • Flat shading applied automatically
    • Original pivots/origins preserved
    • Blender 5.0+ uses DISSOLVE instead of PLANAR
""")
    sys.exit(0)

# ────────────────────────────────────────────────────────────────
# ARGUMENTS
# ────────────────────────────────────────────────────────────────
import argparse

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("--input",        required=True)
parser.add_argument("--output",       default=None)
parser.add_argument("--max-tris",     type=int, default=DEFAULT_MAX_TRIS)
parser.add_argument("--apply-transforms", action="store_true")
parser.add_argument("--join",         action="store_true")
args = parser.parse_args(
    sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
)

# ────────────────────────────────────────────────────────────────
# BANNER
# ────────────────────────────────────────────────────────────────
print(f"""
FFCL-PolyConv – Craftland Optimizer
Version {VERSION}   Blender {bpy.app.version_string}
───────────────────────────────────────────────
""")

if bpy.app.version >= (5, 0, 0):
    print("Blender 5.0+ → DISSOLVE decimation + manual flat shading")

# ────────────────────────────────────────────────────────────────
# PATHS
# ────────────────────────────────────────────────────────────────
input_path = Path(args.input).resolve()
if not input_path.exists():
    sys.exit("❌ Input file not found")

ext = input_path.suffix.lower()
if ext not in ALLOWED_EXT:
    sys.exit(f"❌ Unsupported format: {ext}")

output_name = args.output or f"{input_path.stem}_optimized"
output_path = input_path.parent / f"{output_name}.fbx"

MAX_TRIS = max(args.max_tris, 500)

# ────────────────────────────────────────────────────────────────
# HELPERS
# ────────────────────────────────────────────────────────────────
def get_safe_override():
    ctx = bpy.context.copy()
    ctx["scene"] = bpy.context.scene
    ctx["view_layer"] = bpy.context.view_layer
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            ctx["area"] = area
            for region in area.regions:
                if region.type == 'WINDOW':
                    ctx["region"] = region
                    break
            break
    return ctx

override = get_safe_override()

def get_total_tris():
    return sum(len(obj.data.polygons) for obj in bpy.context.scene.objects
               if obj.type == 'MESH')

def get_total_verts():
    return sum(len(obj.data.vertices) for obj in bpy.context.scene.objects
               if obj.type == 'MESH')

# ────────────────────────────────────────────────────────────────
# RESET & IMPORT
# ────────────────────────────────────────────────────────────────
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

print(f"→ Importing {input_path.name} ...")

try:
    if ext == ".fbx": bpy.ops.import_scene.fbx(filepath=str(input_path))
    elif ext == ".obj": bpy.ops.import_scene.obj(filepath=str(input_path))
    elif ext in {".glb", ".gltf"}: bpy.ops.import_scene.gltf(filepath=str(input_path))
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

initial_tris = get_total_tris()
initial_verts = get_total_verts()
print(f"  Initial triangles: {initial_tris:,}")
print(f"  Initial vertices : {initial_verts:,}")

# ────────────────────────────────────────────────────────────────
# PROCESS EACH MESH
# ────────────────────────────────────────────────────────────────
for obj in list(bpy.context.scene.objects):
    if obj.type != 'MESH':
        continue

    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    orig_scale = obj.scale.copy()

    obj.scale *= WORK_SCALE
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    try:
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=MERGE_DISTANCE)

        loose_verts = [v for v in bm.verts if not v.link_edges]
        loose_edges = [e for e in bm.edges if len(e.link_faces) == 0]
        loose_faces = [f for f in bm.faces if len(f.verts) < 3]

        if loose_verts: bmesh.ops.delete(bm, geom=loose_verts, context='VERTS')
        if loose_edges: bmesh.ops.delete(bm, geom=loose_edges, context='EDGES')
        if loose_faces: bmesh.ops.delete(bm, geom=loose_faces, context='FACES')

        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        bm.to_mesh(obj.data)
        bm.free()
    except Exception as e:
        print(f"⚠️ Cleanup failed on {obj.name}: {e}")

    current_tris = len(obj.data.polygons)
    if current_tris < 4:
        print(f"  Skipping decimation on {obj.name} (too few faces)")
    else:
        try:
            dec = obj.modifiers.new("Deci_Dissolve", 'DECIMATE')
            dec.decimate_type = 'DISSOLVE'
            dec.angle_limit = DISSOLVE_ANGLE
            dec.use_dissolve_boundaries = True
            bpy.ops.object.modifier_apply(modifier=dec.name)
        except Exception as e:
            print(f"⚠️ Dissolve failed on {obj.name}: {e}")

        current_tris = len(obj.data.polygons)
        if current_tris > MAX_TRIS:
            ratio = max(MAX_TRIS / current_tris, 0.05)
            print(f"  📉 Collapse {obj.name} ratio = {ratio:.3f}")
            try:
                dec = obj.modifiers.new("Deci_Collapse", 'DECIMATE')
                dec.decimate_type = 'COLLAPSE'
                dec.ratio = ratio
                dec.use_collapse_triangulate = True
                bpy.ops.object.modifier_apply(modifier=dec.name)
            except Exception as e:
                print(f"⚠️ Collapse failed on {obj.name}: {e}")

    try:
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.shade_flat()
    except Exception as e:
        print(f"⚠️ Shade flat failed on {obj.name}: {e}")
        for poly in obj.data.polygons:
            poly.use_smooth = False
        obj.data.update()

    obj.scale = orig_scale * (SAFETY_SCALE / WORK_SCALE)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    obj.scale = orig_scale
    obj.select_set(False)

# ────────────────────────────────────────────────────────────────
# OPTIONAL JOIN
# ────────────────────────────────────────────────────────────────
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']

if len(meshes) > 1:
    if args.join:
        print(f"→ Joining {len(meshes)} meshes...")
        for m in meshes:
            m.select_set(True)
        bpy.context.view_layer.objects.active = meshes[0]
        try:
            bpy.ops.object.join(override)
            final_obj = bpy.context.object
            if final_obj and final_obj.type == 'MESH':
                start = len(final_obj.material_slots)
                bpy.ops.object.material_slot_remove_unused()
                unique = {}
                for slot in final_obj.material_slots:
                    if not slot.material: continue
                    base = slot.material.name.split('.')[0].rstrip()
                    if base not in unique:
                        unique[base] = slot.material
                    else:
                        slot.material = unique[base]
                bpy.ops.object.material_slot_remove_unused()
                print(f"  Materials: {start} → {len(final_obj.material_slots)}")
        except Exception as e:
            print(f"❌ Join failed: {e}")
    else:
        print(f"→ {len(meshes)} meshes – join skipped (--join to enable)")

# ────────────────────────────────────────────────────────────────
# OPTIONAL TRANSFORM BAKE
# ────────────────────────────────────────────────────────────────
if args.apply_transforms:
    print("→ Baking location & rotation...")
    try:
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=False)
    except Exception as e:
        print(f"⚠️ Transform bake failed: {e}")

# ────────────────────────────────────────────────────────────────
# COLLECT FINAL COUNTS & PRINT SUMMARY
# ────────────────────────────────────────────────────────────────
final_tris = get_total_tris()
final_verts = get_total_verts()

print("\n" + "═" * 60)
print("                  FINAL OPTIMIZATION SUMMARY")
print("═" * 60)
removed_tris = initial_tris - final_tris
removed_verts = initial_verts - final_verts

print(f"  Original   |  Triangles: {initial_tris:>12,}   Vertices: {initial_verts:>12,}")
print(f"  Final      |  Triangles: {final_tris:>12,}   Vertices: {final_verts:>12,}")
print(f"  Removed    |  Triangles: {removed_tris:>12,}   Vertices: {removed_verts:>12,}")
print(f"  Reduction  |  Triangles: {removed_tris / initial_tris * 100:>6.1f}%     Vertices: {removed_verts / initial_verts * 100:>6.1f}%")

if meshes and removed_tris > 0:
    print(f"  Average tris per object: ~{final_tris // len(meshes)}")
print("═" * 60)

# ────────────────────────────────────────────────────────────────
# EXPORT
# ────────────────────────────────────────────────────────────────
try:
    if bpy.app.version >= (5, 0, 0):
        bpy.ops.export_scene.fbx(
            filepath=str(output_path),
            apply_scale_options='FBX_SCALE_ALL',
            use_mesh_modifiers=True,
            add_leaf_bones=False,
            bake_space_transform=True,
        )
    else:
        bpy.ops.export_scene.fbx(
            override,
            filepath=str(output_path),
            apply_scale_options='FBX_SCALE_ALL',
            use_mesh_modifiers=True,
            add_leaf_bones=False,
            bake_space_transform=True,
        )
    print(f"\n✅ Exported → {output_path}")
except Exception as e:
    print(f"❌ Export failed: {e}")
    sys.exit(1)
