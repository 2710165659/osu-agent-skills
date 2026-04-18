from __future__ import annotations

import re
from pathlib import Path

from .downloader import download_beatmap_file
from .errors import PreviewError
from .parser import parse_beatmap
from .renderer_catch import render_catch_preview
from .renderer_mania import render_mania_preview
from .renderer_standard import render_standard_preview
from .renderer_taiko import render_taiko_preview


def generate_preview(bid: str, skill_root: Path) -> dict[str, object]:
    """Download a beatmap, parse it, dispatch to the right renderer, and return JSON-ready output."""
    if not bid.isdigit():
        raise PreviewError("bid must be numeric")

    beatmap_path = download_beatmap_file(bid=bid, temp_dir=skill_root / "temp")
    beatmap = parse_beatmap(beatmap_path)

    output_path = skill_root / "outputs" / f"{bid}.png"
    preview_path = _render_preview_for_mode(beatmap, output_path)
    if preview_path is None:
        raise PreviewError(f"preview rendering for mode {beatmap.mode} is not implemented yet")

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
            r"([A-Z]+)([A-Z][a-z])",
            r"\1-\2",
            re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", key),
        ).lower(): value
        for key, value in section.items()
    }


def _render_preview_for_mode(beatmap, output_path: Path) -> Path | None:
    # osu! uses mode ids 0=standard, 1=taiko, 2=catch, 3=mania.
    if beatmap.mode == 0:
        return render_standard_preview(beatmap, output_path)
    if beatmap.mode == 1:
        return render_taiko_preview(beatmap, output_path)
    if beatmap.mode == 2:
        return render_catch_preview(beatmap, output_path)
    if beatmap.mode == 3:
        return render_mania_preview(beatmap, output_path)
    raise PreviewError(f"unsupported beatmap mode: {beatmap.mode}")
