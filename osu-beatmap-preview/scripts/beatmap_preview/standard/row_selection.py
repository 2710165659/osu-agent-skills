from __future__ import annotations

import random
from dataclasses import dataclass

from ..errors import PreviewError
from ..models import Beatmap, BreakPeriod, StandardHitObject


@dataclass(frozen=True)
class RowTiming:
    start_time: int
    is_preview: bool
    break_periods: tuple[BreakPeriod, ...]


def choose_row_start_times(
    beatmap: Beatmap,
    hit_objects: list[StandardHitObject],
    row_count: int,
    images_per_row: int,
    ms_per_row_duration: int,
    break_gap_ms: int,
) -> list[RowTiming]:
    """选择预览行时间段：随机行避开 break，同时保留 PreviewTime 行。"""
    row_duration = (images_per_row - 1) * ms_per_row_duration
    valid_intervals = _build_valid_row_start_intervals(hit_objects, beatmap.break_periods, row_duration, break_gap_ms)
    if not valid_intervals:
        raise PreviewError("not enough playable time to render standard preview rows")

    preview_time = int(beatmap.general["PreviewTime"])
    if preview_time < 0:
        preview_time = hit_objects[0].start_time

    chosen = [preview_time]
    random_source = random.Random()
    attempts = 0
    # 先随机抽样，避免每次都集中在谱面开头或密集段。
    while len(chosen) < row_count and attempts < 3000:
        attempts += 1
        candidate = _random_start_from_intervals(valid_intervals, random_source)
        if _does_not_overlap_existing(candidate, row_duration, chosen):
            chosen.append(candidate)

    if len(chosen) < row_count:
        # 随机不足时退回到物件起点，保证短谱也尽量能生成完整网格。
        for candidate in _fallback_start_candidates(valid_intervals, hit_objects):
            if _does_not_overlap_existing(candidate, row_duration, chosen):
                chosen.append(candidate)
            if len(chosen) == row_count:
                break

    if len(chosen) < row_count:
        raise PreviewError("could not find enough non-overlapping standard preview rows")

    return [
        RowTiming(
            start_time=start_time,
            is_preview=start_time == preview_time,
            break_periods=tuple(_break_periods_overlapping_row(beatmap.break_periods, start_time, row_duration)),
        )
        for start_time in sorted(chosen)
    ]


def _build_valid_row_start_intervals(
    hit_objects: list[StandardHitObject],
    break_periods: list[BreakPeriod],
    row_duration: int,
    break_gap_ms: int,
) -> list[tuple[int, int]]:
    chart_start = hit_objects[0].start_time
    chart_end = max(hit_object.end_time for hit_object in hit_objects)
    # 明确声明的 break 和根据长空白推断出的 break 都不作为随机预览行候选。
    forbidden = _merge_periods([*break_periods, *_infer_break_periods(hit_objects, break_gap_ms)])
    playable_segments = _subtract_periods(chart_start, chart_end, forbidden)
    intervals = []

    for start, end in playable_segments:
        latest_start = end - row_duration
        if latest_start >= start:
            intervals.append((start, latest_start))

    return intervals


def _infer_break_periods(hit_objects: list[StandardHitObject], break_gap_ms: int) -> list[BreakPeriod]:
    periods: list[BreakPeriod] = []
    previous_end = hit_objects[0].end_time
    for hit_object in hit_objects[1:]:
        if hit_object.start_time - previous_end >= break_gap_ms:
            periods.append(BreakPeriod(start_time=previous_end, end_time=hit_object.start_time))
        previous_end = max(previous_end, hit_object.end_time)
    return periods


def _merge_periods(periods: list[BreakPeriod]) -> list[BreakPeriod]:
    ordered = sorted(periods, key=lambda period: (period.start_time, period.end_time))
    merged: list[BreakPeriod] = []
    for period in ordered:
        if not merged or period.start_time > merged[-1].end_time:
            merged.append(period)
            continue

        previous = merged[-1]
        merged[-1] = BreakPeriod(previous.start_time, max(previous.end_time, period.end_time))
    return merged


def _subtract_periods(
    start_time: int,
    end_time: int,
    forbidden_periods: list[BreakPeriod],
) -> list[tuple[int, int]]:
    segments: list[tuple[int, int]] = []
    cursor = start_time

    # 用游标从左到右扣掉 forbidden period，得到剩余可播放区间。
    for period in forbidden_periods:
        if period.end_time <= cursor:
            continue
        if period.start_time > cursor:
            segments.append((cursor, min(period.start_time, end_time)))
        cursor = max(cursor, period.end_time)
        if cursor >= end_time:
            break

    if cursor < end_time:
        segments.append((cursor, end_time))
    return [(start, end) for start, end in segments if end > start]


def _nearest_valid_start(time: int, intervals: list[tuple[int, int]]) -> int:
    if any(start <= time <= end for start, end in intervals):
        return time

    # fallback 候选若落在 break 内，就吸附到最近的合法区间边界。
    return min(
        (start if time < start else end for start, end in intervals),
        key=lambda candidate: abs(candidate - time),
    )


def _random_start_from_intervals(
    intervals: list[tuple[int, int]],
    random_source: random.Random,
) -> int:
    total = sum(end - start + 1 for start, end in intervals)
    pick = random_source.randrange(total)
    for start, end in intervals:
        length = end - start + 1
        if pick < length:
            return start + pick
        pick -= length
    return intervals[-1][1]


def _does_not_overlap_existing(candidate: int, row_duration: int, chosen: list[int]) -> bool:
    candidate_end = candidate + row_duration
    for existing in chosen:
        existing_end = existing + row_duration
        if candidate < existing_end and candidate_end > existing:
            return False
    return True


def _fallback_start_candidates(
    intervals: list[tuple[int, int]],
    hit_objects: list[StandardHitObject],
) -> list[int]:
    candidates = [_nearest_valid_start(hit_object.start_time, intervals) for hit_object in hit_objects]
    return sorted(set(candidates))


def _break_periods_overlapping_row(
    break_periods: list[BreakPeriod],
    row_start_time: int,
    row_duration: int,
) -> list[BreakPeriod]:
    row_end_time = row_start_time + row_duration
    return [
        period
        for period in break_periods
        if period.start_time < row_end_time and period.end_time > row_start_time
    ]
