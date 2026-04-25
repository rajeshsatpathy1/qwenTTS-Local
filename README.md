# Qwen TTS Dialogue Narration

A Windows-first local workflow for generating narrated dialogue with Qwen3-TTS, then exporting merged WAV, MP3, and shareable MP4 outputs.

Interactive workflow guide: https://rajeshsatpathy1.github.io/qwenTTS-Local/

## What This Project Does

- Generates character-consistent speech from dialogue text files.
- Supports narrator and character voice separation.
- Supports emotional variants by assigning different speaker keys in the dialogue file.
- Splits long lines automatically into safer synthesis chunks.
- Optionally merges generated fragments into one WAV.
- Converts merged audio into MP3 and MP4 for sharing.

## Project Files

- `narrate_dialogue.py`: main TTS pipeline
- `merge_wavs.py`: merge chunked WAV files into one WAV
- `convert_audio.py`: convert audio files to MP3
- `convert_audio_to_mp4.py`: convert audio files to MP4 with a solid color or still image
- `setup_qwen_tts.bat`: Windows setup helper using conda
- `requirements.txt`: Python dependencies used by the project
- `samples/inputs/`: small checked-in example inputs
- `samples/outputs/`: checked-in example outputs
- `docs/NEW_INPUTS.md`: how to add new dialogue and voices
- `docs/TROUBLESHOOTING.md`: known failure modes and fixes
- `docs/COMMANDS.md`: reusable commands

## Requirements

- Windows
- NVIDIA GPU with CUDA support
- Python 3.12
- Enough VRAM for Qwen3-TTS 0.6B or 1.7B models
- Hugging Face access to the released Qwen3-TTS models

## Quick Start

### Option 1: Conda setup

```powershell
setup_qwen_tts.bat
```

### Option 2: Existing virtual environment

```powershell
.\.venv\Scripts\python.exe -m pip install -U -r requirements.txt
```

## Verified Commands

### Show help

```powershell
.\.venv\Scripts\python.exe narrate_dialogue.py --help
.\.venv\Scripts\python.exe merge_wavs.py --help
.\.venv\Scripts\python.exe convert_audio.py --help
.\.venv\Scripts\python.exe convert_audio_to_mp4.py --help
```

### Small narrated sample

```powershell
.\.venv\Scripts\python.exe narrate_dialogue.py samples\inputs\quickstart_dialogue.txt --characters samples\inputs\quickstart_characters.json --model-size 0.6B --output-dir output_quickstart --merge-output --merge-filename quickstart_merged.wav
```

### Merge an existing output folder

```powershell
.\.venv\Scripts\python.exe merge_wavs.py output_villain_directed --out villain_directed_merged_tighter.wav --pause-ms 120 --speaker-change-pause-ms 220
```

### Convert WAV to MP3

```powershell
.\.venv\Scripts\python.exe convert_audio.py output_villain_directed\villain_directed_merged_tighter.wav --output output_villain_directed\villain_directed_merged_tighter.mp3 --bitrate 192k
```

### Convert audio to MP4 with an image background

```powershell
.\.venv\Scripts\python.exe convert_audio_to_mp4.py output_villain_directed\villain_directed_merged_tighter.mp3 --output output_villain_directed\villain_directed_merged_tighter_image.mp4 --image output_villain_directed\Gemini_Generated_Image_vf4vupvf4vupvf4v.png --size 1920x1080 --color black --fps 30 --audio-bitrate 192k
```

## Dialogue Format

Each spoken line must use this format:

```text
[SpeakerName]: Dialogue text here.
```

Rules:

- Empty lines are ignored.
- Lines beginning with `#` are ignored.
- Speaker names must exist as keys in the chosen JSON voice file.
- Long lines are split automatically using punctuation-aware chunking.

## Emotional Variants

You can create multiple voice keys for the same character, for example:

```json
{
  "Villain_Cold": "...",
  "Villain_Bitter": "...",
  "Villain_Angry": "..."
}
```

Then use them directly in the dialogue file:

```text
[Villain_Cold]: "You speak of honor as if it is a shield."
[Villain_Angry]: "You are not a saint. You are just pathetic."
```

## Sample Inputs and Outputs

Checked-in examples live under `samples/`.

- Inputs: `samples/inputs/`
- Outputs: `samples/outputs/`

All generated runtime outputs outside `samples/` are ignored by `.gitignore`.

## Notes

- `VoiceDesign` currently uses the released `1.7B` model, while the clone stage can use `0.6B`.
- FlashAttention is optional. On Windows, the project safely falls back to eager attention.
- If a line sounds wrong, fix the text first: punctuation, line splitting, speaker ownership, and emotional variants matter a lot.
