#!/usr/bin/env python3
"""Merge narrated WAV fragments into one output file with configurable pauses."""

import argparse
import csv
from pathlib import Path

import numpy as np
import soundfile as sf


def merge_output_files(
    output_dir: Path,
    manifest_rows: list[dict],
    merged_filename: str,
    pause_ms: int,
    speaker_change_pause_ms: int,
) -> Path:
    segments = []
    sample_rate = None

    for index, row in enumerate(manifest_rows):
        wav_path = output_dir / row["file"]
        audio, current_sr = sf.read(str(wav_path), dtype="float32")

        if audio.ndim > 1:
            audio = audio.mean(axis=1)

        if sample_rate is None:
            sample_rate = current_sr
        elif current_sr != sample_rate:
            raise ValueError(
                f"Sample rate mismatch for {wav_path}: {current_sr} != {sample_rate}"
            )

        segments.append(audio)

        if index == len(manifest_rows) - 1:
            continue

        next_row = manifest_rows[index + 1]
        current_pause_ms = (
            speaker_change_pause_ms
            if row["character"] != next_row["character"]
            else pause_ms
        )

        if current_pause_ms > 0:
            pause = np.zeros(
                int(sample_rate * current_pause_ms / 1000.0), dtype=np.float32
            )
            segments.append(pause)

    merged_audio = np.concatenate(segments)
    merged_path = output_dir / merged_filename
    sf.write(str(merged_path), merged_audio, sample_rate)
    return merged_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Merge chunked narration WAV files into one final WAV."
    )
    parser.add_argument(
        "output_dir",
        help="Directory containing manifest.csv and the numbered WAV files.",
    )
    parser.add_argument(
        "--manifest",
        default="manifest.csv",
        help="Manifest CSV filename inside output_dir. Default: manifest.csv",
    )
    parser.add_argument(
        "--out",
        default="merged_output.wav",
        help="Merged WAV filename to create inside output_dir. Default: merged_output.wav",
    )
    parser.add_argument(
        "--pause-ms",
        type=int,
        default=120,
        help="Pause between adjacent fragments by the same speaker. Default: 120",
    )
    parser.add_argument(
        "--speaker-change-pause-ms",
        type=int,
        default=220,
        help="Pause between adjacent fragments when the speaker changes. Default: 220",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    manifest_path = output_dir / args.manifest

    if not output_dir.exists():
        raise FileNotFoundError(f"Output directory not found: {output_dir}")
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    with manifest_path.open("r", encoding="utf-8", newline="") as fh:
        manifest_rows = list(csv.DictReader(fh))

    if not manifest_rows:
        raise ValueError(f"Manifest is empty: {manifest_path}")

    merged_path = merge_output_files(
        output_dir=output_dir,
        manifest_rows=manifest_rows,
        merged_filename=args.out,
        pause_ms=args.pause_ms,
        speaker_change_pause_ms=args.speaker_change_pause_ms,
    )

    print(f"Merged WAV: {merged_path}")
    print(f"Fragments: {len(manifest_rows)}")
    print(f"Pause ms: {args.pause_ms}")
    print(f"Speaker change pause ms: {args.speaker_change_pause_ms}")


if __name__ == "__main__":
    main()