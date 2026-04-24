#!/usr/bin/env python3
"""Convert an audio file into a simple MP4 video with a solid background."""

import argparse
import subprocess
from pathlib import Path

import imageio_ffmpeg


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert an audio file into an MP4 video for easy sharing."
    )
    parser.add_argument("input", help="Path to the source audio file.")
    parser.add_argument(
        "--output",
        help="Output MP4 path. Defaults to the input path with an .mp4 extension.",
    )
    parser.add_argument(
        "--size",
        default="1080x1920",
        help="Video size in WIDTHxHEIGHT format. Default: 1080x1920",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=30,
        help="Video frame rate. Default: 30",
    )
    parser.add_argument(
        "--color",
        default="black",
        help="Solid background color. Default: black",
    )
    parser.add_argument(
        "--image",
        help="Optional background image path. If provided, it will be scaled to fit inside the target frame.",
    )
    parser.add_argument(
        "--audio-bitrate",
        default="192k",
        help="AAC audio bitrate. Default: 192k",
    )
    return parser


def convert_to_mp4(
    input_path: Path,
    output_path: Path,
    size: str,
    fps: int,
    color: str,
    image_path: Path | None,
    audio_bitrate: str,
) -> Path:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    command = [ffmpeg, "-y"]

    if image_path is not None:
        width, height = size.split("x", maxsplit=1)
        video_filter = (
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color={color}"
        )
        command.extend(
            [
                "-loop",
                "1",
                "-framerate",
                str(fps),
                "-i",
                str(image_path),
                "-i",
                str(input_path),
                "-vf",
                video_filter,
            ]
        )
    else:
        command.extend(
            [
                "-f",
                "lavfi",
                "-i",
                f"color=c={color}:s={size}:r={fps}",
                "-i",
                str(input_path),
            ]
        )

    command.extend(
        [
            "-c:v",
            "libx264",
            "-tune",
            "stillimage",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            audio_bitrate,
            "-shortest",
            str(output_path),
        ]
    )

    subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return output_path


def main() -> None:
    args = build_parser().parse_args()
    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Input audio file not found: {input_path}")

    image_path = Path(args.image) if args.image else None
    if image_path is not None and not image_path.exists():
        raise FileNotFoundError(f"Background image not found: {image_path}")

    output_path = Path(args.output) if args.output else input_path.with_suffix(".mp4")
    output_path = convert_to_mp4(
        input_path=input_path,
        output_path=output_path,
        size=args.size,
        fps=args.fps,
        color=args.color,
        image_path=image_path,
        audio_bitrate=args.audio_bitrate,
    )

    print(f"Created MP4: {output_path}")
    print(f"Size: {args.size}")
    print(f"FPS: {args.fps}")
    print(f"Color: {args.color}")
    if image_path is not None:
        print(f"Image: {image_path}")
    print(f"Audio bitrate: {args.audio_bitrate}")


if __name__ == "__main__":
    main()