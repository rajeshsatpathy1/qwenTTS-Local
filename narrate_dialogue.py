#!/usr/bin/env python3
"""
Dialogue Narration with Qwen3-TTS (VoiceDesign + VoiceClone workflow)

Workflow:
  1. Load character voice descriptions from characters.json
  2. Parse dialogue lines from a dialogue file
  3. For each unique character, generate a short reference audio clip using
     the VoiceDesign model (one call per character, then cached on disk).
  4. Use VoiceClone + those reference clips to narrate every line with a
     consistent, per-character voice.
  5. Save numbered WAV files to the output/ directory.

Dialogue file format:
  [CharacterName]: Dialogue text here.
  Lines starting with # are comments and are ignored.
  Empty lines are ignored.

Usage:
  python narrate_dialogue.py dialogue_sample.txt
  python narrate_dialogue.py myscript.txt --characters my_characters.json
  python narrate_dialogue.py myscript.txt --model-size 0.6B   # lower VRAM
  python narrate_dialogue.py myscript.txt --output-dir my_output
"""

import argparse
import csv
import importlib.util
import json
import re
import sys
from pathlib import Path

import numpy as np
import torch
import soundfile as sf
from qwen_tts import Qwen3TTSModel


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_characters(path: str) -> dict:
    """Load {character_name: config} from a JSON file."""
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must be a JSON object mapping names to descriptions.")

    json_dir = Path(path).resolve().parent
    resolved = {}

    def resolve_path(value: str) -> str:
        candidate = Path(value)
        if not candidate.is_absolute():
            candidate = json_dir / candidate
        return str(candidate.resolve())

    def resolve_character(name: str, stack: list[str]) -> dict:
        if name in resolved:
            return resolved[name]
        if name not in data:
            raise ValueError(f"Unknown base voice {name!r} referenced in {path}.")
        if name in stack:
            cycle = " -> ".join(stack + [name])
            raise ValueError(f"Circular base voice reference in {path}: {cycle}")

        entry = data[name]
        if isinstance(entry, str):
            config = {
                "description": entry.strip(),
                "ref_audio": None,
                "ref_text": REF_SENTENCE,
            }
        elif isinstance(entry, dict):
            config = {
                "description": "",
                "ref_audio": None,
                "ref_text": REF_SENTENCE,
            }
            base_name = entry.get("base")
            if base_name:
                if not isinstance(base_name, str) or not base_name.strip():
                    raise ValueError(f"Character {name!r} has an invalid 'base' value in {path}.")
                base_config = resolve_character(base_name.strip(), stack + [name])
                config = dict(base_config)
            else:
                base_description = entry.get("voice") or entry.get("description")
                if not isinstance(base_description, str) or not base_description.strip():
                    raise ValueError(
                        f"Character {name!r} in {path} must be a string or an object with "
                        "either 'base' or 'voice'/'description'."
                    )
                config["description"] = base_description.strip()

            modifier = entry.get("modifier", "")
            if modifier:
                if not isinstance(modifier, str):
                    raise ValueError(f"Character {name!r} has a non-string 'modifier' in {path}.")

                config["description"] = f"{config['description']} {modifier.strip()}".strip()

            if "ref_audio" in entry:
                ref_audio = entry["ref_audio"]
                if ref_audio is None:
                    config["ref_audio"] = None
                elif isinstance(ref_audio, str) and ref_audio.strip():
                    config["ref_audio"] = resolve_path(ref_audio.strip())
                else:
                    raise ValueError(f"Character {name!r} has an invalid 'ref_audio' in {path}.")

            if "ref_text" in entry:
                ref_text = entry["ref_text"]
                if not isinstance(ref_text, str) or not ref_text.strip():
                    raise ValueError(f"Character {name!r} has an invalid 'ref_text' in {path}.")
                config["ref_text"] = ref_text.strip()

            if config["ref_audio"] and not config["ref_text"]:
                raise ValueError(
                    f"Character {name!r} provides ref_audio but no ref_text in {path}."
                )
        else:
            raise ValueError(
                f"Character {name!r} in {path} must be either a string or an object."
            )

        resolved[name] = config
        return config

    for character_name in data:
        resolve_character(character_name, [])

    return resolved


def parse_dialogue(path: str) -> list:
    """
    Return a list of (character_name, text) tuples.
    Expected line format:  [CharacterName]: Dialogue text
    """
    pattern = re.compile(r"^\[(.+?)\]:\s*(.+)$")
    lines = []
    with open(path, "r", encoding="utf-8") as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw or raw.startswith("#"):
                continue
            m = pattern.match(raw)
            if m:
                lines.append((m.group(1).strip(), m.group(2).strip()))
            else:
                print(f"  Warning: skipping unrecognized line: {raw!r}", file=sys.stderr)
    return lines


def split_long_text(text: str, max_chars: int) -> list[str]:
    """Split long narration text into sentence-aware chunks."""
    if max_chars <= 0 or len(text) <= max_chars:
        return [text]

    sentences = re.split(r"(?<=[.!?\"])(?:\s+)", text)
    chunks = []
    current = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        if len(sentence) > max_chars:
            if current:
                chunks.append(current)
                current = ""

            words = sentence.split()
            piece = ""
            for word in words:
                candidate = f"{piece} {word}".strip()
                if piece and len(candidate) > max_chars:
                    chunks.append(piece)
                    piece = word
                else:
                    piece = candidate
            if piece:
                chunks.append(piece)
            continue

        candidate = f"{current} {sentence}".strip()
        if current and len(candidate) > max_chars:
            chunks.append(current)
            current = sentence
        else:
            current = candidate

    if current:
        chunks.append(current)

    return chunks or [text]


def expand_dialogue_chunks(dialogue: list[tuple[str, str]], max_chars: int) -> list[tuple[str, str]]:
    """Expand each dialogue line into multiple chunks when needed."""
    expanded = []
    for char_name, text in dialogue:
        for chunk in split_long_text(text, max_chars):
            expanded.append((char_name, chunk))
    return expanded


def load_reference_audio(path: str) -> tuple[np.ndarray, int]:
    """Load a user-supplied reference audio file and normalize it for cloning."""
    wav_arr, sample_rate = sf.read(path, dtype="float32")
    if wav_arr.ndim > 1:
        wav_arr = wav_arr.mean(axis=1)
    return wav_arr, sample_rate


def detect_attn_impl() -> str:
    """
    Return 'flash_attention_2' if the package is installed, else 'eager'.
    FlashAttention 2 is often unavailable on Windows — 'eager' is the safe
    fallback and still works correctly, just uses a little more VRAM.
    """
    if importlib.util.find_spec("flash_attn") is not None:
        return "flash_attention_2"
    return "eager"


def require_cuda() -> None:
    """Fail early with a clear message if CUDA is unavailable."""
    if torch.cuda.is_available():
        return

    sys.exit(
        "Qwen3-TTS requires a CUDA-capable NVIDIA GPU for practical local inference.\n"
        "This environment reports torch.cuda.is_available() = False.\n\n"
        "What to check:\n"
        "  1. Install the NVIDIA driver for your GPU.\n"
        "  2. Install a CUDA-enabled PyTorch build.\n"
        "  3. Confirm your GPU is visible with: python -c \"import torch; print(torch.cuda.is_available(), torch.cuda.device_count())\"\n\n"
        "If this machine has no NVIDIA GPU, this script will not run as written.\n"
        "Use a CUDA machine, or switch to a different TTS model that supports CPU inference."
    )


def load_model(model_id: str, attn_impl: str):
    """Load a Qwen3-TTS model and rewrite common download/auth failures."""
    try:
        return Qwen3TTSModel.from_pretrained(
            model_id,
            device_map="cuda:0",
            dtype=torch.bfloat16,
            attn_implementation=attn_impl,
        )
    except Exception as exc:
        msg = str(exc)
        if "401" in msg or "Unauthorized" in msg or "RepositoryNotFoundError" in msg:
            sys.exit(
                f"Unable to download model {model_id}.\n"
                "Hugging Face returned an authorization error.\n\n"
                "What to do:\n"
                "  1. Open the model page in a browser and confirm you have access.\n"
                "  2. Run: huggingface-cli login\n"
                "  3. Re-run this script, or pre-download the model to a local folder.\n\n"
                f"Original error: {exc}"
            )
        raise


def resolve_model_ids(model_size: str) -> tuple[str, str]:
    """
    Return (voice_design_model_id, voice_clone_model_id).

    Qwen3-TTS currently publishes VoiceDesign only at 1.7B, while Base exists
    at both 1.7B and 0.6B. That lets us create reference voices once with the
    1.7B VoiceDesign model and then narrate the dialogue with the lighter Base
    model selected by --model-size.
    """
    design_model_id = "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign"
    base_model_id = f"Qwen/Qwen3-TTS-12Hz-{model_size}-Base"
    return design_model_id, base_model_id


def merge_output_files(
    output_dir: Path,
    manifest_rows: list[dict],
    merged_filename: str,
    pause_ms: int,
    speaker_change_pause_ms: int,
) -> Path | None:
    """Merge generated WAV files into one track with configurable pauses."""
    if not manifest_rows:
        return None

    merged_segments = []
    sample_rate = None
    previous_character = None

    for row in manifest_rows:
        wav_path = output_dir / row["file"]
        audio, current_sr = sf.read(str(wav_path), dtype="float32")
        if sample_rate is None:
            sample_rate = current_sr
        elif current_sr != sample_rate:
            raise ValueError(f"Sample rate mismatch for {wav_path}: {current_sr} != {sample_rate}")

        if audio.ndim > 1:
            audio = audio.mean(axis=1)

        merged_segments.append(audio)

        is_last = row is manifest_rows[-1]
        if is_last:
            continue

        pause_to_use = speaker_change_pause_ms if previous_character and row["character"] != previous_character else pause_ms
        if pause_to_use > 0:
            pause_samples = int(sample_rate * (pause_to_use / 1000.0))
            merged_segments.append(np.zeros(pause_samples, dtype=np.float32))

        previous_character = row["character"]

    merged_audio = np.concatenate(merged_segments)
    merged_path = output_dir / merged_filename
    sf.write(str(merged_path), merged_audio, sample_rate)
    return merged_path


# ---------------------------------------------------------------------------
# Reference sentence used to generate per-character voice clips
# ---------------------------------------------------------------------------
REF_SENTENCE = (
    "The morning light filtered through the curtains as she reached for her coffee, "
    "wondering what the day might bring."
)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Narrate a multi-character dialogue with Qwen3-TTS.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("dialogue", help="Path to the dialogue .txt file")
    parser.add_argument(
        "--characters", default="characters.json",
        help="JSON file mapping character names to voice descriptions (default: characters.json)",
    )
    parser.add_argument(
        "--model-size", choices=["1.7B", "0.6B"], default="1.7B",
        help="Model size: 1.7B (better quality) or 0.6B (lower VRAM, ~6-8 GB). Default: 1.7B",
    )
    parser.add_argument(
        "--output-dir", default="output",
        help="Folder for output WAV files (default: output/)",
    )
    parser.add_argument(
        "--resume-output", action="store_true",
        help="Skip dialogue chunks whose numbered WAV files already exist in the output folder.",
    )
    parser.add_argument(
        "--regen-refs", action="store_true",
        help="Re-generate character reference clips even if cached versions exist.",
    )
    parser.add_argument(
        "--refs-only", action="store_true",
        help="Generate or refresh character reference clips, then stop before dialogue narration.",
    )
    parser.add_argument(
        "--max-chars-per-line", type=int, default=260,
        help="Automatically split long dialogue lines into chunks of about this many characters. Default: 260",
    )
    parser.add_argument(
        "--merge-output", action="store_true",
        help="Merge all generated WAV chunks into one final WAV file.",
    )
    parser.add_argument(
        "--merge-filename", default="merged_output.wav",
        help="Filename for the merged WAV when --merge-output is used. Default: merged_output.wav",
    )
    parser.add_argument(
        "--merge-pause-ms", type=int, default=250,
        help="Pause between adjacent chunks in the merged WAV. Default: 250 ms",
    )
    parser.add_argument(
        "--speaker-change-pause-ms", type=int, default=450,
        help="Pause between adjacent chunks when the speaker changes in the merged WAV. Default: 450 ms",
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Load inputs
    # ------------------------------------------------------------------
    print(f"Loading characters from: {args.characters}")
    characters = load_characters(args.characters)

    print(f"Parsing dialogue from:   {args.dialogue}")
    dialogue = parse_dialogue(args.dialogue)

    if not dialogue:
        sys.exit("No valid dialogue lines found. Check your dialogue file format.")

    dialogue = expand_dialogue_chunks(dialogue, args.max_chars_per_line)

    used_chars = {char for char, _ in dialogue}
    missing = used_chars - set(characters.keys())
    if missing:
        sys.exit(
            f"Error: the following characters appear in the dialogue but have no "
            f"voice description in {args.characters}:\n  {', '.join(sorted(missing))}\n"
            f"Add entries for them and re-run."
        )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    ref_dir = output_dir / "_character_references"
    ref_dir.mkdir(exist_ok=True)

    require_cuda()

    design_model_id, base_model_id = resolve_model_ids(args.model_size)

    attn_impl = detect_attn_impl()
    print(f"\nAttention implementation : {attn_impl}")
    print(f"Model size               : {args.model_size}")
    print(f"CUDA device count        : {torch.cuda.device_count()}")
    print(f"VoiceDesign model        : {design_model_id}")
    print(f"VoiceClone model         : {base_model_id}")
    print(f"Max chars per line       : {args.max_chars_per_line}")
    print(f"Output directory         : {output_dir.resolve()}\n")

    # ------------------------------------------------------------------
    # Step 1 — VoiceDesign: generate one reference clip per character
    # ------------------------------------------------------------------
    char_refs = {}  # name -> (wav_array, sample_rate)
    ref_texts = {}

    for char_name in sorted(used_chars):
        config = characters[char_name]
        ref_texts[char_name] = config["ref_text"]
        if not config["ref_audio"]:
            continue

        source_path = config["ref_audio"]
        if not Path(source_path).exists():
            sys.exit(f"Reference audio for {char_name} was not found: {source_path}")

        print(f"Using supplied reference audio for {char_name}: {source_path}")
        wav_arr, sr = load_reference_audio(source_path)
        ref_path = ref_dir / f"{char_name}.wav"
        if args.regen_refs or not ref_path.exists():
            sf.write(str(ref_path), wav_arr, sr)
        char_refs[char_name] = (wav_arr, sr)

    chars_needing_refs = [
        c for c in sorted(used_chars)
        if not characters[c]["ref_audio"]
        if args.regen_refs or not (ref_dir / f"{c}.wav").exists()
    ]

    if chars_needing_refs:
        print(f"Loading VoiceDesign model ({design_model_id}) ...")
        design_model = load_model(design_model_id, attn_impl)

        print("\nGenerating character reference clips:")
        for char_name in chars_needing_refs:
            instruct = characters[char_name]["description"]
            print(f"  {char_name}: {instruct}")
            wavs, sr = design_model.generate_voice_design(
                text=ref_texts[char_name],
                language="English",
                instruct=instruct,
            )
            ref_path = ref_dir / f"{char_name}.wav"
            sf.write(str(ref_path), wavs[0], sr)
            char_refs[char_name] = (wavs[0], sr)
            print(f"    Saved -> {ref_path.name}")

        # Free VRAM before loading the second model
        del design_model
        torch.cuda.empty_cache()
    else:
        print("All character reference clips already exist (use --regen-refs to recreate).")

    # Load any cached reference clips that we didn't just generate
    for char_name in sorted(used_chars):
        if char_name not in char_refs:
            ref_path = ref_dir / f"{char_name}.wav"
            wav_arr, sr = sf.read(str(ref_path))
            char_refs[char_name] = (wav_arr, sr)

    if args.refs_only:
        print(f"\nDone! {len(char_refs)} character reference clips are available in: {ref_dir.resolve()}")
        return

    # ------------------------------------------------------------------
    # Step 2 — VoiceClone: build reusable per-character prompts
    # ------------------------------------------------------------------
    print(f"\nLoading Base (VoiceClone) model ({base_model_id}) ...")
    clone_model = load_model(base_model_id, attn_impl)

    print("Building voice clone prompts ...")
    clone_prompts = {}
    for char_name in sorted(used_chars):
        wav_arr, sr = char_refs[char_name]
        clone_prompts[char_name] = clone_model.create_voice_clone_prompt(
            ref_audio=(wav_arr, sr),
            ref_text=ref_texts[char_name],
        )
        print(f"  {char_name} -> OK")

    # ------------------------------------------------------------------
    # Step 3 — Narrate every dialogue line
    # ------------------------------------------------------------------
    print(f"\nNarrating {len(dialogue)} lines ...\n")
    manifest_rows = []

    for idx, (char_name, text) in enumerate(dialogue, start=1):
        filename = f"{idx:04d}_{char_name}.wav"
        out_path = output_dir / filename
        preview = text[:70] + ("..." if len(text) > 70 else "")

        if args.resume_output and out_path.exists():
            print(f"  [{idx:04d}/{len(dialogue):04d}] {char_name}: skipping existing {filename}")
            manifest_rows.append({"index": idx, "character": char_name, "text": text, "file": filename})
            continue

        print(f"  [{idx:04d}/{len(dialogue):04d}] {char_name}: {preview}")

        wavs, sr = clone_model.generate_voice_clone(
            text=text,
            language="English",
            voice_clone_prompt=clone_prompts[char_name],
        )
        sf.write(str(out_path), wavs[0], sr)
        manifest_rows.append({"index": idx, "character": char_name, "text": text, "file": filename})

    # ------------------------------------------------------------------
    # Save manifest CSV
    # ------------------------------------------------------------------
    manifest_path = output_dir / "manifest.csv"
    with open(manifest_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["index", "character", "text", "file"])
        writer.writeheader()
        writer.writerows(manifest_rows)

    merged_path = None
    if args.merge_output:
        merged_path = merge_output_files(
            output_dir=output_dir,
            manifest_rows=manifest_rows,
            merged_filename=args.merge_filename,
            pause_ms=args.merge_pause_ms,
            speaker_change_pause_ms=args.speaker_change_pause_ms,
        )

    print(f"\nDone! {len(dialogue)} audio files saved to: {output_dir.resolve()}")
    print(f"Manifest: {manifest_path}")
    if merged_path is not None:
        print(f"Merged WAV: {merged_path}")


if __name__ == "__main__":
    main()
