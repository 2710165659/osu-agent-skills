from __future__ import annotations

import re
import tempfile
from pathlib import Path

from .downloader import download_beatmap_file
from .errors import PreviewError
from .models import Beatmap
from .parser import parse_beatmap
from .renderer_catch import render_catch_preview
from .renderer_mania import render_mania_preview
from .renderer_standard import render_standard_preview
from .renderer_taiko import render_taiko_preview
from .standard import get_standard_output_extension


def generate_preview(bid: str, skill_root: Path) -> dict[str, object]:
    """下载谱面并返回 JSON 友好的预览结果。"""
    if not bid.isdigit():
        raise PreviewError("bid must be numeric")

    temp_root = Path(tempfile.gettempdir()) / "osu-beatmap-preview"
    beatmap_path = download_beatmap_file(bid=bid, temp_dir=temp_root / "osu-download-cache")
    beatmap = parse_beatmap(beatmap_path)

    output_path = temp_root / "outputs" / _build_output_filename(beatmap, bid)
    preview_path = _render_preview_for_mode(beatmap, output_path)

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
    # 输出字段按 skill 约定从 osu! 原始 CamelCase 转为 hyphen-case。
    return {
        re.sub(
            r"([A-Z]+)([A-Z][a-z])",
            r"\1-\2",
            re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", key),
        ).lower(): value
        for key, value in section.items()
    }


def _render_preview_for_mode(beatmap: Beatmap, output_path: Path) -> Path:
    # osu! 模式编号：0=standard, 1=taiko, 2=catch, 3=mania。
    if beatmap.mode == 0:
        return render_standard_preview(beatmap, output_path)
    if beatmap.mode == 1:
        return render_taiko_preview(beatmap, output_path)
    if beatmap.mode == 2:
        return render_catch_preview(beatmap, output_path)
    if beatmap.mode == 3:
        return render_mania_preview(beatmap, output_path)
    raise PreviewError(f"unsupported beatmap mode: {beatmap.mode}")


def _build_output_filename(beatmap: Beatmap, bid: str) -> str:
    if beatmap.mode == 0:
        return f"{bid}{get_standard_output_extension()}"
    return f"{bid}.png"
