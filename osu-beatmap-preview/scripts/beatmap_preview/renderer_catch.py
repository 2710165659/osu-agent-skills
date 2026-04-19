from __future__ import annotations

from pathlib import Path

from .errors import PreviewError
from .models import Beatmap


def render_catch_preview(beatmap: Beatmap, output_path: Path) -> Path:
    """渲染 osu!catch 预览图。"""
    raise PreviewError("catch preview rendering is not implemented yet")
