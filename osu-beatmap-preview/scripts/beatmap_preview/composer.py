from __future__ import annotations

from pathlib import Path

from PIL import Image


def save_animated_gif(
    frames: list[Image.Image],
    output_path: Path,
    frame_duration_ms: int,
    loop: int,
) -> None:
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=frame_duration_ms,
        loop=loop,
        optimize=True,
        disposal=2,
    )


def save_png(image: Image.Image, output_path: Path) -> None:
    image.save(output_path)
