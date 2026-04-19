from __future__ import annotations

from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageFont

from ..models import Beatmap, BreakPeriod, StandardHitObject
from .config import (
    BREAK_FADE_DURATION_MS,
    BREAK_GAP_MS,
    BREAK_MIN_DURATION_MS,
    BREAK_OVERLAY_BAR_HEIGHT,
    BREAK_OVERLAY_BAR_WIDTH_RATIO,
    BREAK_OVERLAY_COLOR,
    BREAK_OVERLAY_COUNTER_FONT_SIZE,
    BREAK_OVERLAY_INFO_COLOR,
    BREAK_OVERLAY_INFO_FONT_SIZE,
    BREAK_OVERLAY_INFO_TOP_GAP,
    BROKEN_GAMEFIELD_ROUNDING_ALLOWANCE,
    CANVAS_BACKGROUND_COLOR,
    HORIZONTAL_PAGE_MARGIN,
    IMAGE_BACKGROUND_COLOR,
    IMAGE_HEIGHT,
    IMAGE_WIDTH,
    IMAGES_PER_ROW,
    INTER_ROW_GAP,
    INTRA_ROW_IMAGE_GAP,
    LEFT_PANEL_BACKGROUND_COLOR,
    LEFT_PANEL_WIDTH,
    MS_PER_ROW_DURATION,
    OBJECT_RADIUS,
    PLAYFIELD_HEIGHT,
    PLAYFIELD_STORYBOARD_SHIFT,
    PLAYFIELD_VIEWPORT_RATIO,
    PLAYFIELD_WIDTH,
    POST_HIT_FADE_MS,
    PREVIEW_TIME_LABEL_COLOR,
    ROW_COUNT,
    SLIDER_BODY_SUPERSAMPLE,
    SLIDER_BORDER_WIDTH,
    SLIDER_FADE_OUT_MS,
    SLIDER_LEGACY_BORDER_PORTION,
    SLIDER_LEGACY_SHADOW_ALPHA,
    SLIDER_LEGACY_TRACK_ALPHA,
    SNAKING_IN_SLIDERS,
    SNAKING_OUT_SLIDERS,
    SPINNER_FADE_OUT_MS,
    TIME_LABEL_COLOR,
    TIME_LABEL_FONT_SIZE,
    TIME_LABEL_HEIGHT,
    TIME_LABEL_NOTE_COLOR,
    TIME_LABEL_NOTE_FONT_SIZE,
    TIME_LABEL_NOTE_TOP_GAP,
    TIME_LABEL_TOP_GAP,
    VERTICAL_PAGE_MARGIN,
)
from .row_selection import RowTiming, choose_row_start_times
from .skin import StandardSkin, load_standard_skin
from .slider_path import build_slider_path, path_position_at, slice_path


@dataclass(frozen=True)
class FrameLayout:
    playfield_left: int
    playfield_top: int
    scale: float


@dataclass(frozen=True)
class ComboInfo:
    color: tuple[int, int, int]
    number: int


@dataclass(frozen=True)
class RenderSettings:
    circle_radius: float
    circle_diameter: int
    preempt_ms: int
    fade_in_ms: float


def render_standard_grid(beatmap: Beatmap, hit_objects: list[StandardHitObject]) -> Image.Image:
    """Render osu!standard as a grid of gameplay snapshots."""
    skin = load_standard_skin()
    settings = _build_render_settings(beatmap)
    frame_layout = _build_frame_layout()
    combo_info = _build_combo_info(hit_objects, skin.combo_colors)
    row_timings = choose_row_start_times(
        beatmap=beatmap,
        hit_objects=hit_objects,
        row_count=ROW_COUNT,
        images_per_row=IMAGES_PER_ROW,
        ms_per_row_duration=MS_PER_ROW_DURATION,
        break_gap_ms=BREAK_GAP_MS,
    )
    font_regular = ImageFont.load_default(size=TIME_LABEL_FONT_SIZE)
    font_note = ImageFont.load_default(size=TIME_LABEL_NOTE_FONT_SIZE)
    canvas = Image.new("RGBA", _build_canvas_size(), CANVAS_BACKGROUND_COLOR)
    draw = ImageDraw.Draw(canvas)

    for row_index, row_timing in enumerate(row_timings):
        y = VERTICAL_PAGE_MARGIN + row_index * (
            IMAGE_HEIGHT + TIME_LABEL_TOP_GAP + TIME_LABEL_HEIGHT + INTER_ROW_GAP
        )
        for image_index in range(IMAGES_PER_ROW):
            snapshot_time = row_timing.start_time + image_index * MS_PER_ROW_DURATION
            x = HORIZONTAL_PAGE_MARGIN + image_index * (IMAGE_WIDTH + INTRA_ROW_IMAGE_GAP)
            frame = _render_frame(
                hit_objects=hit_objects,
                combo_info=combo_info,
                skin=skin,
                settings=settings,
                frame_layout=frame_layout,
                snapshot_time=snapshot_time,
                break_periods=row_timing.break_periods if row_timing.is_preview else (),
            )
            canvas.alpha_composite(frame, (x, y))
            note = _build_time_label_note(row_timing) if image_index == 0 else None
            is_preview_label = row_timing.is_preview and image_index == 0
            _draw_time_label(
                draw,
                _format_time(snapshot_time),
                x,
                y + IMAGE_HEIGHT + TIME_LABEL_TOP_GAP,
                font_regular,
                font_note,
                note,
                PREVIEW_TIME_LABEL_COLOR if is_preview_label else TIME_LABEL_COLOR,
                PREVIEW_TIME_LABEL_COLOR if is_preview_label else TIME_LABEL_NOTE_COLOR,
            )

    return canvas


def _build_render_settings(beatmap: Beatmap) -> RenderSettings:
    circle_size = float(beatmap.difficulty["CircleSize"])
    approach_rate = float(beatmap.difficulty["ApproachRate"])
    scale = (1.0 - 0.7 * ((circle_size - 5.0) / 5.0)) / 2.0 * BROKEN_GAMEFIELD_ROUNDING_ALLOWANCE
    circle_radius = OBJECT_RADIUS * scale
    circle_diameter = max(1, round(circle_radius * 2))
    preempt_ms = _difficulty_range_int(approach_rate, 1800, 1200, 450)
    fade_in_ms = 400 * min(1, preempt_ms / 450)
    return RenderSettings(
        circle_radius=circle_radius,
        circle_diameter=circle_diameter,
        preempt_ms=preempt_ms,
        fade_in_ms=fade_in_ms,
    )


def _difficulty_range_int(difficulty: float, minimum: int, middle: int, maximum: int) -> int:
    if difficulty > 5:
        return int(middle + (maximum - middle) * ((difficulty - 5) / 5))
    if difficulty < 5:
        return int(middle + (middle - minimum) * ((difficulty - 5) / 5))
    return middle


def _build_frame_layout() -> FrameLayout:
    available_width = IMAGE_WIDTH - LEFT_PANEL_WIDTH
    viewport_width = min(available_width, IMAGE_HEIGHT * PLAYFIELD_WIDTH / PLAYFIELD_HEIGHT)
    playfield_width = round(viewport_width * PLAYFIELD_VIEWPORT_RATIO)
    playfield_height = round(playfield_width * PLAYFIELD_HEIGHT / PLAYFIELD_WIDTH)
    scale = playfield_width / PLAYFIELD_WIDTH
    return FrameLayout(
        playfield_left=LEFT_PANEL_WIDTH + (available_width - playfield_width) // 2,
        playfield_top=round((IMAGE_HEIGHT - playfield_height) / 2 + PLAYFIELD_STORYBOARD_SHIFT * scale),
        scale=scale,
    )


def _build_canvas_size() -> tuple[int, int]:
    width = HORIZONTAL_PAGE_MARGIN * 2 + IMAGES_PER_ROW * IMAGE_WIDTH + (IMAGES_PER_ROW - 1) * INTRA_ROW_IMAGE_GAP
    row_height = IMAGE_HEIGHT + TIME_LABEL_TOP_GAP + TIME_LABEL_HEIGHT
    height = VERTICAL_PAGE_MARGIN * 2 + ROW_COUNT * row_height + (ROW_COUNT - 1) * INTER_ROW_GAP
    return width, height


def _build_combo_info(
    hit_objects: list[StandardHitObject],
    combo_colors: list[tuple[int, int, int]],
) -> dict[int, ComboInfo]:
    combo_info: dict[int, ComboInfo] = {}
    color_index = 0
    number = 0
    previous_was_spinner = False

    for index, hit_object in enumerate(hit_objects):
        starts_combo = index == 0 or previous_was_spinner or (hit_object.new_combo and not _is_spinner(hit_object))
        if starts_combo:
            if index > 0:
                color_index = (color_index + hit_object.combo_offset + 1) % len(combo_colors)
            number = 1
        else:
            number += 1

        combo_info[index] = ComboInfo(color=combo_colors[color_index], number=number)
        previous_was_spinner = _is_spinner(hit_object)

    return combo_info


def _render_frame(
    hit_objects: list[StandardHitObject],
    combo_info: dict[int, ComboInfo],
    skin: StandardSkin,
    settings: RenderSettings,
    frame_layout: FrameLayout,
    snapshot_time: int,
    break_periods: tuple[BreakPeriod, ...],
) -> Image.Image:
    frame = Image.new("RGBA", (IMAGE_WIDTH, IMAGE_HEIGHT), IMAGE_BACKGROUND_COLOR)
    draw = ImageDraw.Draw(frame)
    draw.rectangle((0, 0, LEFT_PANEL_WIDTH, IMAGE_HEIGHT), fill=LEFT_PANEL_BACKGROUND_COLOR)

    visible_indexes = [
        index
        for index, hit_object in enumerate(hit_objects)
        if _is_visible(hit_object, snapshot_time, settings.preempt_ms)
    ]

    # Later objects are painted first so the next object to hit remains readable on top.
    for index in sorted(visible_indexes, key=lambda item: hit_objects[item].start_time, reverse=True):
        hit_object = hit_objects[index]
        combo = combo_info[index]
        if _is_spinner(hit_object):
            _draw_spinner(frame, skin, hit_object, snapshot_time, settings, frame_layout)
        elif _is_slider(hit_object):
            _draw_slider(frame, skin, hit_object, combo, snapshot_time, settings, frame_layout)
        else:
            _draw_hit_circle(frame, skin, hit_object, combo, snapshot_time, settings, frame_layout)

    for index in sorted(visible_indexes, key=lambda item: hit_objects[item].start_time, reverse=True):
        hit_object = hit_objects[index]
        if not _is_spinner(hit_object):
            _draw_approach_circle(
                frame,
                skin,
                hit_object,
                combo_info[index].color,
                snapshot_time,
                settings,
                frame_layout,
            )

    current_break = _current_break_period(break_periods, snapshot_time)
    if current_break is not None:
        _draw_break_overlay(frame, current_break, snapshot_time)

    return frame


def _is_visible(hit_object: StandardHitObject, snapshot_time: int, preempt_ms: int) -> bool:
    lifetime_start = hit_object.start_time - preempt_ms
    if _is_slider(hit_object):
        lifetime_end = hit_object.end_time + SLIDER_FADE_OUT_MS
    elif _is_spinner(hit_object):
        lifetime_end = hit_object.end_time + SPINNER_FADE_OUT_MS
    else:
        lifetime_end = hit_object.start_time + POST_HIT_FADE_MS
    return lifetime_start <= snapshot_time <= lifetime_end


def _draw_hit_circle(
    frame: Image.Image,
    skin: StandardSkin,
    hit_object: StandardHitObject,
    combo: ComboInfo,
    snapshot_time: int,
    settings: RenderSettings,
    frame_layout: FrameLayout,
) -> None:
    alpha = _object_alpha(hit_object.start_time, hit_object.start_time, snapshot_time, settings)
    center = _to_frame_point(hit_object.x, hit_object.y, frame_layout)
    _draw_circle_piece(frame, skin, center, settings.circle_diameter, combo.color, alpha, str(combo.number))


def _draw_slider(
    frame: Image.Image,
    skin: StandardSkin,
    hit_object: StandardHitObject,
    combo: ComboInfo,
    snapshot_time: int,
    settings: RenderSettings,
    frame_layout: FrameLayout,
) -> None:
    alpha = _object_alpha(hit_object.start_time, hit_object.end_time, snapshot_time, settings)
    path = build_slider_path(hit_object)
    snaked_start, snaked_end = _slider_snaked_range(hit_object, snapshot_time, settings)
    visible_path = slice_path(path, snaked_start, snaked_end)
    frame_path = [_to_frame_point(x, y, frame_layout) for x, y in visible_path]
    body_width = max(1, round(settings.circle_diameter * frame_layout.scale))
    border_width = max(1, round(SLIDER_BORDER_WIDTH * frame_layout.scale))
    _draw_slider_body(frame, frame_path, body_width, border_width, skin.slider_border, skin.slider_track, alpha)

    head = _to_frame_point(hit_object.x, hit_object.y, frame_layout)
    _draw_slider_reverse_arrows(frame, skin, path, hit_object.slider_repeats, settings, frame_layout, alpha)
    _draw_slider_ball(frame, skin, path, hit_object, snapshot_time, settings, frame_layout, alpha)
    head_alpha = _slider_head_alpha(hit_object, snapshot_time, settings, snaked_start, snaked_end)
    if head_alpha > 0:
        _draw_circle_piece(frame, skin, head, settings.circle_diameter, combo.color, head_alpha, str(combo.number))


def _slider_snaked_range(
    hit_object: StandardHitObject,
    snapshot_time: int,
    settings: RenderSettings,
) -> tuple[float, float]:
    span_count = max(1, hit_object.slider_repeats)
    start = 0.0
    end = 1.0

    if snapshot_time < hit_object.start_time:
        if SNAKING_IN_SLIDERS:
            snake_start = hit_object.start_time - settings.preempt_ms
            end = max(0.0, min(1.0, (snapshot_time - snake_start) / (settings.preempt_ms / 3)))
        return start, end

    if snapshot_time > hit_object.end_time:
        return start, end

    completion = max(0.0, min(1.0, (snapshot_time - hit_object.start_time) / max(1, hit_object.end_time - hit_object.start_time)))
    span = min(span_count - 1, int(completion * span_count))
    span_progress = _slider_path_progress(span_count, completion)

    if span >= span_count - 1 and SNAKING_OUT_SLIDERS:
        if span % 2 == 1:
            end = span_progress
        else:
            start = span_progress

    return start, end


def _draw_spinner(
    frame: Image.Image,
    skin: StandardSkin,
    hit_object: StandardHitObject,
    snapshot_time: int,
    settings: RenderSettings,
    frame_layout: FrameLayout,
) -> None:
    alpha = _object_alpha(hit_object.start_time, hit_object.end_time, snapshot_time, settings)
    center = _to_frame_point(PLAYFIELD_WIDTH / 2, PLAYFIELD_HEIGHT / 2, frame_layout)
    size = round(min(PLAYFIELD_WIDTH, PLAYFIELD_HEIGHT) * 0.95 * frame_layout.scale)
    sprite = _resize_with_alpha(skin.spinner_circle, size, alpha)
    frame.alpha_composite(sprite, (round(center[0] - sprite.width / 2), round(center[1] - sprite.height / 2)))


def _draw_approach_circle(
    frame: Image.Image,
    skin: StandardSkin,
    hit_object: StandardHitObject,
    color: tuple[int, int, int],
    snapshot_time: int,
    settings: RenderSettings,
    frame_layout: FrameLayout,
) -> None:
    if snapshot_time >= hit_object.start_time:
        return

    elapsed = snapshot_time - (hit_object.start_time - settings.preempt_ms)
    progress = max(0.0, min(1.0, elapsed / settings.preempt_ms))
    alpha = 0.9 * min(1.0, elapsed / max(1.0, settings.fade_in_ms * 2))
    approach_scale = 4 - 3 * progress
    size = max(1, round(settings.circle_diameter * approach_scale * frame_layout.scale))
    center = _to_frame_point(hit_object.x, hit_object.y, frame_layout)
    sprite = _tint_sprite(skin.approachcircle, color, alpha, size)
    frame.alpha_composite(sprite, (round(center[0] - sprite.width / 2), round(center[1] - sprite.height / 2)))


def _object_alpha(
    start_time: int,
    end_time: int,
    snapshot_time: int,
    settings: RenderSettings,
) -> float:
    if snapshot_time < start_time:
        fade_start = start_time - settings.preempt_ms
        return max(0.0, min(1.0, (snapshot_time - fade_start) / settings.fade_in_ms))
    if snapshot_time <= end_time:
        return 1.0
    return max(0.0, 1.0 - (snapshot_time - end_time) / SLIDER_FADE_OUT_MS)


def _slider_head_alpha(
    hit_object: StandardHitObject,
    snapshot_time: int,
    settings: RenderSettings,
    snaked_start: float,
    snaked_end: float,
) -> float:
    if snaked_start > 0.001 or snaked_end <= 0.001:
        return 0.0
    if snapshot_time < hit_object.start_time:
        return _object_alpha(hit_object.start_time, hit_object.start_time, snapshot_time, settings)
    if snapshot_time <= hit_object.start_time + POST_HIT_FADE_MS:
        return 1.0 - (snapshot_time - hit_object.start_time) / POST_HIT_FADE_MS
    return 0.0


def _draw_slider_ball(
    frame: Image.Image,
    skin: StandardSkin,
    path: list[tuple[float, float]],
    hit_object: StandardHitObject,
    snapshot_time: int,
    settings: RenderSettings,
    frame_layout: FrameLayout,
    alpha: float,
) -> None:
    if not (hit_object.start_time <= snapshot_time <= hit_object.end_time):
        return

    completion = (snapshot_time - hit_object.start_time) / max(1, hit_object.end_time - hit_object.start_time)
    progress = _slider_path_progress(max(1, hit_object.slider_repeats), completion)
    center = _to_frame_point(*path_position_at(path, progress), frame_layout)
    follow_size = max(1, round(settings.circle_diameter * 2.4 * frame_layout.scale))
    ball_size = max(1, round(settings.circle_diameter * 1.15 * frame_layout.scale))
    follow_circle = _resize_with_alpha(skin.slider_follow_circle, follow_size, alpha * 0.7)
    ball = _resize_with_alpha(skin.slider_ball, ball_size, alpha)
    frame.alpha_composite(follow_circle, (round(center[0] - follow_circle.width / 2), round(center[1] - follow_circle.height / 2)))
    frame.alpha_composite(ball, (round(center[0] - ball.width / 2), round(center[1] - ball.height / 2)))


def _slider_path_progress(span_count: int, completion: float) -> float:
    span = min(span_count - 1, int(completion * span_count))
    progress = (completion * span_count) % 1
    if completion >= 1:
        progress = 1
    if span % 2 == 1:
        progress = 1 - progress
    return progress


def _draw_circle_piece(
    frame: Image.Image,
    skin: StandardSkin,
    center: tuple[float, float],
    diameter: int,
    color: tuple[int, int, int],
    alpha: float,
    number: str | None,
) -> None:
    frame_diameter = max(1, round(diameter * _frame_scale()))
    hitcircle = _tint_sprite(skin.hitcircle, color, alpha, frame_diameter)
    overlay = _resize_with_alpha(skin.hitcircle_overlay, frame_diameter, alpha)
    position = (round(center[0] - frame_diameter / 2), round(center[1] - frame_diameter / 2))
    frame.alpha_composite(hitcircle, position)
    frame.alpha_composite(overlay, position)
    if number is not None:
        _draw_number(frame, skin, number, center, frame_diameter, alpha)


def _frame_scale() -> float:
    return _build_frame_layout().scale


def _draw_number(
    frame: Image.Image,
    skin: StandardSkin,
    number: str,
    center: tuple[float, float],
    circle_diameter: int,
    alpha: float,
) -> None:
    digit_height = max(1, round(circle_diameter * 0.52))
    digit_images = [_resize_digit(skin.digits[digit], digit_height, alpha) for digit in number]
    overlap = round(skin.hitcircle_overlap * digit_height / 100)
    total_width = sum(image.width for image in digit_images) - overlap * (len(digit_images) - 1)
    x = round(center[0] - total_width / 2)
    y = round(center[1] - digit_height / 2)

    for digit_image in digit_images:
        frame.alpha_composite(digit_image, (x, y))
        x += digit_image.width - overlap


def _resize_digit(sprite: Image.Image, height: int, alpha: float) -> Image.Image:
    box = sprite.getbbox()
    cropped = sprite.crop(box)
    width = max(1, round(cropped.width * height / cropped.height))
    return _resize_with_alpha(cropped, (width, height), alpha)


def _draw_slider_body(
    frame: Image.Image,
    points: list[tuple[float, float]],
    width: int,
    border_width: int,
    border_color: tuple[int, int, int],
    track_color: tuple[int, int, int],
    alpha: float,
) -> None:
    if len(points) < 2:
        return

    scale = SLIDER_BODY_SUPERSAMPLE
    layer = Image.new("RGBA", (frame.width * scale, frame.height * scale), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    scaled_points = [(x * scale, y * scale) for x, y in points]
    shadow_width = max(1, width + border_width)
    accent_width = max(1, round(width * (1 - SLIDER_LEGACY_BORDER_PORTION)))
    middle_width = max(1, round(accent_width * 0.72))
    inner_width = max(1, round(accent_width * 0.44))
    outer_track = _darken(track_color, 0.1)
    inner_track = _legacy_lighten(track_color, 0.5)
    middle_track = _mix_rgb(outer_track, inner_track, 0.5)

    _draw_round_path(draw, scaled_points, shadow_width * scale, (0, 0, 0, round(255 * alpha * SLIDER_LEGACY_SHADOW_ALPHA)))
    _draw_round_path(draw, scaled_points, width * scale, (*border_color, round(255 * alpha)))
    _draw_round_path(draw, scaled_points, accent_width * scale, (*outer_track, round(255 * alpha * SLIDER_LEGACY_TRACK_ALPHA)))
    _draw_round_path(draw, scaled_points, middle_width * scale, (*middle_track, round(255 * alpha * SLIDER_LEGACY_TRACK_ALPHA)))
    _draw_round_path(draw, scaled_points, inner_width * scale, (*inner_track, round(255 * alpha * SLIDER_LEGACY_TRACK_ALPHA)))
    layer = layer.resize(frame.size, Image.Resampling.LANCZOS)
    frame.alpha_composite(layer)


def _draw_round_path(
    draw: ImageDraw.ImageDraw,
    points: list[tuple[float, float]],
    width: int,
    color: tuple[int, int, int, int],
) -> None:
    draw.line(points, fill=color, width=width, joint="curve")
    radius = width / 2
    for x, y in points:
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)


def _darken(color: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    return tuple(round(channel * (1 - amount)) for channel in color)


def _legacy_lighten(color: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    amount *= 0.5
    return tuple(min(255, round(channel * (1 + 0.5 * amount) + 255 * amount)) for channel in color)


def _mix_rgb(
    first: tuple[int, int, int],
    second: tuple[int, int, int],
    amount: float,
) -> tuple[int, int, int]:
    return tuple(round(first[index] * (1 - amount) + second[index] * amount) for index in range(3))


def _draw_slider_reverse_arrows(
    frame: Image.Image,
    skin: StandardSkin,
    path: list[tuple[float, float]],
    repeats: int,
    settings: RenderSettings,
    frame_layout: FrameLayout,
    alpha: float,
) -> None:
    if repeats <= 1:
        return

    arrow_size = max(1, round(settings.circle_diameter * 0.78 * frame_layout.scale))
    arrow = _resize_with_alpha(skin.reverse_arrow, arrow_size, alpha)
    for repeat_index in range(1, repeats):
        point = path[-1] if repeat_index % 2 == 1 else path[0]
        center = _to_frame_point(*point, frame_layout)
        frame.alpha_composite(arrow, (round(center[0] - arrow.width / 2), round(center[1] - arrow.height / 2)))


def _tint_sprite(
    sprite: Image.Image,
    color: tuple[int, int, int],
    alpha: float,
    size: int | tuple[int, int],
) -> Image.Image:
    resized = _resize_with_alpha(sprite, size, alpha)
    mask = resized.getchannel("A")
    tinted = Image.new("RGBA", resized.size, (*color, 0))
    tinted.putalpha(mask)
    return tinted


def _resize_with_alpha(
    sprite: Image.Image,
    size: int | tuple[int, int],
    alpha: float,
) -> Image.Image:
    if isinstance(size, int):
        target_size = (size, size)
    else:
        target_size = size
    resized = sprite.resize(target_size, Image.Resampling.LANCZOS)
    if alpha < 1:
        alpha_channel = resized.getchannel("A").point(lambda value: round(value * alpha))
        resized.putalpha(alpha_channel)
    return resized


def _to_frame_point(
    x: float,
    y: float,
    frame_layout: FrameLayout,
) -> tuple[float, float]:
    return (
        frame_layout.playfield_left + x * frame_layout.scale,
        frame_layout.playfield_top + y * frame_layout.scale,
    )


def _draw_time_label(
    draw: ImageDraw.ImageDraw,
    label: str,
    x: int,
    y: int,
    font: ImageFont.ImageFont,
    note_font: ImageFont.ImageFont,
    note: str | None,
    label_color: tuple[int, int, int, int],
    note_color: tuple[int, int, int, int],
) -> None:
    _draw_centered_text(draw, label, x, y, font, label_color)
    if note is not None:
        text_box = draw.textbbox((0, 0), label, font=font)
        note_y = y + (text_box[3] - text_box[1]) + TIME_LABEL_NOTE_TOP_GAP
        _draw_centered_text(draw, note, x, note_y, note_font, note_color)


def _draw_centered_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: int,
    y: int,
    font: ImageFont.ImageFont,
    color: tuple[int, int, int, int],
) -> None:
    text_box = draw.textbbox((0, 0), text, font=font)
    text_width = text_box[2] - text_box[0]
    text_x = x + (IMAGE_WIDTH - text_width) / 2
    draw.text((text_x, y), text, fill=color, font=font)


def _build_time_label_note(row_timing: RowTiming) -> str | None:
    if not row_timing.is_preview:
        return None
    return "Preview Time"


def _current_break_period(
    break_periods: tuple[BreakPeriod, ...],
    snapshot_time: int,
) -> BreakPeriod | None:
    for period in break_periods:
        if _break_overlay_alpha(period, snapshot_time) > 0:
            return period
    return None


def _draw_break_overlay(
    frame: Image.Image,
    break_period: BreakPeriod,
    snapshot_time: int,
) -> None:
    """Draw the osu! break overlay shape: centre countdown and remaining-time bar."""
    alpha = _break_overlay_alpha(break_period, snapshot_time)
    if alpha <= 0:
        return

    layer = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    center_x = IMAGE_WIDTH / 2
    center_y = IMAGE_HEIGHT / 2
    counter_font = ImageFont.load_default(size=BREAK_OVERLAY_COUNTER_FONT_SIZE)
    info_font = ImageFont.load_default(size=BREAK_OVERLAY_INFO_FONT_SIZE)

    _draw_break_arrows(draw, alpha)
    _draw_break_remaining_bar(draw, break_period, snapshot_time, center_x, center_y, alpha)

    remaining_seconds = max(0, (break_period.end_time - snapshot_time + 999) // 1000)
    counter_label = str(remaining_seconds)
    counter_box = draw.textbbox((0, 0), counter_label, font=counter_font)
    counter_y = center_y - 15 - (counter_box[3] - counter_box[1])
    _draw_centered_text(draw, counter_label, 0, counter_y, counter_font, _with_alpha(BREAK_OVERLAY_COLOR, alpha))

    break_label = f"Break {_format_time(break_period.start_time)} - {_format_time(break_period.end_time)}"
    info_y = center_y + BREAK_OVERLAY_INFO_TOP_GAP
    _draw_centered_text(draw, break_label, 0, info_y, info_font, _with_alpha(BREAK_OVERLAY_INFO_COLOR, alpha))
    frame.alpha_composite(layer)


def _draw_break_remaining_bar(
    draw: ImageDraw.ImageDraw,
    break_period: BreakPeriod,
    snapshot_time: int,
    center_x: float,
    center_y: float,
    alpha: float,
) -> None:
    track_width = round(IMAGE_WIDTH * BREAK_OVERLAY_BAR_WIDTH_RATIO)
    track_height = BREAK_OVERLAY_BAR_HEIGHT
    track_left = center_x - track_width / 2
    track_top = center_y - track_height / 2
    track_bounds = (track_left, track_top, track_left + track_width, track_top + track_height)
    draw.rounded_rectangle(track_bounds, radius=track_height / 2, fill=(48, 48, 48, round(150 * alpha)))

    remaining_ratio = _break_remaining_bar_ratio(break_period, snapshot_time)
    fill_width = track_width * remaining_ratio
    fill_left = center_x - fill_width / 2
    fill_bounds = (fill_left, track_top, fill_left + fill_width, track_top + track_height)
    draw.rounded_rectangle(fill_bounds, radius=track_height / 2, fill=(238, 238, 238, round(230 * alpha)))


def _draw_break_arrows(draw: ImageDraw.ImageDraw, alpha: float) -> None:
    color = (238, 238, 238, round(80 * alpha))
    glow_color = (238, 238, 238, round(35 * alpha))
    center_y = IMAGE_HEIGHT / 2
    for offset, direction in ((-0.22, 1), (0.22, -1)):
        center_x = IMAGE_WIDTH / 2 + IMAGE_WIDTH * offset
        _draw_chevron(draw, center_x, center_y, 32, direction, glow_color, 9)
        _draw_chevron(draw, center_x, center_y, 20, direction, color, 4)


def _draw_chevron(
    draw: ImageDraw.ImageDraw,
    center_x: float,
    center_y: float,
    size: int,
    direction: int,
    color: tuple[int, int, int, int],
    width: int,
) -> None:
    half = size / 2
    point = (center_x + direction * half, center_y)
    top = (center_x - direction * half, center_y - half)
    bottom = (center_x - direction * half, center_y + half)
    draw.line((top, point, bottom), fill=color, width=width, joint="curve")


def _break_overlay_alpha(break_period: BreakPeriod, snapshot_time: int) -> float:
    if break_period.end_time - break_period.start_time < BREAK_MIN_DURATION_MS:
        return 0.0
    if snapshot_time < break_period.start_time or snapshot_time > break_period.end_time:
        return 0.0

    if snapshot_time < break_period.start_time + BREAK_FADE_DURATION_MS:
        return (snapshot_time - break_period.start_time) / BREAK_FADE_DURATION_MS
    if snapshot_time > break_period.end_time - BREAK_FADE_DURATION_MS:
        return (break_period.end_time - snapshot_time) / BREAK_FADE_DURATION_MS
    return 1.0


def _break_remaining_bar_ratio(break_period: BreakPeriod, snapshot_time: int) -> float:
    effective_duration = break_period.end_time - BREAK_FADE_DURATION_MS - break_period.start_time
    if effective_duration <= 0:
        return 0.0

    remaining = break_period.end_time - BREAK_FADE_DURATION_MS - snapshot_time
    return max(0.0, min(1.0, remaining / effective_duration))


def _with_alpha(color: tuple[int, int, int, int], alpha: float) -> tuple[int, int, int, int]:
    return (color[0], color[1], color[2], round(color[3] * alpha))


def _format_time(time_ms: int) -> str:
    minutes = time_ms // 60000
    seconds = (time_ms % 60000) // 1000
    milliseconds = time_ms % 1000
    return f"{minutes:02d}:{seconds:02d}:{milliseconds:03d}"


def _is_slider(hit_object: StandardHitObject) -> bool:
    return bool(hit_object.hit_type & 2)


def _is_spinner(hit_object: StandardHitObject) -> bool:
    return bool(hit_object.hit_type & 8)
