# Audio balance check

- Voice: /home/dutchbase/Projects/videofactory/videos/videofactory/library-test-hf/01_voice/voice.wav
- Effects: summed effects, measured after WAV encoding
- Export period: 0.0–16.6 s
- Required distance: 12 dB (RMS and peak); internal margin: 13 dB
- Smallest distance: n/a (no measurable effects) dB
- Violations: 0
- Status: passed
- Effect events: [(3.2, 'whoosh'), (10.4, 'pop')]
- Windows: 20 ms, anchored to full timeline; 50 ms before / 150 ms after words
- Listening review: pending (headphones and phone speaker)

```json
{
  "required_db": 12,
  "minimum_db": null,
  "violations": 0,
  "measured_windows": 0,
  "status": "passed",
  "voice": "/home/dutchbase/Projects/videofactory/videos/videofactory/library-test-hf/01_voice/voice.wav",
  "effects": "summed effects, measured after WAV encoding",
  "effect_events": [
    [
      3.2,
      "whoosh"
    ],
    [
      10.4,
      "pop"
    ]
  ],
  "effect_track_sha256": "b56a12050b6bfebaf0bdb13396137efbdb410f0d4a34b48e131952b332c3c2c8",
  "start": 0.0,
  "end": 16.6,
  "sources": {
    "/home/dutchbase/Projects/videofactory/videos/videofactory/library-test-hf/01_voice/voice.wav": "523a547e71bfc3a66da7730396daae7e99524b792c4eac8c55915fe02680820b",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/library-test-hf/02_transcript/words.json": "b6c0ecb730fd1ae4d2b681d73a5050a1c2598b6543cbb45968859ab27cde0b11",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/library-test-hf/03_cues/cues.json": "bdb2bcad8b4d0e3e3ae05ace5ef29e40dabdef6daedf257a8a7ea56b50e0c1a8",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/library-test-hf/03_cues/cues.md": "a440a29352303c9c7f56b319c16e49fe9d316ba17a8e31b58c29d13d8c456a6b",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/library-test-hf/project.json": "2fe5b49f640cab630b9b0b78f20cc5080170c395beee541264be321d594beb8b",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/library-test-hf/04_scene/index.html": "4d616b518107067ebbbd2b326bb233f42001795bde08b4ed2bc1e6b26571d714",
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
    "/home/dutchbase/Projects/videofactory/videos/videofactory/library-test-hf/04_scene/assets/icons-animated/lucide-animated/audio-lines.js": "7dd8b7cc93b58e35e7e91d12a0a871665220c3d7704b8080222fad6e6b785339",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/library-test-hf/04_scene/assets/lottie/check-mark.js": "201d8a2713e45f98565e08e7cda0bc21adc78cd1deb1caf6a5ab799f50e10310",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/library-test-hf/04_scene/blocks/core.js": "1a2f056afb5500747bca1b899b65545d1514e31bf9d479255a97d6a2a7e3c37e",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/library-test-hf/04_scene/fx/kit.js": "1ddff9906328117343aef9a3896034d0d8c39b923bba0fb2cfb62e8ce4a5c2c7",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/library-test-hf/04_scene/fx/marker-highlight.js": "f30ba934290c8a701262946909def0e8efa8eb47e6f1b3499fbabfb2a6b05be6",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/library-test-hf/04_scene/fx/mesh-gradient.js": "730e0c3d16f00efb0a5fee82c141a80832114ab30aadadb8470e1d6ba9b9fa0c",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/library-test-hf/04_scene/fx/progress-bar.js": "5a787be30c7515a186fa959f72545a832dbc5f4b39f9246eb90cfafb3be83e83",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/library-test-hf/04_scene/fx/spring-in.js": "844076556986f1c8cace82fd150af80bdbb12977b241896359719decdc8b9eb0",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/library-test-hf/04_scene/fx/tracking-in.js": "6b5b52d4a658b62531e21fe0882763f069816ee52a09751fa526672a7d507f02",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/library-test-hf/04_scene/fx/whip-pan.js": "61e4bef177b5d750a0fdb032b32eec568a33001f075a5b271f5df489caee7af2",
    "/home/dutchbase/Projects/videofactory/brands/videofactory/tokens.js": "db2705981b6692da3f2041e3383e9df1960f118e4f06ee474e0953d92238bec9",
    "/home/dutchbase/Projects/videofactory/_runtime/vendor/gsap.min.js": "92bb9a96476f983d212a2bc4f54c889039c1696dd4461d40a736860938570fbb",
    "/home/dutchbase/Projects/videofactory/_runtime/hf-bridge.js": "1438daeca22bc7eca7e4da2305e5a13ae57e30a4e9ffb0715e3cf75dcb69f35b",
    "/home/dutchbase/Projects/videofactory/videos/videofactory/library-test-hf/03_cues/cues.js": "ed842e801a17823410f31677dd8e16e1d8764085923a6c93b3be175b5e6a3adb"
  },
  "sound_sources": {
    "music": "brand file",
    "effects": {
      "whoosh": "brand file",
      "pop": "brand file"
    }
  },
  "export": "/home/dutchbase/Projects/videofactory/videos/videofactory/library-test-hf/05_render/library-test-hf.mp4",
  "export_sha256": "7e3af6f6a4a9dc5a258b2f9824c81ce7c858de6a7bd6b5f1830763b55cc4ee93"
}
```
