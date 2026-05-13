# osu! Beatmap Preview

Generate osu! beatmap preview images from beatmap IDs. Supports all four osu! game modes.

## Quick Start

```bash
# Default: PNG format
python scripts/run.py --bid=4903207

# GIF format (standard only)
python scripts/run.py --bid=4903207 --format=gif

# Shorthand
python scripts/run.py --bid=4903207 --fmt=png
```

## Arguments

| Argument | Required | Default | Description |
|---|---|---|---|
| `--bid` | yes | — | osu! beatmap id (numeric only) |
| `--format`, `--fmt` | no | `png` | output format: `png` or `gif` |

> **Note:** `--format` only takes effect for osu!standard (mode 0). taiko, catch, and mania always output PNG.

## Mode Support

| Mode | PNG | GIF |
|---|---|---|
| osu!standard (0) | 5×8 grid | 2×2 animated, 5s loop |
| osu!taiko (1) | horizontal rows | — |
| osu!catch (2) | vertical columns | — |
| osu!mania (3) | vertical columns | — |

## Validate Environment

```bash
python scripts/validate.py
```

Checks imports, temp directory access, network connectivity, and a full render test (bid 2116202).

## Output

JSON to stdout with structure:

```json
{
    "status": "success",
    "msg": "preview generated successfully for bid 4903207",
    "preview-img": "/tmp/osu-beatmap-preview/outputs/4903207.png",
    "beatmap-info": {
        "meta-data": { "title": "...", "artist": "...", ... },
        "difficulty": { "circle-size": "3.5", "approach-rate": "9", ... }
    }
}
```

## Architecture

```
scripts/
├── run.py                     # CLI entry point
├── validate.py                # Environment validation
└── beatmap_preview/
    ├── service.py             # Orchestrator: download → parse → render
    ├── downloader.py          # Beatmap file download from osu.ppy.sh
    ├── parser.py              # .osu file parser (all 4 modes)
    ├── models.py              # Data models (Beatmap, HitObjects, etc.)
    ├── errors.py              # PreviewError
    ├── composer.py            # Shared GIF/PNG frame assembly
    ├── mods.py                # Mod system (stub)
    ├── convert.py             # Cross-mode convert (stub)
    ├── standard/              # osu!standard renderer
    │   ├── renderer.py        #   Frame rendering + grid/GIF assembly
    │   ├── config.py          #   Layout/presentation constants
    │   ├── skin.py            #   Skin asset loader
    │   └── slider_path.py     #   Slider path math (Bezier, Catmull, etc.)
    ├── taiko/                 # osu!taiko renderer
    │   ├── renderer.py        #   Row-based chart rendering
    │   ├── config.py          #   Layout/color constants
    │   ├── skin.py            #   Skin asset loader
    │   └── timing.py          #   Scroll position mapper, timing lines
    ├── catch/                 # osu!catch renderer
    │   ├── renderer.py        #   Column-based chart rendering
    │   ├── config.py          #   Layout/color constants
    │   ├── skin.py            #   Skin asset loader
    │   └── objects.py         #   Object processor (fruits, hyper dash, etc.)
    └── mania/                 # osu!mania renderer
        ├── renderer.py        #   Column-based chart rendering
        └── config.py          #   Layout/color constants
```
