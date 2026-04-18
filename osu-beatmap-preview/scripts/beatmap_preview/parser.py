from __future__ import annotations

from pathlib import Path

from .errors import PreviewError
from .models import (
    Beatmap,
    CatchHitObject,
    HitObject,
    ManiaHitObject,
    StandardHitObject,
    TaikoHitObject,
    TimingPoint,
)


def parse_beatmap(beatmap_path: Path) -> Beatmap:
    try:
        sections = _split_sections(beatmap_path.read_text(encoding="utf-8-sig"))

        metadata = _parse_key_value_section(sections, "Metadata")
        difficulty = _parse_key_value_section(sections, "Difficulty")
        general = _parse_key_value_section(sections, "General")
        timing_points = _parse_timing_points(sections)
        mode = int(general["Mode"])

        if mode == 0:
            hit_objects = _parse_standard_hit_objects(sections, difficulty, timing_points)
        elif mode == 1:
            hit_objects = _parse_taiko_hit_objects(sections, difficulty, timing_points)
        elif mode == 2:
            hit_objects = _parse_catch_hit_objects(sections, difficulty, timing_points)
        elif mode == 3:
            hit_objects = _parse_mania_hit_objects(sections, difficulty, timing_points)
        else:
            raise PreviewError(f"Unsupported beatmap mode: {mode}")

        return Beatmap(
            metadata=metadata,
            difficulty=difficulty,
            general=general,
            timing_points=timing_points,
            hit_objects=hit_objects,
        )
    except Exception as exc:
        raise PreviewError("Failed to parse beatmap.") from exc


def _split_sections(content: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current_section = ""

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("//"):
            continue

        if line.startswith("[") and line.endswith("]"):
            current_section = line[1:-1]
            sections[current_section] = []
            continue

        if not current_section:
            continue
        sections[current_section].append(line)

    return sections


def _parse_key_value_section(sections: dict[str, list[str]], section_name: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in sections[section_name]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip()

    return values


def _parse_timing_points(sections: dict[str, list[str]]) -> list[TimingPoint]:
    timing_points: list[TimingPoint] = []
    for line in sections["TimingPoints"]:
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 2:
            continue

        meter = int(parts[2]) if len(parts) > 2 and parts[2] else 4
        if meter <= 0:
            meter = 4
        uninherited = len(parts) < 7 or parts[6] == "1"
        timing_points.append(
            TimingPoint(
                time=float(parts[0]),
                beat_length=float(parts[1]),
                meter=meter,
                uninherited=uninherited,
            )
        )

    return sorted(timing_points, key=lambda point: (point.time, point.beat_length))


def _parse_standard_hit_objects(
    sections: dict[str, list[str]],
    difficulty: dict[str, str],
    timing_points: list[TimingPoint],
) -> list[HitObject]:
    hit_objects: list[HitObject] = []
    for line in sections["HitObjects"]:
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 5:
            continue

        x = int(parts[0])
        y = int(parts[1])
        start_time = int(parts[2])
        hit_type = int(parts[3])
        end_time = _parse_object_end_time(parts, start_time, hit_type, difficulty, timing_points)

        hit_objects.append(
            StandardHitObject(
                x=x,
                y=y,
                start_time=start_time,
                end_time=end_time,
                hit_type=hit_type,
            )
        )

    return _sort_hit_objects(hit_objects)


def _parse_taiko_hit_objects(
    sections: dict[str, list[str]],
    difficulty: dict[str, str],
    timing_points: list[TimingPoint],
) -> list[HitObject]:
    hit_objects: list[HitObject] = []
    for line in sections["HitObjects"]:
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 5:
            continue

        start_time = int(parts[2])
        hit_type = int(parts[3])
        hitsound = int(parts[4])
        end_time = _parse_object_end_time(parts, start_time, hit_type, difficulty, timing_points)

        hit_objects.append(
            TaikoHitObject(
                start_time=start_time,
                end_time=end_time,
                hit_type=hit_type,
                hitsound=hitsound,
            )
        )

    return _sort_hit_objects(hit_objects)


def _parse_catch_hit_objects(
    sections: dict[str, list[str]],
    difficulty: dict[str, str],
    timing_points: list[TimingPoint],
) -> list[HitObject]:
    hit_objects: list[HitObject] = []
    for line in sections["HitObjects"]:
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 5:
            continue

        x = int(parts[0])
        start_time = int(parts[2])
        hit_type = int(parts[3])
        end_time = _parse_object_end_time(parts, start_time, hit_type, difficulty, timing_points)

        hit_objects.append(
            CatchHitObject(
                x=x,
                start_time=start_time,
                end_time=end_time,
                hit_type=hit_type,
            )
        )

    return _sort_hit_objects(hit_objects)


def _parse_mania_hit_objects(
    sections: dict[str, list[str]],
    difficulty: dict[str, str],
    timing_points: list[TimingPoint],
) -> list[HitObject]:
    key_count = int(float(difficulty["CircleSize"]))
    hit_objects: list[HitObject] = []
    for line in sections["HitObjects"]:
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 5:
            continue

        x = int(parts[0])
        start_time = int(parts[2])
        hit_type = int(parts[3])
        lane = max(0, min(key_count - 1, x * key_count // 512))
        is_long_note = bool(hit_type & 128)
        end_time = start_time
        if is_long_note:
            end_time = int(parts[5].split(":", 1)[0])

        hit_objects.append(
            ManiaHitObject(
                lane=lane,
                start_time=start_time,
                end_time=end_time,
                is_long_note=is_long_note,
            )
        )

    return _sort_hit_objects(hit_objects)


def _parse_object_end_time(
    parts: list[str],
    start_time: int,
    hit_type: int,
    difficulty: dict[str, str],
    timing_points: list[TimingPoint],
) -> int:
    if hit_type & 8:
        return int(parts[5])
    if hit_type & 2:
        return _parse_slider_end_time(parts, start_time, difficulty, timing_points)
    return start_time


def _parse_slider_end_time(
    parts: list[str],
    start_time: int,
    difficulty: dict[str, str],
    timing_points: list[TimingPoint],
) -> int:
    # Slider duration depends on the active red line beat length plus the latest velocity multiplier.
    slides = int(parts[6])
    pixel_length = float(parts[7])
    slider_multiplier = float(difficulty["SliderMultiplier"])
    beat_length, slider_velocity = _resolve_slider_timing(start_time, timing_points)
    duration = pixel_length / (slider_multiplier * 100 * slider_velocity) * beat_length * slides
    return start_time + round(duration)


def _resolve_slider_timing(start_time: int, timing_points: list[TimingPoint]) -> tuple[float, float]:
    beat_length = timing_points[0].beat_length
    slider_velocity = 1.0

    for point in timing_points:
        if point.time > start_time:
            break
        if point.uninherited:
            beat_length = point.beat_length
        elif point.beat_length < 0:
            slider_velocity = -100 / point.beat_length

    return beat_length, slider_velocity


def _sort_hit_objects(hit_objects: list[HitObject]) -> list[HitObject]:
    return sorted(hit_objects, key=lambda hit_object: (hit_object.start_time, hit_object.end_time))
