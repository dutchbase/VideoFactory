"""Build the synthetic Blender pilot fixture; run with Blender 5.2.2 --background.

Usage: blender -b -t 4 --python build_fixture.py -- /output/switch-gesture.blend
The source PNGs are synthetic test art from ../native_pilot, never an approved rig.
"""

import sys
from pathlib import Path

import bpy


def alpha_material(name: str, image_path: Path):
    image = bpy.data.images.load(str(image_path), check_existing=True)
    image.pack()
    # The built .blend is copied next to this builder after validation. Keep
    # its editable source link local even though the pilot packs the pixels.
    image.filepath = f"//../native_pilot/{image_path.name}"
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = image
    transparent = nodes.new("ShaderNodeBsdfTransparent")
    emission = nodes.new("ShaderNodeEmission")
    mixed = nodes.new("ShaderNodeMixShader")
    output = nodes.new("ShaderNodeOutputMaterial")
    links = material.node_tree.links
    links.new(texture.outputs["Color"], emission.inputs["Color"])
    links.new(texture.outputs["Alpha"], mixed.inputs[0])
    links.new(transparent.outputs["BSDF"], mixed.inputs[1])
    links.new(emission.outputs["Emission"], mixed.inputs[2])
    links.new(mixed.outputs["Shader"], output.inputs["Surface"])
    return material


def plane(name: str, image_path: Path, depth: float):
    bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, depth))
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(alpha_material(name, image_path))
    return obj


def main(output: Path):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    source = Path(__file__).resolve().parent.parent / "native_pilot"
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 1
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 4
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    scene.render.fps = 24
    scene.frame_start = 0
    scene.frame_end = 239
    scene.render.filepath = "//frames/frame_"
    scene.view_settings.view_transform = "Standard"

    open_face = plane("face:open", source / "face-open.png", 0.0)
    closed_face = plane("face:closed", source / "face-closed.png", 0.01)
    # Hold the closed state through the blink, then restore the open state.
    for frame, closed in ((0, False), (95, False), (96, True), (101, True), (102, False), (239, False)):
        open_face.hide_render = closed
        closed_face.hide_render = not closed
        open_face.keyframe_insert(data_path="hide_render", frame=frame)
        closed_face.keyframe_insert(data_path="hide_render", frame=frame)

    arm = plane("gesture:arm", source / "arm.png", 0.02)
    for frame, x, angle in ((0, -0.08, 0), (96, -0.08, 0), (120, 0.12, -0.2), (144, -0.08, 0), (239, -0.08, 0)):
        arm.location.x = x
        arm.rotation_euler.z = angle
        arm.keyframe_insert(data_path="location", frame=frame)
        arm.keyframe_insert(data_path="rotation_euler", frame=frame)

    bpy.ops.object.camera_add(location=(0, 0, 5))
    camera = bpy.context.object
    camera.name = "camera:orthographic"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 2.0
    scene.camera = camera
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    print("PILOT_PROJECT", output)


if __name__ == "__main__":
    main(Path(sys.argv[sys.argv.index("--") + 1]))
