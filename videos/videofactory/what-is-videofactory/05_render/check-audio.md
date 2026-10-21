# Audio balance check

- Voice: /home/dutchbase/Projects/videofactory/videos/videofactory/what-is-videofactory/01_voice/voice.mp3
- Effects: summed effects, measured after WAV encoding
- Export period: 0.0–215.36 s
- Required distance: 12 dB (RMS and peak); internal margin: 13 dB
- Smallest distance: 13.000396406361457 dB
- Violations: 0
- Status: passed
- Effect events: [(0.0, 'whoosh'), (4.24, 'error 0.6'), (5.94, 'whoosh'), (7.76, 'pop'), (9.44, 'pop'), (11.9, 'blip'), (16.32, 'stamp'), (19.34, 'whoosh'), (27.58, 'key'), (33.9, 'chime'), (35.72, 'whoosh'), (59.3, 'whoosh'), (60.92, 'key'), (66.18, 'pop'), (69.32, 'whoosh'), (77.3, 'pop'), (85.72, 'stamp'), (87.72, 'whoosh'), (98.8, 'whoosh'), (105.48, 'whoosh'), (108.98, 'error 0.6'), (113.84, 'whoosh'), (123.1, 'stamp'), (125.3, 'whoosh'), (129.52, 'whoosh'), (134.08, 'whoosh'), (138.84, 'pop'), (146.24, 'file:mouse-clicks.wav'), (152.88, 'pop'), (159.52, 'whoosh'), (167.94, 'chime'), (170.4, 'whoosh'), (177.1, 'pop'), (184.98, 'whoosh'), (192.6, 'key'), (196.34, 'whoosh'), (199.78, 'stamp'), (203.82, 'impact'), (207.22, 'riser'), (213.28, 'pop')]
- Windows: 20 ms, anchored to full timeline; 50 ms before / 150 ms after words
- Listening review: pending (headphones and phone speaker)

```json
{
  "required_db": 12,
  "minimum_db": 13.000396406361457,
  "violations": 0,
  "measured_windows": 253,
  "status": "passed",
  "voice": "/home/dutchbase/Projects/videofactory/videos/videofactory/what-is-videofactory/01_voice/voice.mp3",
  "effects": "summed effects, measured after WAV encoding",
  "effect_events": [
    [
      0.0,
      "whoosh"
    ],
    [
      4.24,
      "error 0.6"
    ],
    [
      5.94,
      "whoosh"
    ],
    [
      7.76,
      "pop"
    ],
    [
      9.44,
      "pop"
    ],
    [
      11.9,
      "blip"
    ],
    [
      16.32,
      "stamp"
    ],
    [
      19.34,
      "whoosh"
    ],
    [
      27.58,
      "key"
    ],
    [
      33.9,
      "chime"
    ],
    [
      35.72,
      "whoosh"
    ],
    [
      59.3,
      "whoosh"
    ],
    [
      60.92,
      "key"
    ],
    [
      66.18,
      "pop"
    ],
    [
      69.32,
      "whoosh"
    ],
    [
      77.3,
      "pop"
    ],
    [
      85.72,
      "stamp"
    ],
    [
      87.72,
      "whoosh"
    ],
    [
      98.8,
      "whoosh"
    ],
    [
      105.48,
      "whoosh"
    ],
    [
      108.98,
      "error 0.6"
    ],
    [
      113.84,
      "whoosh"
    ],
    [
      123.1,
      "stamp"
    ],
    [
      125.3,
      "whoosh"
    ],
    [
      129.52,
      "whoosh"
    ],
    [
      134.08,
      "whoosh"
    ],
    [
      138.84,
      "pop"
    ],
    [
      146.24,
      "file:mouse-clicks.wav"
    ],
    [
      152.88,
      "pop"
    ],
    [
      159.52,
      "whoosh"
    ],
    [
      167.94,
      "chime"
    ],
    [
      170.4,
      "whoosh"
    ],
    [
      177.1,
      "pop"
    ],
    [
      184.98,
      "whoosh"
    ],
    [
      192.6,
      "key"
    ],
    [
      196.34,
      "whoosh"
    ],
    [
      199.78,
      "stamp"
    ],
    [
      203.82,
      "impact"
    ],
    [
      207.22,
      "riser"
    ],
    [
      213.28,
      "pop"
    ]
  ],
  "effect_track_sha256": "6b02345b9d24d90fe170070de66143d97378d960b751bfbe58165f19f2835dfb",
  "start": 0.0,
  "end": 215.36,
  "sources": {
    "/home/dutchbase/Projects/videofactory/videos/videofactory/what-is-videofactory/01_voice/voice.mp3": "03684d272f6890681b8f4ae64fb4c01fa50328405ce45ac8b77dd29596f1ad49",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/what-is-videofactory/02_transcript/words.json": "39722c0267ec428cb2a751b065cbcc934e28fe313fdd106464f2e739b92787f2",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/what-is-videofactory/03_cues/cues.json": "a4bcf1a781c5f0c8bab4ee63b6e2bfe33d6d40015059d5ddb57642d50fd8ca6b",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/what-is-videofactory/03_cues/cues.md": "e64e81c961e767ef7210d45fba49c8229ae035128b2e8a530fe55dc47e009d1f",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/what-is-videofactory/project.json": "e54d6d4f451774d4cbdd9dc78d9e474e1c4b62d1acda97900bd35dab3dc2aec6",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/what-is-videofactory/04_scene/index.html": "b0652dfe11e9f7a5e96c733823ba1cb62f7bc0ea7f05f48fb59a940382be0d49",
    "/home/dutchbase/Projects/videofactory/anim.py": "da18ec3fac706822e39fde651f4cacd6ba989627b00d72293b59d8b7a6e34fc2",
    "/home/dutchbase/Projects/videofactory/_runtime/synth.py": "a9fcca04ba771e5b01d460c4d42832548d856865e37769243b52622af995fe22",
    "/home/dutchbase/Projects/videofactory/brands/videofactory/sound/SOURCES.md": "a570d0e0d33ce8a74c6cf41c8a2009a858fa2734009b753115e172e19548d1ce",
    "/home/dutchbase/Projects/videofactory/brands/videofactory/sound/music/study.ogg": "15f6279b84cbd8e89c3272afd10b0e1d6b89522f0f7216a285a063b17a873d4a",
    "/home/dutchbase/Projects/videofactory/brands/videofactory/sound/music/tinker.ogg": "dff31912bb799fb439f98d41f22515f225de32e0740ac80c211399f5c2ccad87",
    "/home/dutchbase/Projects/videofactory/brands/videofactory/sound/sfx/blip.ogg": "f6f911fd652d2e08969e9c3483f1874838381f3d9539f6469b55fed73df5650f",
    "/home/dutchbase/Projects/videofactory/brands/videofactory/sound/sfx/chime.ogg": "35abd1f6213ec6635154a93aa08ebaf1f15ee9f22e82e625b693c86a008b683b",
    "/home/dutchbase/Projects/videofactory/brands/videofactory/sound/sfx/click.ogg": "5ff0df37dfdb04fa165ad6795687d0c70caf0035e27891154f7ed5d6c3681590",
    "/home/dutchbase/Projects/videofactory/brands/videofactory/sound/sfx/coin.ogg": "3deca91c77c53fd83b6a9f2bf648ab97bf3c3e9fd38041af076badf4eb2065a3",
    "/home/dutchbase/Projects/videofactory/brands/videofactory/sound/sfx/error.ogg": "faf0783673e64481591b0a933367efedd931fe2d04c20b26032098aa005ba449",
    "/home/dutchbase/Projects/videofactory/brands/videofactory/sound/sfx/impact.ogg": "9c74162cb5869581377866048a8a145c769cc136a041d28cf85ca656cc54f9ac",
    "/home/dutchbase/Projects/videofactory/brands/videofactory/sound/sfx/key.ogg": "232f43307399c0a8b53089cd3c0492364148f67934f4977252b7b602e22e0d43",
    "/home/dutchbase/Projects/videofactory/brands/videofactory/sound/sfx/pop.ogg": "70313bc342c0677a4151d59d54ab57857b1b362f39cb0c53a4d35e0bf26dcccb",
    "/home/dutchbase/Projects/videofactory/brands/videofactory/sound/sfx/powerup.ogg": "2f6a799626c606f0496c94a5cf31ba4f08c3e3aa8dd37d62aaa85c2d797ab37d",
    "/home/dutchbase/Projects/videofactory/brands/videofactory/sound/sfx/riser.ogg": "26f6bdab083c4ccf7216742e570b86bdf94ddfed20e4257d666bb14aa8d2d50f",
    "/home/dutchbase/Projects/videofactory/brands/videofactory/sound/sfx/select.ogg": "08fe6f4d1a57e61d66005c9622725d43657b80e1bbfc232caa5b51e94f70a847",
    "/home/dutchbase/Projects/videofactory/brands/videofactory/sound/sfx/stamp.ogg": "5e6bbc89c028432c53413e8c38058d6a7f4203e2db74a553aadf8933b78f695a",
    "/home/dutchbase/Projects/videofactory/brands/videofactory/sound/sfx/step.ogg": "bba757cafdf6c4c751a4c8855933effe3d33fe4c60eedb031243ef614a2917e8",
    "/home/dutchbase/Projects/videofactory/brands/videofactory/sound/sfx/tick.ogg": "0d82d4671cbae82dc3e13be9305c39c833d2d2a7579cccee21ab31a6bd2a0def",
    "/home/dutchbase/Projects/videofactory/brands/videofactory/sound/sfx/whoosh.ogg": "c1894d051257bccdf8d04b550d24c6759b941da190ecc44bd82cda96d9fcdd13",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/what-is-videofactory/04_scene/assets/lottie/growth-chart.js": "c91215ebb53ca0cbd550a7589cee1952c7ec93036024d007dea736dbe4632e20",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/what-is-videofactory/04_scene/assets/real.js": "450bab6f453d6c3db0967c8ff40a2e919d793fa97cd51531370f4041570e19d3",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/what-is-videofactory/04_scene/motion/AI-03.dc.html": "aca59e4aa5ee4acd6869059fe1281eacb32bbf0f29af61c5a47d3a59d42129d5",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/what-is-videofactory/04_scene/motion/VID-01.dc.html": "227823aea6c5c3e53757f4aa49581e6d299b0818f7c0c5de0c635c9057fcab45",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/what-is-videofactory/04_scene/scene.js": "425212b5e564f1af5f479b9d1e644777e5df21269fb7a348904e6d0d4ac0c888",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/what-is-videofactory/04_scene/thumbnail.html": "bed9d478b429a0b93c3fe915ff2dabd217fbf3c32aff8f1db0dbf9b618a5d13c",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/what-is-videofactory/04_scene/thumbnail.js": "371adb24c38b32b3f9868d110c514f770dbce35c7bce60aff91508f152ae6273",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/what-is-videofactory/04_scene/assets/mouse-clicks.wav": "853b0bef6cb9c4ac5dce73eeeb3b6c6203bfab1da62cc8f4a1eba757001c09e3",
    "/home/dutchbase/Projects/videofactory/brands/videofactory/tokens.js": "db2705981b6692da3f2041e3383e9df1960f118e4f06ee474e0953d92238bec9",
    "/home/dutchbase/Projects/videofactory/_runtime/vendor/gsap.min.js": "92bb9a96476f983d212a2bc4f54c889039c1696dd4461d40a736860938570fbb",
    "/home/dutchbase/Projects/videofactory/_runtime/hf-bridge.js": "1438daeca22bc7eca7e4da2305e5a13ae57e30a4e9ffb0715e3cf75dcb69f35b",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/what-is-videofactory/03_cues/cues.js": "cb540b4df363ee5fe35b40957c5cb37f1de121e3b5c69fde83418aa51ab42c45"
  },
  "sound_sources": {
    "music": "brand file",
    "effects": {
      "whoosh": "brand file",
      "error": "brand file",
      "pop": "brand file",
      "blip": "brand file",
      "stamp": "brand file",
      "key": "brand file",
      "chime": "brand file",
      "file:mouse-clicks.wav": "project file",
      "impact": "brand file",
      "riser": "brand file"
    }
  },
  "export": "/home/dutchbase/Projects/videofactory/videos/videofactory/what-is-videofactory/05_render/what-is-videofactory.mp4",
  "export_sha256": "5d8d49df8f31cdd14247b3cd73d1b7ef30b2eeadae174ded683097a3436159f3"
}
```
