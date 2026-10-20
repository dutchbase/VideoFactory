# Synfig 1.4.5 pilot fixture

`switch-gesture.sif` is synthetic test art, not a real character or an approved rig. It has two editable face states in a Switch Group and a separate moving gesture group. The PNG imports are relative to this directory. Run Synfig with this directory as its working directory.

The project is 256 × 256, 24 fps, frames 0–239. Single-frame CLI renders succeeded at 0f, 96f and 120f using Synfig 1.4.5. At 96f, both eye pixels change from green to closed dark strokes. At 120f, the arm bounds move. The adapter uses `SYNFIG_RENDERING_THREADS=3` with `-T1` to cap the render queue at four workers and avoid a second scanline pool. See [STATUS.md](STATUS.md): the complete 720p render took 137.678 s and failed the 60-second adoption target.

This fixture never supplies a character approval. Native production stays gated on a registered source and your decision for the current rig revision.
