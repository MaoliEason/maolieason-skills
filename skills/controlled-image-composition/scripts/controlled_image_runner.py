#!/usr/bin/env python3
"""Allow-listed deterministic image operations. No generative-image integration."""
import argparse, hashlib, json, math, sys
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image, ImageChops

ALLOWED = {"rotate", "composite"}
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
    inputs, params = m.get("inputs", {}), m.get("parameters", {})
    out_path = path_under(root, m.get("output"))
    receipt_path = path_under(root, m.get("receipt", "work/run_receipt.json"))
    if out_path.exists() or receipt_path.exists(): raise RunnerError("refusing to overwrite output or receipt")
    if op == "rotate":
        source, source_hash = locked_image(root, inputs.get("source_image"), "source_image")
        angle = float(params.get("angle_degrees", float("nan")))
        if not math.isfinite(angle): raise RunnerError("angle_degrees must be finite")
        expand = params.get("expand", True)
        if not isinstance(expand, bool): raise RunnerError("expand must be boolean")
        names = {"nearest": Image.Resampling.NEAREST, "bilinear": Image.Resampling.BILINEAR, "bicubic": Image.Resampling.BICUBIC, "lanczos": Image.Resampling.LANCZOS}
        resampling = str(params.get("resampling", "bicubic")).lower()
        if resampling not in names: raise RunnerError("unsupported resampling")
        result = source.rotate(angle, resample=names[resampling], expand=expand)
        hashes = {"source_image": source_hash}
        operation = {"name": op, "angle_degrees": angle, "expand": expand, "resampling": resampling}
    else:
        base, bh = locked_image(root, inputs.get("base_image"), "base_image")
        module, mh = locked_image(root, inputs.get("module_image"), "module_image")
        mask, kh = locked_image(root, inputs.get("approved_mask"), "approved_mask")
        if base.size != module.size or base.size != mask.size: raise RunnerError("base, module canvas, and mask must have identical dimensions")
        mask = mask.convert("L")
        vals = set(mask.getdata())
        if not vals.issubset({0, 255}) or 255 not in vals: raise RunnerError("mask must be nonempty and binary (0/255)")
        result = Image.composite(module.convert("RGBA"), base.convert("RGBA"), ImageChops.multiply(mask, module.convert("RGBA").getchannel("A")))
        diff = ImageChops.difference(result.convert("RGB"), base.convert("RGB"))
        changed = ImageChops.lighter(ImageChops.lighter(diff.getchannel(0), diff.getchannel(1)), diff.getchannel(2))
        frozen = ImageChops.multiply(changed, Image.eval(mask, lambda v: 255 if v == 0 else 0))
        if frozen.getbbox(): raise RunnerError("pixel changes detected outside approved mask")
        hashes = {"base_image": bh, "module_image": mh, "approved_mask": kh}
        operation = {"name": op, "frozen_region_check": "passed"}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    result.save(out_path)
    with Image.open(out_path) as im: im.verify()
    receipt = {"schema_version": 1, "status": "CANDIDATE_CREATED", "task_id": m.get("task_id", "unnamed"),
        "runner": "controlled-image-runner/1.0.0", "manifest_sha256": sha(mp), "operation": operation,
        "inputs_sha256": hashes, "output": {"path": m["output"], "sha256": sha(out_path), "size": list(result.size)},
        "created_at_utc": datetime.now(timezone.utc).isoformat(), "release_status": "NOT_RELEASED_REQUIRES_REVIEW"}
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return receipt, receipt_path

def verify(receipt_file):
    rp = Path(receipt_file).resolve()
    receipt = json.loads(rp.read_text(encoding="utf-8"))
    if receipt.get("runner") != "controlled-image-runner/1.0.0": raise RunnerError("unknown runner receipt")
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
