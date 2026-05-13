from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ModId(Enum):
    EZ = "EZ"
    HT = "HT"
    HR = "HR"
    DT = "DT"
    FL = "FL"
    HD = "HD"
    DA = "DA"


@dataclass
class ModSettings:
    speed_multiplier: float = 1.0
    cs: float | None = None
    ar: float | None = None
    od: float | None = None
    hp: float | None = None
    hard_rock: bool = False
    easy: bool = False
    hidden: bool = False
    flashlight: bool = False


def parse_mods(mod_str: str) -> ModSettings:
    """Parse mod string like 'DT1.5x+HR+DAcs=5ar=9' into ModSettings. (stub)"""
    raise NotImplementedError("mod support not yet implemented")


def mods_for_mode(settings: ModSettings, mode: int) -> ModSettings:
    """Filter out mods not supported by the given game mode. (stub)"""
    raise NotImplementedError("mod support not yet implemented")
