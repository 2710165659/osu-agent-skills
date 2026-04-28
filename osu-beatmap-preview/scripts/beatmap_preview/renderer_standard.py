from __future__ import annotations

from pathlib import Path

from .errors import PreviewError
from .models import Beatmap, StandardHitObject
from .standard import get_standard_output_extension, render_standard_gif, render_standard_grid


def render_standard_preview(beatmap: Beatmap, output_path: Path) -> Path:
    """渲染 osu!standard 预览图。"""
    try:
        hit_objects = [hit_object for hit_object in beatmap.hit_objects if isinstance(hit_object, StandardHitObject)]
        if not hit_objects:
            raise PreviewError("standard beatmap has no hit objects")

        output_path = output_path.with_suffix(get_standard_output_extension())
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if output_path.suffix == ".gif":
            frames, frame_duration_ms, loop = render_standard_gif(beatmap, hit_objects)
            frames[0].save(
                output_path,
                save_all=True,
                append_images=frames[1:],
                duration=frame_duration_ms,
                loop=loop,
                optimize=True,
                disposal=2,
            )
        else:
            image = render_standard_grid(beatmap, hit_objects)
            image.save(output_path)
        return output_path
    except PreviewError:
        raise
    except (OSError, KeyError, ValueError, IndexError, ZeroDivisionError) as exc:
        raise PreviewError("Failed to render preview.") from exc
