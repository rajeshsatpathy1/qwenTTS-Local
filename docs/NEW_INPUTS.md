# Adding New Inputs

## 1. Create a voice file

Voice files are JSON objects mapping speaker names to natural-language voice descriptions.

Example:

```json
{
  "Narrator": "Measured adult narrator, ominous and detached.",
  "Hero": "Young adult voice, earnest, tense, and slightly breathless.",
  "Villain_Cold": "Old deep voice, cold and controlled.",
  "Villain_Angry": "Old deep voice, harsh and venomous, but not shouting."
}
```

Guidelines:

- Keep one key per actual performance mode.
- Use separate keys for emotional shifts instead of forcing one description to do everything.
- Prefer concrete delivery terms: slow, clipped, controlled anger, bitter, weary, detached.

## 2. Create a dialogue file

Every spoken line must be written as:

```text
[SpeakerName]: Dialogue text
```

Example:

```text
[Narrator]: Rain rattled against the stained glass.
[Villain_Cold]: "You speak of honor as if it is a shield."
[Narrator]: He circled the hero.
[Villain_Angry]: "You are not a saint."
```

## 3. Keep speaker ownership clean

Avoid mixing narration into character speech.

Bad:

```text
[Villain]: "You speak of honor as if it is a shield." He circled the hero.
```

Better:

```text
[Villain_Cold]: "You speak of honor as if it is a shield."
[Narrator]: He circled the hero.
```

This prevents characters from accidentally speaking third-person action beats.

## 4. Use punctuation to guide performance

Useful tools:

- `...` for a deliberate trailing pause
- short sentences for emphasis
- isolated lines for impact lines
- separate narration from direct speech

Example:

```text
[Villain_Bitter]: "But tell me... what good does honor actually do?"
[Villain_Angry]: "No. You have not."
```

## 5. Render the dialogue

```powershell
.\.venv\Scripts\python.exe narrate_dialogue.py your_dialogue.txt --characters your_voices.json --model-size 0.6B --output-dir output_your_scene --merge-output
```

## 6. Merge or convert later if needed

```powershell
.\.venv\Scripts\python.exe merge_wavs.py output_your_scene --out merged.wav --pause-ms 120 --speaker-change-pause-ms 220
.\.venv\Scripts\python.exe convert_audio.py output_your_scene\merged.wav --output output_your_scene\merged.mp3 --bitrate 192k
```

## 7. For MP4 sharing

Solid background:

```powershell
.\.venv\Scripts\python.exe convert_audio_to_mp4.py output_your_scene\merged.mp3 --output output_your_scene\merged.mp4 --size 1080x1920 --color black
```

Image background:

```powershell
.\.venv\Scripts\python.exe convert_audio_to_mp4.py output_your_scene\merged.mp3 --output output_your_scene\merged.mp4 --image your_image.png --size 1920x1080 --color black
```
