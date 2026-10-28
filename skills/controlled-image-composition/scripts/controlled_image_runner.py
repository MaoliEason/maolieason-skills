#!/usr/bin/env python3
"""Allow-listed deterministic image operations. No generative-image integration."""
import argparse, hashlib, json, math, sys
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image, ImageChops

ALLOWED = {"rotate", "crop", "resize", "flip", "perspective_warp", "composite"}
TASK_TYPES = {
    "rotate": "raster_transform", "crop": "raster_transform",
    "resize": "raster_transform", "flip": "raster_transform",
    "perspective_warp": "planar_alignment", "composite": "local_composite",
}
RESAMPLING = {"nearest": Image.Resampling.NEAREST, "bilinear": Image.Resampling.BILINEAR,
              "bicubic": Image.Resampling.BICUBIC, "lanczos": Image.Resampling.LANCZOS}
class RunnerError(Exception): pass

def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(1048576), b""): h.update(b)
    return h.hexdigest()

def path_under(root, raw):
    if not isinstance(raw, str) or not raw or Path(raw).is_absolute() or ".." in Path(raw).parts:
        raise RunnerError("only safe relative paths are allowed")
    p = (root / raw).resolve()
    if not p.is_relative_to(root.resolve()): raise RunnerError("path escapes task directory")
    return p

def locked_image(root, item, label):
    if not isinstance(item, dict) or not item.get("path") or not item.get("sha256"):
        raise RunnerError(f"{label}: path and sha256 required")
    p = path_under(root, item["path"])
    if not p.is_file(): raise RunnerError(f"{label}: file missing")
    actual = sha(p)
    if actual != item["sha256"]: raise RunnerError(f"{label}: SHA-256 mismatch")
    try:
        with Image.open(p) as im: im.load(); out = im.copy()
    except Exception as e: raise RunnerError(f"{label}: unreadable image: {e}") from e
    return out, actual

def run(manifest_path):
    mp = Path(manifest_path).resolve(); root = mp.parent
    try: m = json.loads(mp.read_text(encoding="utf-8"))
    except Exception as e: raise RunnerError(f"invalid manifest: {e}") from e
    if m.get("schema_version") != 1: raise RunnerError("schema_version must be 1")
    op = m.get("operation")
    if op not in ALLOWED: raise RunnerError(f"operation {op!r} is not allow-listed; generative redraw is not supported")
    task_type = m.get("task_type")
    expected_task_type = {"rotate":"raster_transform","crop":"raster_transform","resize":"raster_transform","flip":"raster_transform","perspective_warp":"planar_alignment","composite":"local_composite"}[op]
    if task_type != expected_task_type:
        raise RunnerError(f"task_type must be {expected_task_type!r} for operation {op!r}")
    inputs, params = m.get("inputs", {}), m.get("parameters", {})
    out_path = path_under(root, m.get("output"))
    receipt_path = path_under(root, m.get("receipt", "work/run_receipt.json"))
    if out_path.exists() or receipt_path.exists(): raise RunnerError("refusing to overwrite output or receipt")
    hashes = {}
    if op in {"rotate", "crop", "resize", "flip", "perspective_warp"}:
        source, source_hash = locked_image(root, inputs.get("source_image"), "source_image")
        hashes["source_image"] = source_hash
        resampling_name = str(params.get("resampling", "bicubic")).lower()
        if resampling_name not in RESAMPLING:
            raise RunnerError(f"unsupported resampling: {resampling_name}")
        resample = RESAMPLING[resampling_name]
        if op == "rotate":
            angle = float(params.get("angle_degrees", float("nan")))
            if not math.isfinite(angle):
                raise RunnerError("angle_degrees must be finite")
            expand = params.get("expand", True)
            if not isinstance(expand, bool):
                raise RunnerError("expand must be boolean")
            result = source.rotate(angle, resample=resample, expand=expand)
            operation = {"name": op, "angle_degrees": angle, "expand": expand, "resampling": resampling_name}
        elif op == "crop":
            box = params.get("box")
            if not isinstance(box, list) or len(box) != 4 or any(isinstance(v, bool) or not isinstance(v, int) for v in box):
                raise RunnerError("crop box must be [left, top, right, bottom] integer pixels")
            left, top, right, bottom = box
            if left < 0 or top < 0 or right > source.width or bottom > source.height or right <= left or bottom <= top:
                raise RunnerError("crop box is empty or outside the source image")
            result = source.crop(tuple(box))
            operation = {"name": op, "box": box}
        elif op == "resize":
            size = params.get("size")
            if not isinstance(size, list) or len(size) != 2 or any(isinstance(v, bool) or not isinstance(v, int) or v <= 0 for v in size):
                raise RunnerError("size must be [width, height] positive integers")
            result = source.resize(tuple(size), resample=resample)
            operation = {"name": op, "size": size, "resampling": resampling_name}
        elif op == "flip":
            direction = params.get("direction")
            if direction == "horizontal":
                result = source.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            elif direction == "vertical":
                result = source.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            else:
                raise RunnerError("flip direction must be horizontal or vertical")
            operation = {"name": op, "direction": direction}
        else:
            size = params.get("output_size")
            if not isinstance(size, list) or len(size) != 2 or any(isinstance(v, bool) or not isinstance(v, int) or v <= 0 for v in size):
                raise RunnerError("output_size must be [width, height] positive integers")
            coefficients = params.get("coefficients")
            if not isinstance(coefficients, list) or len(coefficients) != 8:
                raise RunnerError("perspective coefficients must contain 8 finite numbers")
            try:
                coefficients = [float(v) for v in coefficients]
            except (TypeError, ValueError) as e:
                raise RunnerError("perspective coefficients must be numeric") from e
            if not all(math.isfinite(v) for v in coefficients):
                raise RunnerError("perspective coefficients must be finite")
            result = source.transform(tuple(size), Image.Transform.PERSPECTIVE, coefficients, resample=resample)
            operation = {"name": op, "output_size": size, "coefficients": coefficients, "resampling": resampling_name,
                         "note": "Coefficients map output pixels to source pixels; calibration is caller-supplied."}
    else:
        base, bh = locked_image(root, inputs.get("base_image"), "base_image")
        module, mh = locked_image(root, inputs.get("module_image"), "module_image")
        mask, kh = locked_image(root, inputs.get("approved_mask"), "approved_mask")
        if base.size != module.size or base.size != mask.size:
            raise RunnerError("base, module canvas, and mask must have identical dimensions")
        mask = mask.convert("L")
        vals = set(mask.getdata())
        if not vals.issubset({0, 255}) or 255 not in vals:
            raise RunnerError("mask must be nonempty and binary (0/255)")
        base_rgba, module_rgba = base.convert("RGBA"), module.convert("RGBA")
        effective = ImageChops.multiply(mask, module_rgba.getchannel("A"))
        result = Image.composite(module_rgba, base_rgba, effective)
        diff = ImageChops.difference(result, base_rgba)
        changed = ImageChops.lighter(ImageChops.lighter(diff.getchannel("R"), diff.getchannel("G")), diff.getchannel("B"))
        changed = ImageChops.lighter(changed, diff.getchannel("A"))
        frozen = ImageChops.multiply(changed, Image.eval(mask, lambda v: 255 if v == 0 else 0))
        if frozen.getbbox():
            raise RunnerError("pixel changes detected outside approved mask")
        hashes = {"base_image": bh, "module_image": mh, "approved_mask": kh}
        operation = {"name": op, "frozen_region_check": "passed"}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    result.save(out_path)
    with Image.open(out_path) as im: im.verify()
    receipt = {"schema_version": 1, "status": "CANDIDATE_CREATED", "task_id": m.get("task_id", "unnamed"), "task_type": task_type,
        "runner": "controlled-image-runner/1.1.0", "manifest_sha256": sha(mp), "operation": operation,
        "inputs_sha256": hashes, "output": {"path": m["output"], "sha256": sha(out_path), "size": list(result.size)},
        "created_at_utc": datetime.now(timezone.utc).isoformat(), "release_status": "NOT_RELEASED_REQUIRES_REVIEW"}
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return receipt, receipt_path

def verify(receipt_file):
    rp = Path(receipt_file).resolve()
    receipt = json.loads(rp.read_text(encoding="utf-8"))
    if receipt.get("runner") not in {"controlled-image-runner/1.0.0", "controlled-image-runner/1.1.0"}: raise RunnerError("unknown runner receipt")
    if receipt.get("release_status") != "NOT_RELEASED_REQUIRES_REVIEW": raise RunnerError("unexpected release state")
    root = rp.parent.parent if rp.parent.name == "work" else rp.parent
    out = path_under(root, receipt["output"]["path"])
    if not out.is_file() or sha(out) != receipt["output"]["sha256"]: raise RunnerError("output missing or hash differs from receipt")
    with Image.open(out) as im:
        im.load()
        if list(im.size) != receipt["output"]["size"]: raise RunnerError("output dimensions differ from receipt")
    return {"status": "RECEIPT_VERIFIED", "output_sha256": sha(out), "size": receipt["output"]["size"], "release_status": receipt["release_status"]}

def main():
    p = argparse.ArgumentParser(); s = p.add_subparsers(dest="cmd", required=True)
    a = s.add_parser("run"); a.add_argument("--manifest", required=True)
    b = s.add_parser("verify"); b.add_argument("--receipt", required=True)
    args = p.parse_args()
    try:
        if args.cmd == "run":
            r, rp = run(args.manifest); print(json.dumps({"status": r["status"], "receipt": str(rp), "output": r["output"], "release_status": r["release_status"]}, indent=2))
        else: print(json.dumps(verify(args.receipt), indent=2))
        return 0
    except Exception as e:
        print(json.dumps({"status": "BLOCKED", "error": str(e)}, indent=2), file=sys.stderr); return 2
if __name__ == "__main__": sys.exit(main())
