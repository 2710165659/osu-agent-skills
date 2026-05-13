from __future__ import annotations

import re
import tempfile
from pathlib import Path

from .composer import save_animated_gif, save_png
from .downloader import download_beatmap_file
from .errors import PreviewError
from .models import Beatmap
from .parser import parse_beatmap
from .standard.renderer import render_standard
from .taiko.renderer import render_taiko_grid
from .catch.renderer import render_catch_grid
from .mania.renderer import render_mania_grid


def generate_preview(bid: str, skill_root: Path, fmt: str = "gif") -> dict[str, object]:
    if not bid.isdigit():
        raise PreviewError("bid must be numeric")

    temp_root = Path(tempfile.gettempdir()) / "osu-beatmap-preview"
    beatmap_path = download_beatmap_file(bid=bid, temp_dir=temp_root / "osu-download-cache")
    beatmap = parse_beatmap(beatmap_path)
    ext = fmt if beatmap.mode == 0 else "png"
    output_path = temp_root / "outputs" / f"{bid}.{ext}"

    preview_path = _render_preview_for_mode(beatmap, output_path, fmt)

    return {
        "status": "success",
        "msg": f"preview generated successfully for bid {bid}",
        "preview-img": str(preview_path.resolve()),
        "beatmap-info": {
            "meta-data": _format_section_keys(beatmap.metadata),
            "difficulty": _format_section_keys(beatmap.difficulty),
        },
    }




def _format_section_keys(section: dict[str, str]) -> dict[str, str]:
    return {
        re.sub(
            r"([A-Z]+)([A-Z][a-z])", r"\1-\2",
            re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", key),
        ).lower(): value
        for key, value in section.items()
    }


def _render_preview_for_mode(beatmap: Beatmap, output_path: Path, fmt: str) -> Path:
    if beatmap.mode == 0:
        from .models import StandardHitObject
        hit_objects = [ho for ho in beatmap.hit_objects if isinstance(ho, StandardHitObject)]
        if not hit_objects:
            raise PreviewError("standard beatmap has no hit objects")
        result = render_standard(beatmap, hit_objects, fmt)
        if fmt == "gif":
            frames, frame_duration_ms, loop = result
            save_animated_gif(frames, output_path, frame_duration_ms, loop)
        else:
            save_png(result, output_path)
        return output_path

    if beatmap.mode == 1:
        return render_taiko_grid(beatmap, output_path)

    if beatmap.mode == 2:
        return render_catch_grid(beatmap, output_path)

    if beatmap.mode == 3:
        return render_mania_grid(beatmap, output_path)

    raise PreviewError(f"unsupported beatmap mode: {beatmap.mode}")
