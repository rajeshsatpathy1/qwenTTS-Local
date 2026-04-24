# Commands

## Install requirements into the existing virtual environment

```powershell
.\.venv\Scripts\python.exe -m pip install -U -r requirements.txt
```

## Quickstart render

```powershell
.\.venv\Scripts\python.exe narrate_dialogue.py samples\inputs\quickstart_dialogue.txt --characters samples\inputs\quickstart_characters.json --model-size 0.6B --output-dir output_quickstart --merge-output --merge-filename quickstart_merged.wav
```

## Directed villain render

```powershell
.\.venv\Scripts\python.exe narrate_dialogue.py villain_dialogue_directed.txt --characters villain_voice.json --model-size 0.6B --output-dir output_villain_directed --merge-output --merge-filename villain_directed_merged.wav --merge-pause-ms 220 --speaker-change-pause-ms 420
```

## Tighter merge only

```powershell
.\.venv\Scripts\python.exe merge_wavs.py output_villain_directed --out villain_directed_merged_tighter.wav --pause-ms 120 --speaker-change-pause-ms 220
```

## WAV to MP3

```powershell
.\.venv\Scripts\python.exe convert_audio.py output_villain_directed\villain_directed_merged_tighter.wav --output output_villain_directed\villain_directed_merged_tighter.mp3 --bitrate 192k
```

## MP3 to MP4 with a solid background

```powershell
.\.venv\Scripts\python.exe convert_audio_to_mp4.py output_villain_directed\villain_directed_merged_tighter.mp3 --output output_villain_directed\villain_directed_merged_tighter.mp4 --size 1080x1920 --color black --fps 30 --audio-bitrate 192k
```

## MP3 to MP4 with an image background

```powershell
.\.venv\Scripts\python.exe convert_audio_to_mp4.py output_villain_directed\villain_directed_merged_tighter_reuse.mp3 --output output_villain_directed\villain_directed_merged_tighter_reuse_image_1920x1080.mp4 --image output_villain_directed\Gemini_Generated_Image_vf4vupvf4vupvf4v.png --size 1920x1080 --color black --fps 30 --audio-bitrate 192k
```

## Stop duplicate narration runs

```powershell
Get-CimInstance Win32_Process -Filter "Name LIKE 'python%'" | Where-Object { $_.CommandLine -like '*narrate_dialogue.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
```
