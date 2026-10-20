---
voice_id: YOUR_VOICE_ID
model: YOUR_SUPPORTED_MODEL_ID
stability: natural
similarity_boost: 0.75
format: mp3_44100_128
---
# <BRAND NAME> voice settings

Free path: record the script yourself and put the file in the video's `01_voice/` folder. Nothing here is needed.

ElevenLabs path: replace `YOUR_VOICE_ID` with a voice id from your ElevenLabs voice library and
`YOUR_SUPPORTED_MODEL_ID` with a model your plan has (`python anim.py speak <slug> --check` lists them).
The key goes in the local `.env`. Example with real values: `brands/videofactory/voice.md`.
Each video freezes these settings when it is created. Guide: `../../_shared/voice.md`.
