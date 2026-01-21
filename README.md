<p align="center">
  <img src="https://dl.dir.freefiremobile.com/common/OB51/CSH/CraftlandIcon/CRAFTLAND_STUDIO_LOGO.png" width="220">
</p>

<h1 align="center">FreeFayer Low-Poly Converter</h1>

<p align="center">
  <strong>
    Blender automation tool to create mobile-optimized low-poly FBX files<br>
    mainly for Free Fire Craftland and other low-end mobile games
  </strong>
</p>

<br>

<p align="center">
  <img src="https://github.com/str-atif/FFCL-PolyConv/blob/main/7d4e4755-8ba8-4faf-8414-47d31e7c64e6.png?raw=true" width="720">
</p>

<br>

---

## Version

**1.1.0 — Command-line driven release**  
*012126*

> This version removes interactive prompts and introduces proper CLI arguments,  
> making the tool suitable for automation, batch processing, and headless Blender usage.

---

## Features

- Supported input formats: `.fbx`, `.obj`, `.glb`, `.gltf`
- Always exports optimized `.fbx` files
- Fully command-line driven (no interactive prompts)
- Automatic triangle reduction with configurable hard limit
- Safe geometry cleanup:
  - Merge by distance
  - Delete loose geometry
  - Recalculate normals
- Temporary scale normalization during processing to prevent numeric instability
- Flat shading applied automatically (ideal for architectural & prop assets)
- Optional mesh joining when multiple objects are present
- No external Python dependencies required
- Designed to help avoid Craftland map rejections caused by high-poly assets

---

## Requirements

- Blender **4.0+**  
  *(Recommended: 4.2 or newer)*
- Windows / Linux / macOS

---

## Installation

1. Download or clone this repository.
2. Place `FreeFayer.py` anywhere on your system.  
   No installation or `pip` setup required — only the Blender executable.

---

## Usage

Run in **headless / background mode** (recommended):

### Windows

```bat
"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe" ^
  --background ^
  --python FreeFayer.py ^
  -- ^
  --input "C:\models\my_house.fbx" ^
  --max-tris 4200
```
##Linux / macOS
```bash
/Applications/Blender.app/Contents/MacOS/Blender \
  --background \
  --python ./FreeFayer.py \
  -- \
  --input ./character.glb \
  --output char_lowpoly \
  --max-tris 2800
```

# Quick Examples
# Basic usage – default 4000 triangle limit
--input building.obj

## Custom output name
--input pistol.fbx --output pistol_low

## Aggressive optimization for small props
--input lamp.glb --max-tris 900

## Medium-sized prop / weapon
--input ak47.fbx --max-tris 3200
