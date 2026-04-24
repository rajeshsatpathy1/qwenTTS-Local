# Troubleshooting

## CUDA is not available

Symptom:

- `torch.cuda.is_available()` is `False`
- The script exits before model load

Fix:

- Confirm the NVIDIA GPU is visible with `nvidia-smi`
- Install a CUDA-enabled PyTorch build
- Recheck with:

```powershell
.\.venv\Scripts\python.exe -c "import torch; print(torch.__version__); print(torch.version.cuda); print(torch.cuda.is_available()); print(torch.cuda.device_count())"
```

## Hugging Face model access fails

Symptom:

- `401 Unauthorized`
- `RepositoryNotFoundError`

Fix:

```powershell
huggingface-cli login
```

Then rerun the narration command.

## Duplicate python runs

Symptom:

- Several `narrate_dialogue.py` processes are active
- VRAM pressure, partial outputs, confusing folder state

Fix:

```powershell
Get-CimInstance Win32_Process -Filter "Name LIKE 'python%'" | Where-Object { $_.CommandLine -like '*narrate_dialogue.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
```

Then rerun exactly one narration command.

## Long monologue stalls or feels unstable

Cause:

- One giant line creates one giant synthesis request

Fix:

- Break long passages into multiple lines
- Keep narration and dialogue separate
- Use emotional variants instead of cramming all behavior into one prompt
- Lower the line size if needed:

```powershell
.\.venv\Scripts\python.exe narrate_dialogue.py your_dialogue.txt --characters your_voices.json --max-chars-per-line 180 --output-dir output_scene
```

## Character says narrator text

Cause:

- A character-tagged line still includes third-person action beats

Bad:

```text
[Villain]: "You speak of honor as if it is a shield." He circled the hero.
```

Fix:

```text
[Villain_Cold]: "You speak of honor as if it is a shield."
[Narrator]: He circled the hero.
```

## Merge pauses feel too long or too short

Tighter merge:

```powershell
.\.venv\Scripts\python.exe merge_wavs.py output_scene --out merged_tight.wav --pause-ms 90 --speaker-change-pause-ms 160
```

Balanced merge:

```powershell
.\.venv\Scripts\python.exe merge_wavs.py output_scene --out merged_balanced.wav --pause-ms 120 --speaker-change-pause-ms 220
```

More dramatic merge:

```powershell
.\.venv\Scripts\python.exe merge_wavs.py output_scene --out merged_dramatic.wav --pause-ms 180 --speaker-change-pause-ms 320
```

## MP4 output needs an image

Use:

```powershell
.\.venv\Scripts\python.exe convert_audio_to_mp4.py output_scene\merged.mp3 --output output_scene\merged.mp4 --image your_image.png --size 1920x1080 --color black
```

If the image ratio does not match the video ratio, the script pads instead of stretching.
