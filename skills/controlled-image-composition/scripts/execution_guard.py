#!/usr/bin/env python3
"""Preflight guard for strict image edits and orthographic view sets.

This validates the declared production contract and file provenance. It does not
prove that a model is physically correct; that requires model/image inspection.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

FORBIDDEN = {
    "image_gen", "image-generation", "whole-image-generation",
    "generative-redraw", "dall-e", "text-to-image"
}
VIEW_NAMES = ("front", "side", "top")

class GuardError(Exception):
    pass

def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def safe_file(root, item, label):
    if not isinstance(item, dict):
        raise GuardError(f"{label}: expected path and sha256")
    raw = item.get("path")
    if not isinstance(raw, str) or not raw or Path(raw).is_absolute() or ".." in Path(raw).parts:
        raise GuardError(f"{label}: unsafe relative path")
    path = (root / raw).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise GuardError(f"{label}: file missing or outside manifest root")
    actual = sha256(path)
    if item.get("sha256") != actual:
        raise GuardError(f"{label}: SHA-256 mismatch")
    return path, actual

def validate_execution_contract(manifest, root, source_module_sha256=None):
    contract = manifest.get("execution")
    if not isinstance(contract, dict):
        raise GuardError("execution contract missing; refusing untracked production path")
    task_type = contract.get("task_type")
    method = contract.get("method")
    tools = contract.get("tools_used")
    if not isinstance(tools, list) or not tools:
        raise GuardError("execution.tools_used must list actual tools")
    used = {str(x).strip().lower() for x in tools}
    forbidden = sorted(x for x in used if x in FORBIDDEN or any(y in x for y in ("whole-image-generation", "generative-redraw")))
    if forbidden:
        raise GuardError("forbidden generative method declared for strict edit: " + ", ".join(forbidden))
    if task_type == "strict_existing_image_edit":
        if method not in {"deterministic_2d_composite", "3d_model_render_and_composite"}:
            raise GuardError("strict image edits require deterministic_2d_composite or 3d_model_render_and_composite")
        if method == "3d_model_render_and_composite":
            model = contract.get("model_source")
            _, model_hash = safe_file(root, model, "execution.model_source")
            if contract.get("model_sha256") != model_hash:
                raise GuardError("execution.model_sha256 does not match model source")
        return {"task_type": task_type, "method": method, "tools_used": sorted(used)}

    if task_type == "orthographic_views_from_existing_module":
        if method != "orthographic_render_from_single_3d_model":
            raise GuardError("orthographic views must be rendered from one shared 3D model")
        if source_module_sha256 and contract.get("source_module_sha256") != source_module_sha256:
            raise GuardError("execution source-module hash does not match the locked module image")
        model_path, model_hash = safe_file(root, contract.get("model_source"), "execution.model_source")
        if contract.get("model_sha256") != model_hash:
            raise GuardError("execution.model_sha256 does not match model source")
        views = contract.get("views")
        if not isinstance(views, dict) or any(name not in views for name in VIEW_NAMES):
            raise GuardError("orthographic view set must include front, side, and top")
        seen_paths, seen_hashes = set(), set()
        for name in VIEW_NAMES:
            view_path, view_hash = safe_file(root, views[name], f"execution.views.{name}")
            if view_path == model_path:
                raise GuardError(f"{name} view path cannot be the model source")
            if views[name].get("model_sha256") != model_hash:
                raise GuardError(f"{name} view was not bound to the same model hash")
            if str(views[name].get("projection", "")).lower() != "orthographic":
                raise GuardError(f"{name} view must declare orthographic projection")
            if str(view_path) in seen_paths or view_hash in seen_hashes:
                raise GuardError("front, side, and top must be distinct output files")
            seen_paths.add(str(view_path)); seen_hashes.add(view_hash)
        return {"task_type": task_type, "method": method, "model_sha256": model_hash,
                "view_sha256": {name: views[name]["sha256"] for name in VIEW_NAMES},
                "tools_used": sorted(used)}
    raise GuardError(f"unsupported task_type: {task_type!r}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()
    try:
        path = Path(args.manifest).resolve()
        manifest = json.loads(path.read_text(encoding="utf-8"))
        inputs = manifest.get("inputs", {})
        source = inputs.get("source_module", {})
        source_hash = source.get("sha256") if isinstance(source, dict) else None
        result = validate_execution_contract(manifest, path.parent, source_hash)
        print(json.dumps({"status": "PREFLIGHT_PASSED", "execution": result}, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2

if __name__ == "__main__":
    sys.exit(main())
