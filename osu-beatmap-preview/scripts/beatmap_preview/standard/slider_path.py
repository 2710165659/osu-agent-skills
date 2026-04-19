from __future__ import annotations

import math

from ..errors import PreviewError
from ..models import StandardHitObject


def build_slider_path(hit_object: StandardHitObject) -> list[tuple[float, float]]:
    """Approximate a standard-mode slider path in osu! playfield coordinates."""
    if hit_object.slider_type is None:
        raise PreviewError("slider is missing path type")

    points = [(float(hit_object.x), float(hit_object.y))]
    points.extend((float(x), float(y)) for x, y in hit_object.slider_points)

    if hit_object.slider_type == "L":
        path = points
    elif hit_object.slider_type == "P":
        path = _approximate_perfect_curve(points)
    elif hit_object.slider_type == "C":
        path = _approximate_catmull(points)
    else:
        path = _approximate_bezier_segments(points)

    return _fit_path_to_length(path, hit_object.slider_pixel_length)


def path_position_at(path: list[tuple[float, float]], progress: float) -> tuple[float, float]:
    """Return the point at progress [0, 1] along an already approximated path."""
    if len(path) < 2:
        return path[0]

    target = _path_length(path) * max(0.0, min(1.0, progress))
    travelled = 0.0
    for index in range(1, len(path)):
        previous = path[index - 1]
        current = path[index]
        segment_length = math.dist(previous, current)
        if segment_length == 0:
            continue
        if travelled + segment_length >= target:
            ratio = (target - travelled) / segment_length
            return (
                previous[0] + (current[0] - previous[0]) * ratio,
                previous[1] + (current[1] - previous[1]) * ratio,
            )
        travelled += segment_length

    return path[-1]


def slice_path(
    path: list[tuple[float, float]],
    start_progress: float,
    end_progress: float,
) -> list[tuple[float, float]]:
    """Return the path section between two progress values in [0, 1]."""
    if len(path) < 2:
        return path
    if start_progress > end_progress:
        start_progress, end_progress = end_progress, start_progress

    start_progress = max(0.0, min(1.0, start_progress))
    end_progress = max(0.0, min(1.0, end_progress))
    start_distance = _path_length(path) * start_progress
    end_distance = _path_length(path) * end_progress
    sliced = [path_position_at(path, start_progress)]
    travelled = 0.0

    for index in range(1, len(path)):
        current_distance = travelled + math.dist(path[index - 1], path[index])
        if start_distance < current_distance < end_distance:
            sliced.append(path[index])
        travelled = current_distance

    sliced.append(path_position_at(path, end_progress))
    return _dedupe_points(sliced)


def _path_length(path: list[tuple[float, float]]) -> float:
    return sum(math.dist(path[index - 1], path[index]) for index in range(1, len(path)))


def _approximate_bezier_segments(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    path: list[tuple[float, float]] = []
    segment = [points[0]]

    for point in points[1:]:
        segment.append(point)
        if len(segment) > 2 and point == segment[-2]:
            segment.pop()
            path.extend(_approximate_bezier(segment))
            segment = [point]

    if len(segment) > 1:
        path.extend(_approximate_bezier(segment))
    return _dedupe_points(path)


def _approximate_bezier(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    steps = max(64, len(points) * 24)
    return [_bezier_at(points, index / steps) for index in range(steps + 1)]


def _bezier_at(points: list[tuple[float, float]], t: float) -> tuple[float, float]:
    working = points[:]
    while len(working) > 1:
        working = [
            (
                working[index][0] * (1 - t) + working[index + 1][0] * t,
                working[index][1] * (1 - t) + working[index + 1][1] * t,
            )
            for index in range(len(working) - 1)
        ]
    return working[0]


def _approximate_perfect_curve(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    if len(points) != 3 or _are_collinear(points[0], points[1], points[2]):
        return _approximate_bezier_segments(points)

    centre = _circle_centre(points[0], points[1], points[2])
    radius = math.dist(centre, points[0])
    start_angle = math.atan2(points[0][1] - centre[1], points[0][0] - centre[0])
    middle_angle = math.atan2(points[1][1] - centre[1], points[1][0] - centre[0])
    end_angle = math.atan2(points[2][1] - centre[1], points[2][0] - centre[0])
    end_angle = _normalise_arc_end(start_angle, middle_angle, end_angle)
    steps = max(64, round(abs(end_angle - start_angle) * radius / 4))
    return [
        (
            centre[0] + math.cos(start_angle + (end_angle - start_angle) * index / steps) * radius,
            centre[1] + math.sin(start_angle + (end_angle - start_angle) * index / steps) * radius,
        )
        for index in range(steps + 1)
    ]


def _circle_centre(
    first: tuple[float, float],
    second: tuple[float, float],
    third: tuple[float, float],
) -> tuple[float, float]:
    ax, ay = first
    bx, by = second
    cx, cy = third
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
    return ux, uy


def _normalise_arc_end(start: float, middle: float, end: float) -> float:
    while end < start:
        end += math.tau
    middle_forward = middle
    while middle_forward < start:
        middle_forward += math.tau
    if middle_forward <= end:
        return end

    while end > start:
        end -= math.tau
    return end


def _approximate_catmull(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    if len(points) < 2:
        return points

    path: list[tuple[float, float]] = []
    extended = [points[0], *points, points[-1]]
    for index in range(1, len(extended) - 2):
        p0, p1, p2, p3 = extended[index - 1], extended[index], extended[index + 1], extended[index + 2]
        for step in range(48):
            path.append(_catmull_at(p0, p1, p2, p3, step / 48))
    path.append(points[-1])
    return _dedupe_points(path)


def _catmull_at(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
    t: float,
) -> tuple[float, float]:
    t2 = t * t
    t3 = t2 * t
    x = 0.5 * (
        (2 * p1[0])
        + (-p0[0] + p2[0]) * t
        + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
        + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3
    )
    y = 0.5 * (
        (2 * p1[1])
        + (-p0[1] + p2[1]) * t
        + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
        + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3
    )
    return x, y


def _fit_path_to_length(
    path: list[tuple[float, float]],
    expected_length: float,
) -> list[tuple[float, float]]:
    if len(path) < 2 or expected_length <= 0:
        return path

    fitted = [path[0]]
    travelled = 0.0
    for index in range(1, len(path)):
        previous = path[index - 1]
        current = path[index]
        segment_length = math.dist(previous, current)
        if segment_length == 0:
            continue
        if travelled + segment_length >= expected_length:
            ratio = (expected_length - travelled) / segment_length
            fitted.append((previous[0] + (current[0] - previous[0]) * ratio, previous[1] + (current[1] - previous[1]) * ratio))
            return fitted
        fitted.append(current)
        travelled += segment_length

    previous = fitted[-2]
    current = fitted[-1]
    segment_length = math.dist(previous, current)
    if segment_length > 0 and travelled < expected_length:
        extra = (expected_length - travelled) / segment_length
        fitted[-1] = (current[0] + (current[0] - previous[0]) * extra, current[1] + (current[1] - previous[1]) * extra)
    return fitted


def _dedupe_points(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    deduped: list[tuple[float, float]] = []
    for point in points:
        if not deduped or point != deduped[-1]:
            deduped.append(point)
    return deduped


def _are_collinear(
    first: tuple[float, float],
    second: tuple[float, float],
    third: tuple[float, float],
) -> bool:
    return abs((second[1] - first[1]) * (third[0] - first[0]) - (second[0] - first[0]) * (third[1] - first[1])) < 0.001
