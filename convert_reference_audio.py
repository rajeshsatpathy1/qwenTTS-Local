#!/usr/bin/env python3
"""Convert spoken reference audio like M4A into a clone-ready WAV file."""

import argparse
import subprocess
from pathlib import Path

import imageio_ffmpeg


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert a spoken reference recording into a mono WAV for Qwen TTS voice cloning."
    )
    parser.add_argument("input", help="Path to the source audio file, such as .m4a or .mp3")
    parser.add_argument(
        "--output",
        help="Output WAV path. Defaults to the input path with a .wav extension.",
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=24000,
        help="Output WAV sample rate. Default: 24000",
    )
    parser.add_argument(
        "--channels",
        type=int,
        default=1,
        help="Number of output channels. Default: 1",
    )
    parser.add_argument(
        "--normalize",
        action="store_true",
        help="Normalize the converted speech clip before export.",
    )
    return parser


def convert_reference_audio(
    input_path: Path,
    output_path: Path,
    sample_rate: int,
    channels: int,
    normalize: bool,
) -> Path:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        ffmpeg,
        "-y",
        "-i",
        str(input_path),
        "-ar",
        str(sample_rate),
        "-ac",
        str(channels),
    ]

    if normalize:
        command.extend(["-af", "loudnorm"])

    command.append(str(output_path))

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            "FFmpeg conversion failed.\n"
            f"Command: {' '.join(command)}\n"
            f"stderr:\n{result.stderr.strip()}"
        )

    return output_path


def main() -> None:
    args = build_parser().parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Input audio file not found: {input_path}")

    output_path = Path(args.output) if args.output else input_path.with_suffix(".wav")
    output_path = convert_reference_audio(
        input_path=input_path,
        output_path=output_path,
        sample_rate=args.sample_rate,
        channels=args.channels,
        normalize=args.normalize,
    )

    print(f"Created WAV: {output_path}")
    print(f"Sample rate: {args.sample_rate}")
    print(f"Channels: {args.channels}")
    print(f"Normalized: {args.normalize}")


if __name__ == "__main__":
    main()