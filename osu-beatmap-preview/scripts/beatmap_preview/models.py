from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TimingPoint:
    time: float
    beat_length: float
    meter: int
    uninherited: bool


@dataclass(frozen=True)
class StandardHitObject:
    x: int
    y: int
    start_time: int
    end_time: int
    hit_type: int


@dataclass(frozen=True)
class TaikoHitObject:
    start_time: int
    end_time: int
    hit_type: int
    hitsound: int


@dataclass(frozen=True)
class CatchHitObject:
    x: int
    start_time: int
    end_time: int
    hit_type: int


@dataclass(frozen=True)
class ManiaHitObject:
    lane: int
    start_time: int
    end_time: int
    is_long_note: bool


HitObject = StandardHitObject | TaikoHitObject | CatchHitObject | ManiaHitObject


@dataclass(frozen=True)
class Beatmap:
    metadata: dict[str, str]
    difficulty: dict[str, str]
    general: dict[str, str]
    timing_points: list[TimingPoint]
    hit_objects: list[HitObject]

    @property
    def mode(self) -> int:
        return int(self.general["Mode"])

    @property
    def title(self) -> str:
        if "TitleUnicode" in self.metadata and self.metadata["TitleUnicode"]:
            return self.metadata["TitleUnicode"]
        return self.metadata["Title"]

    @property
    def version(self) -> str:
        return self.metadata["Version"]
