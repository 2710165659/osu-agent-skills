from __future__ import annotations

from pathlib import Path

from .errors import PreviewError
from .models import Beatmap


def render_taiko_preview(beatmap: Beatmap, output_path: Path) -> Path:
    """渲染 osu!taiko 预览图。"""
    raise PreviewError("taiko preview rendering is not implemented yet")
