# Audio balance check

- Voice: /home/dutchbase/Projects/videofactory/videos/videofactory/library-test-modern/01_voice/voice.wav
- Effects: summed effects, measured after WAV encoding
- Export period: 0.0–16.6 s
- Required distance: 12 dB (RMS and peak); internal margin: 13 dB
- Smallest distance: n/a (no measurable effects) dB
- Violations: 0
- Status: passed
- Effect events: [(3.2, 'whoosh'), (10.4, 'pop'), (12.4, 'key')]
- Windows: 20 ms, anchored to full timeline; 50 ms before / 150 ms after words
- Listening review: pending (headphones and phone speaker)

```json
{
  "required_db": 12,
  "minimum_db": null,
  "violations": 0,
  "measured_windows": 0,
  "status": "passed",
  "voice": "/home/dutchbase/Projects/videofactory/videos/videofactory/library-test-modern/01_voice/voice.wav",
  "effects": "summed effects, measured after WAV encoding",
  "effect_events": [
    [
      3.2,
      "whoosh"
    ],
    [
      10.4,
      "pop"
    ],
    [
      12.4,
      "key"
    ]
  ],
  "effect_track_sha256": "b56a12050b6bfebaf0bdb13396137efbdb410f0d4a34b48e131952b332c3c2c8",
  "start": 0.0,
  "end": 16.6,
  "sources": {
    "/home/dutchbase/Projects/videofactory/videos/videofactory/library-test-modern/01_voice/voice.wav": "523a547e71bfc3a66da7730396daae7e99524b792c4eac8c55915fe02680820b",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/library-test-modern/02_transcript/words.json": "b6c0ecb730fd1ae4d2b681d73a5050a1c2598b6543cbb45968859ab27cde0b11",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/library-test-modern/03_cues/cues.json": "72abf4b7a81fb3a771620b7a130dc2ead9c27b7705403e20653fcb3a91945f14",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/library-test-modern/03_cues/cues.md": "4d27686f7c521f4f08cb5bbdd65a04763ce5f9f616f7a560082ecf365c71f421",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/library-test-modern/project.json": "1f338633022c2828c82cae11e1c37f07f4d9d2c41852d9c3c0b6fe42eb48e5b7",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/library-test-modern/04_scene/index.html": "7579348085b8ae8cfd02dec3d532183acb7ae1d95be4258aa59c0b62ec628c9b",
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
    "/home/dutchbase/Projects/videofactory/videos/videofactory/library-test-modern/04_scene/assets/icons-animated/lucide-animated/mic.js": "ce9495f4bc2a770237c66a53909bd7ce2848d0ae30ce6392b9aeda428cbb9b0e",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/library-test-modern/04_scene/assets/lottie/success-check.js": "451f3d899d6e6032ccb96843899c72e2feba32e1722b7d64deb30190acaf3acb",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/library-test-modern/04_scene/blocks/core.js": "1a2f056afb5500747bca1b899b65545d1514e31bf9d479255a97d6a2a7e3c37e",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/library-test-modern/04_scene/fx/arrow-annotate.js": "4cf99a686f2ae918ddd5738c9e41cf7a4afaccc1df54b54e6d2fb14cf7f26627",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/library-test-modern/04_scene/fx/circle-reveal.js": "169627eba19d88298bca34c4e246a81e521bb50542512e680e9702fb40cbd1d5",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/library-test-modern/04_scene/fx/dynamic-grid.js": "c4eb028a2b827c154640acfd84a41bd51d22ad772250acc5af0143c185861431",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/library-test-modern/04_scene/fx/kit.js": "1ddff9906328117343aef9a3896034d0d8c39b923bba0fb2cfb62e8ce4a5c2c7",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/library-test-modern/04_scene/fx/matrix-decode.js": "1aa9d26c3614cc55c5efd052ef4de3c48df49db8bf00a502077e91b056bec63e",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/library-test-modern/04_scene/fx/terminal.js": "17b62a59d24891ce2d392f7a1083f895775e09cd6333715356c95c9ba28a4b0b",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/library-test-modern/04_scene/fx/underline.js": "14fa4261d7b9aad81390cef2f6a621e608af2c07a63417ee6d2d8335ba213923",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/library-test-modern/04_scene/scene.js": "9b3cde131b5859bc328d127527554700718fc89afe5080f6f5eea1676b76cb73",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/library-test-modern/04_scene/thumbnail.html": "54f4617bda6eedf83ff701d426e6f2a057278732e21b7fe7b1f0927a0b68afa9",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/library-test-modern/04_scene/thumbnail.js": "371adb24c38b32b3f9868d110c514f770dbce35c7bce60aff91508f152ae6273",
    "/home/dutchbase/Projects/videofactory/brands/videofactory/tokens.js": "db2705981b6692da3f2041e3383e9df1960f118e4f06ee474e0953d92238bec9",
    "/home/dutchbase/Projects/videofactory/_runtime/vendor/gsap.min.js": "92bb9a96476f983d212a2bc4f54c889039c1696dd4461d40a736860938570fbb",
    "/home/dutchbase/Projects/videofactory/_runtime/hf-bridge.js": "1438daeca22bc7eca7e4da2305e5a13ae57e30a4e9ffb0715e3cf75dcb69f35b",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/library-test-modern/03_cues/cues.js": "5c59f4c1478d899b3a52b1d1f1fdb347e02e2fbd49cf75d4ff66e28db054299e"
  },
  "sound_sources": {
    "music": "brand file",
    "effects": {
      "whoosh": "brand file",
      "pop": "brand file",
      "key": "brand file"
    }
  },
  "export": "/home/dutchbase/Projects/videofactory/videos/videofactory/library-test-modern/05_render/library-test-modern.mp4",
  "export_sha256": "10250873ee7eed26607cad9e217808537efdeddf3f6f42ae78419c0a49af45d1"
}
```
