# Blender 5.2.2 LTS synthetic pilot

`switch-gesture.blend` is an editable synthetic 2D rig, not a real or approved character. The project holds two named face planes (`face:open`, `face:closed`), a separately animated `gesture:arm` plane, and an orthographic camera. It uses the test PNGs in `../native_pilot/`. Image data is packed for portability, while the editable source links are relative to this directory. `build_fixture.py` rebuilds it with Blender 5.2.2 LTS.

The scene is 24 fps, frames 0–239. The face changes at frame 96 and restores at 102. The arm moves at frame 120. Output is transparent RGBA PNG using Cycles CPU at one sample with four renderer threads. This fixture proves tool behaviour only. It never supplies character identity, rig or action review approval.

Use the guarded `studio.blender_character.render_project` for a local pilot render. The output path must be an empty staging directory. It checks duration, frame count, memory, swap, decoded alpha and the pinned tool version. Do not register or expose production native actions until the pilot benchmark and your rig review pass.
