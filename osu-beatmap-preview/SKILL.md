---
name: osu-beatmap-preview
description: Generate an osu! beatmap preview image and JSON result from a beatmap id. Use this skill when a task involves osu!, beatmap preview, chart preview, standard preview, taiko preview, catch preview, mania preview, preview image generation, beatmap metadata output, or running `python scripts/run.py --bid="..."` to inspect a map and return structured success or error results.
---

# osu! Beatmap Preview

Prefer absolute paths for command paths when running from automation or another working directory. The examples below use relative paths from the skill root.

Run the skill from the skill root:

```bash
python scripts/run.py --bid="5199917"
```

Validate the environment and core preview workflow from the skill root:

```bash
python scripts/validate.py
```

`validate.py` checks required imports, temp-directory read/write access, network access to the osu! beatmap download endpoint, and a render test for beatmap `2116202`. It prints a summary and exits with code `0` on success or `1` on failure.

Use this skill when you need:

- An osu! beatmap preview image by beatmap id
- Support for osu!standard, osu!taiko, osu!catch, or osu!mania preview workflows
- JSON output for success or failure
- Beatmap metadata and difficulty fields in the response
- A quick CLI workflow for osu! preview tasks
- Explicit error output for invalid ids or unsupported preview cases

Return JSON with hyphen-case keys:

- Use `status: success` when the preview is generated.
- Use `status: error` when download, parsing, or rendering fails.
- Keep `preview-img` empty on errors.
- Keep `beatmap-info.meta-data` as the full `[Metadata]` section.
- Keep `beatmap-info.difficulty` as the full `[Difficulty]` section.

Mode support:

- The skill is designed for all four osu! game modes.

Render only the chart preview. Do not add titles, metadata text, headers, or other decorations into the image.
