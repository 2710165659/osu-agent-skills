from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.beatmap_preview.errors import PreviewError
from scripts.beatmap_preview.service import generate_preview


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download an osu! beatmap and render a preview image."
    )
    parser.add_argument("--bid", required=True, help="osu! beatmap id")
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    try:
        result = generate_preview(args.bid, Path(__file__).resolve().parents[1])
    except PreviewError as exc:
        payload = json.dumps(
            {
                "status": "error",
                "msg": str(exc),
                "preview-img": "",
                "beatmap-info": {},
            },
            ensure_ascii=False,
            indent=4,
        )
        sys.stdout.buffer.write((payload + "\n").encode("utf-8"))
        return 1

    payload = json.dumps(result, ensure_ascii=False, indent=4)
    sys.stdout.buffer.write((payload + "\n").encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

