#!/usr/bin/env python3
"""Convert audio files to MP3 using a bundled FFmpeg binary."""

import argparse
from pathlib import Path

import imageio_ffmpeg
from pydub import AudioSegment


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert an audio file to MP3 for easier sharing and playback."
    )
    parser.add_argument("input", help="Path to the source audio file, typically WAV.")
    parser.add_argument(
        "--output",
        help="Output MP3 path. Defaults to the input path with an .mp3 extension.",
    )
    parser.add_argument(
        "--bitrate",
        default="192k",
        help="MP3 bitrate to use. Default: 192k",
    )
    return parser


def convert_to_mp3(input_path: Path, output_path: Path, bitrate: str) -> Path:
    AudioSegment.converter = imageio_ffmpeg.get_ffmpeg_exe()
    audio = AudioSegment.from_file(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    audio.export(output_path, format="mp3", bitrate=bitrate)
    return output_path


def main() -> None:
    args = build_parser().parse_args()
    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Input audio file not found: {input_path}")

    output_path = Path(args.output) if args.output else input_path.with_suffix(".mp3")
    output_path = convert_to_mp3(input_path, output_path, args.bitrate)

    print(f"Created MP3: {output_path}")
    print(f"Bitrate: {args.bitrate}")


if __name__ == "__main__":
    main()