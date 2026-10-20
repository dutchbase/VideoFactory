# Notices

VideoFactory is released under the MIT License (see LICENSE). This file lists the third-party parts and their own licences.

Lucide icons in library/icons/lucide/ and the generated _runtime/icons.js retain their notice. The full upstream license, including Feather attribution, is licenses/lucide-LICENSE.txt. Source: https://github.com/lucide-icons/lucide/blob/main/LICENSE

Unmodified fonts come from the official Google Fonts repository. Each family folder has its original OFL.txt; FONT-SOURCES.json records URLs and hashes. Families: Archivo, Inter, JetBrains Mono and Caveat. The Studio app bundles DM Sans in studio/web/fonts/ with its OFL.txt.

Python, Playwright/Chromium, Pillow, NumPy, FFmpeg and optional Whisper binaries are not bundled. Their own licenses apply.

earshot (MIT, https://github.com/Leonxlnx/earshot) is installed on demand into the gitignored tools/earshot/ by tools/setup_earshot.sh and is not bundled. Its models carry their own licences: CLAP laion/larger_clap_general (Apache-2.0), AST MIT/ast-finetuned-audioset-10-10-0.4593 (BSD-3-Clause).

Code adapted from MIT-licensed projects (full licences in licenses/):
- _runtime/textcheck.js and P.track in _runtime/player.js: ideas from cth9191/animate (tools/textcheck.mjs, kit/core.js), https://github.com/cth9191/animate, licenses/animate-LICENSE.txt
- P.spring in _runtime/player.js: duration and bounce to stiffness and damping, after motiondivision/motion (packages/motion-dom spring generator), https://github.com/motiondivision/motion, licenses/motion-LICENSE.txt
- check.flashes and check.subtimes (motion blur): ideas from howseen-ai/claude-motion-design (render_template.py), https://github.com/howseen-ai/claude-motion-design, licenses/claude-motion-design-LICENSE.txt
- anim.master (limiter settings): after AbubakrChan/product-launch-motion (scripts/master.sh), https://github.com/AbubakrChan/product-launch-motion, licenses/product-launch-motion-LICENSE.txt

Code adapted from Apache-2.0 projects (licence and upstream NOTICE in licenses/):
- P.ease.crashIn / whip / softLand / accelExit in _runtime/player.js and window.Eases in _runtime/hf-bridge.js: ease math from tejashmakwana/motionmaxxing (runtime/motion.js), Apache-2.0, https://github.com/tejashmakwana/motionmaxxing, licenses/motionmaxxing-Apache-2.0.txt
- tools/precedent/precedent.py and tools/precedent/moments.jsonl: vendored from tejashmakwana/motionmaxxing (scripts/precedent.py, library/moments.jsonl), Apache-2.0, default library path changed, licenses/motionmaxxing-Apache-2.0.txt

Ideas from t3knobox/klik-anim-skill-creation and remotion-dev/skills (no licence) are re-expressed in our own words in _shared/motion.md and _shared/review.md; no text or code is copied.

lottie-web 5.12.2 is vendored in _runtime/vendor/lottie_canvas.min.js (MIT). Licence and hash: licenses/lottie-web-LICENSE.txt.

Files in library/ keep their own licences. library/sources.json lists the allowed sources; each video's 04_scene/assets/library.md logs every item it uses, with licence and source. Stock photos and video come from Pexels, Pixabay and Unsplash under their own licences and are not stored in git.

UI UX Pro Max (MIT) is vendored in .claude/skills/ui-ux-pro-max/ as an optional offline design lookup, from https://github.com/nextlevelbuilder/ui-ux-pro-max-skill at commit 026b6e1. Licence: licenses/ui-ux-pro-max-MIT.txt. Details: .claude/skills/ui-ux-pro-max/VENDOR.md.

HyperFrames 0.8.86 (Apache-2.0, https://github.com/heygen-com/hyperframes) is an optional second render engine. It is installed with npm from tools/hyperframes/ (pinned in package-lock.json) and is not bundled. Licence: licenses/hyperframes-Apache-2.0.txt. We always run it with HYPERFRAMES_NO_TELEMETRY=1 and DO_NOT_TRACK=1.

Components rewritten from MIT-licensed Remotion projects (library/fx/). VideoFactory does not ship Remotion or React for them: each part is re-implemented on a GSAP timeline, and its block.md names the upstream file and commit. Pinned commits are in library/upstream/sources.json.
- RemotionUI, https://github.com/riaz37/remotion-ui, licenses/remotionui-MIT.txt
- Onda, https://github.com/degueba/onda, licenses/onda-MIT.txt
- Curvable motion, https://github.com/Curvable/motion, licenses/curvable-motion-MIT.txt
- remotion-bits, https://github.com/av/remotion-bits, MIT by its package.json (no LICENSE file in the repo), licenses/remotion-bits-NOTE.md

Animated icons in library/icons-animated/lucide-animated/ are converted from lucide-animated (MIT, https://github.com/pqoqubbw/icons, licenses/lucide-animated-MIT.txt). Their drawings are Lucide icons (ISC, licenses/lucide-LICENSE.txt). Icon tags and categories come from the Lucide repository metadata (ISC).

Lottie animations in library/lottie/ come from LottieFiles under the Lottie Simple License (https://lottiefiles.com/page/license), one file at a time. Each <name>.meta.json records the licence, the animation page and the creator.

The sounds in brands/videofactory/sound/ are CC0 1.0 (public domain): effects from Kenney's Interface Sounds, UI Audio, Impact Sounds and Sci-fi Sounds packs (kenney.nl) and the Swishes Sound Pack by artisticdude (OpenGameArt), and two tracks by cynicmusic (OpenGameArt). They were converted to OGG, trimmed and level-set; one effect is played backwards. Every file, author, URL and licence is in brands/videofactory/sound/SOURCES.md. The generator _runtime/synth.py is our own code, written from a behaviour spec.

The sound library in library/audio/ is not distributed with VideoFactory. `anim.py audio` downloads it from the original sources to your own computer. library/audio/sources.json lists every source, its page and its licence (CC0 1.0, the Sonniss GDC bundle licence, the Mixkit free licence). The Sonniss and Mixkit licences forbid sharing the files: do not commit or upload them.
