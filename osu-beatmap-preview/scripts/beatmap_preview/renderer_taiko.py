from __future__ import annotations

from pathlib import Path

from .errors import PreviewError
from .models import Beatmap
from .models import TaikoHitObject
from .taiko import render_taiko_grid


def render_taiko_preview(beatmap: Beatmap, output_path: Path) -> Path:
    """渲染 osu!taiko 预览图。"""
    try:
        hit_objects = [hit_object for hit_object in beatmap.hit_objects if isinstance(hit_object, TaikoHitObject)]
        if not hit_objects:
            raise PreviewError("taiko beatmap has no hit objects")

        image = render_taiko_grid(beatmap, hit_objects)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path)
        return output_path
    except PreviewError:
        raise
    except (OSError, KeyError, ValueError, IndexError, ZeroDivisionError) as exc:
        raise PreviewError("Failed to render preview.") from exc
