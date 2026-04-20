from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from ..errors import PreviewError

TAIKO_ASSET_DIR = Path(__file__).resolve().parents[3] / "assets" / "taiko"


@dataclass(frozen=True)
class TaikoSkin:
    bar_left: Image.Image
    bar_right: Image.Image
    bar_line: Image.Image
    hit_circle: Image.Image
    hit_circle_overlay: Image.Image
    big_hit_circle: Image.Image
    big_hit_circle_overlay: Image.Image
    roll_middle: Image.Image
    roll_end: Image.Image


def load_taiko_skin() -> TaikoSkin:
    """加载 taiko 预览渲染用到的皮肤素材。"""
    required_assets = {
        "bar_left": "taiko-bar-left@2x.png",
        "bar_right": "taiko-bar-right@2x.png",
        "bar_line": "taiko-barline@2x.png",
        "hit_circle": "taikohitcircle@2x.png",
        "hit_circle_overlay": "taikohitcircleoverlay-0@2x.png",
        "big_hit_circle": "taikobigcircle@2x.png",
        "big_hit_circle_overlay": "taikobigcircleoverlay-0@2x.png",
        "roll_middle": "taiko-roll-middle@2x.png",
        "roll_end": "taiko-roll-end@2x.png",
    }
    images: dict[str, Image.Image] = {}
    for key, filename in required_assets.items():
        asset_path = TAIKO_ASSET_DIR / filename
        if not asset_path.exists():
            raise PreviewError(f"missing taiko skin asset: {asset_path}")
        image = Image.open(asset_path).convert("RGBA")
        if key in {"roll_middle", "roll_end"}:
            # roll 素材本身带了顶部透明留白，直接缩放会导致身体和半圆尾上下对不齐。
            # 先按 alpha 可见区域裁掉透明边界，再参与后续缩放。
            image = image.crop(image.getchannel("A").getbbox())
        images[key] = image

    return TaikoSkin(**images)
