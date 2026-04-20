from __future__ import annotations

from pathlib import Path

from .errors import PreviewError
from .catch import render_catch_grid
from .models import Beatmap
from .models import CatchHitObject


def render_catch_preview(beatmap: Beatmap, output_path: Path) -> Path:
    """渲染 osu!catch 预览图。"""
    try:
        hit_objects = [hit_object for hit_object in beatmap.hit_objects if isinstance(hit_object, CatchHitObject)]
        if not hit_objects:
            raise PreviewError("catch beatmap has no hit objects")

        image = render_catch_grid(beatmap, hit_objects)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path)
        return output_path
    except PreviewError:
        raise
    except (OSError, KeyError, ValueError, IndexError, ZeroDivisionError) as exc:
        raise PreviewError("Failed to render preview.") from exc
