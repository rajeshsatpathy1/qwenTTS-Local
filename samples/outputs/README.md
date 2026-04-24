# Sample Outputs

This folder contains small checked-in outputs that were generated from `samples/inputs/` and validated during repo setup.

## Included sample set

`quickstart/`

Contains:

- numbered WAV fragments
- `manifest.csv`
- `quickstart_merged.wav`
- `quickstart_merged.mp3`
- `quickstart_merged_tight.wav`
- `quickstart_merged.mp4`

## Why this folder exists

The main runtime output folders are ignored by `.gitignore`, but this sample output set is kept so the repository includes:

- a known-good example input/output pair
- a concrete manifest format example
- reusable audio and video conversion examples

## Regenerating the sample set

```powershell
.\.venv\Scripts\python.exe narrate_dialogue.py samples\inputs\quickstart_dialogue.txt --characters samples\inputs\quickstart_characters.json --model-size 0.6B --output-dir samples\outputs\quickstart --merge-output --merge-filename quickstart_merged.wav
.\.venv\Scripts\python.exe convert_audio.py samples\outputs\quickstart\quickstart_merged.wav --output samples\outputs\quickstart\quickstart_merged.mp3 --bitrate 192k
.\.venv\Scripts\python.exe merge_wavs.py samples\outputs\quickstart --out quickstart_merged_tight.wav --pause-ms 80 --speaker-change-pause-ms 140
.\.venv\Scripts\python.exe convert_audio_to_mp4.py samples\outputs\quickstart\quickstart_merged.mp3 --output samples\outputs\quickstart\quickstart_merged.mp4 --size 1080x1920 --color black --fps 30 --audio-bitrate 128k
```
