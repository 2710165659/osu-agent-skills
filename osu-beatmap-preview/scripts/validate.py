import os
import sys

TEST_BID = "2116202"
SCRIPT_ROOT = os.path.dirname(os.path.abspath(__file__))

if SCRIPT_ROOT not in sys.path:
    sys.path.insert(0, SCRIPT_ROOT)


class ValidationResult:
    def __init__(self, name, ok, message):
        self.name = name
        self.ok = ok
        self.message = message


def get_skill_root():
    from pathlib import Path

    return Path(SCRIPT_ROOT).parent


def get_temp_root():
    import tempfile
    from pathlib import Path

    return Path(tempfile.gettempdir()) / "osu-beatmap-preview"


def validate_required_imports():
    modules = (
        "PIL",
        "PIL.Image",
        "beatmap_preview.service",
        "beatmap_preview.parser",
        "beatmap_preview.downloader",
    )

    try:
        for module_name in modules:
            __import__(module_name)
    except Exception as exc:
        return ValidationResult(
            name="Required imports",
            ok=False,
            message=f"failed to import {module_name}: {exc}",
        )

    return ValidationResult(
        name="Required imports",
        ok=True,
        message="Pillow and beatmap_preview modules import successfully.",
    )


def validate_temp_read_write():
    try:
        import uuid

        temp_root = get_temp_root()
        temp_dir = temp_root / "validate"
        temp_file = temp_dir / f"{uuid.uuid4().hex}.txt"
        content = "osu-beatmap-preview validate"

        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_file.write_text(content, encoding="utf-8")
        if temp_file.read_text(encoding="utf-8") != content:
            return ValidationResult(
                name="Temp read/write",
                ok=False,
                message=f"{temp_file} did not read back the same content that was written.",
            )
        temp_file.unlink()
    except OSError as exc:
        return ValidationResult(
            name="Temp read/write",
            ok=False,
            message=f"could not read/write under {temp_dir}: {exc}",
        )
    except Exception as exc:
        return ValidationResult(
            name="Temp read/write",
            ok=False,
            message=f"could not validate temp read/write: {exc}",
        )

    return ValidationResult(
        name="Temp read/write",
        ok=True,
        message=f"{temp_root} can create, write, read, and clean up files.",
    )


def validate_network():
    try:
        from urllib.error import HTTPError, URLError
        from urllib.request import Request, urlopen
    except Exception as exc:
        return ValidationResult(
            name="Network access",
            ok=False,
            message=f"could not import network dependencies: {exc}",
        )

    try:
        request = Request(
            url=f"https://osu.ppy.sh/osu/{TEST_BID}",
            headers={"User-Agent": "osu-beatmap-preview/validate"},
        )

        with urlopen(request, timeout=20) as response:
            response.read(1)
    except HTTPError as exc:
        return ValidationResult(
            name="Network access",
            ok=False,
            message=f"osu! download endpoint returned HTTP {exc.code}.",
        )
    except URLError as exc:
        return ValidationResult(
            name="Network access",
            ok=False,
            message=f"could not reach the osu! download endpoint: {exc.reason}",
        )
    except TimeoutError:
        return ValidationResult(
            name="Network access",
            ok=False,
            message="timed out while connecting to the osu! download endpoint.",
        )
    except Exception as exc:
        return ValidationResult(
            name="Network access",
            ok=False,
            message=f"could not validate network access: {exc}",
        )

    return ValidationResult(
        name="Network access",
        ok=True,
        message="osu! beatmap download endpoint is reachable.",
    )


def validate_render_preview():
    try:
        from pathlib import Path

        from PIL import Image

        from beatmap_preview.errors import PreviewError
        from beatmap_preview.service import generate_preview
    except Exception as exc:
        return ValidationResult(
            name="Preview render",
            ok=False,
            message=f"could not import preview render dependencies: {exc}",
        )

    temp_root = get_temp_root()
    preview_path = temp_root / "outputs" / f"{TEST_BID}.png"
    beatmap_path = temp_root / "osu-download-cache" / f"{TEST_BID}.osu"
    cleanup_render_preview_outputs(preview_path, beatmap_path)

    try:
        result = generate_preview(TEST_BID, get_skill_root())
        preview_path = Path(str(result["preview-img"]))

        if not beatmap_path.is_file() or beatmap_path.stat().st_size <= 0:
            return ValidationResult(
                name="Preview render",
                ok=False,
                message=f".osu file was not downloaded correctly to {beatmap_path}.",
            )

        if not preview_path.is_file() or preview_path.stat().st_size <= 0:
            return ValidationResult(
                name="Preview render",
                ok=False,
                message=f"preview image was not written correctly to {preview_path}.",
            )

        with Image.open(preview_path) as image:
            image.verify()

        with Image.open(preview_path) as image:
            width, height = image.size
            image_format = image.format

        if width <= 0 or height <= 0:
            return ValidationResult(
                name="Preview render",
                ok=False,
                message=f"preview image has invalid dimensions: {width}x{height}.",
            )
    except PreviewError as exc:
        return ValidationResult(
            name="Preview render",
            ok=False,
            message=f"failed to generate preview for bid {TEST_BID}: {exc}",
        )
    except Exception as exc:
        return ValidationResult(
            name="Preview render",
            ok=False,
            message=f"failed to validate preview output for bid {TEST_BID}: {exc}",
        )
    finally:
        cleanup_render_preview_outputs(preview_path, beatmap_path)

    return ValidationResult(
        name="Preview render",
        ok=True,
        message=(
            f"bid {TEST_BID} downloaded and rendered successfully; image was {image_format}, "
            f"{width}x{height}. Test files were cleaned up."
        ),
    )


def cleanup_render_preview_outputs(preview_path, beatmap_path):
    for path in (preview_path, beatmap_path):
        if path is None:
            continue
        try:
            if path.is_file():
                path.unlink()
        except Exception:
            pass


def run_validations():
    return [
        validate_required_imports(),
        validate_temp_read_write(),
        validate_network(),
        validate_render_preview(),
    ]


def format_report(results):
    all_ok = all(result.ok for result in results)
    status = "OK" if all_ok else "FAILED"
    lines = [f"osu-beatmap-preview validation: {status}"]

    for result in results:
        marker = "OK" if result.ok else "FAIL"
        lines.append(f"[{marker}] {result.name}: {result.message}")

    if all_ok:
        lines.append("Environment and core preview generation are working.")
    else:
        lines.append("Some checks failed. Inspect the FAIL lines above for environment or network issues.")

    return "\n".join(lines)


def main():
    results = run_validations()
    print(format_report(results))
    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
