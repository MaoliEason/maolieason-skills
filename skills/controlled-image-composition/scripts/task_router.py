#!/usr/bin/env python3
"""Fail-closed task router for controlled image operations."""
import argparse, json, sys
from pathlib import Path
try:
    from controlled_image_runner import RunnerError, run, verify
except ImportError:
    from .controlled_image_runner import RunnerError, run, verify

class RouterError(Exception): pass
DEFAULT_REGISTRY = Path(__file__).resolve().parents[1] / "adapters" / "registry.json"

def load_registry(path):
    try: data=json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as e: raise RouterError(f"adapter registry unreadable: {e}") from e
    if data.get("schema_version") != 1 or not isinstance(data.get("adapters"), list):
        raise RouterError("invalid adapter registry schema")
    return data

def resolve_route(manifest, registry):
    task, op=manifest.get("task_type"), manifest.get("operation")
    if not task or not op: raise RouterError("manifest must declare task_type and operation")
    found=[a for a in registry["adapters"] if a.get("task_type")==task and op in a.get("operations",[])]
    if not found:
        known=next((a for a in registry["adapters"] if a.get("task_type")==task),None)
        if known and known.get("status") != "supported":
            raise RouterError(f"capability unavailable for {task}: {known.get('reason','adapter not implemented')}")
        raise RouterError(f"no adapter registered for task_type={task!r}, operation={op!r}")
    adapter=found[0]
    if adapter.get("status") != "supported" or adapter.get("executor") != "controlled_image_runner":
        raise RouterError(f"adapter {adapter.get('id')} is not executable")
    return adapter

def route_manifest(manifest_path, registry_path=DEFAULT_REGISTRY):
    mp=Path(manifest_path).resolve()
    try: m=json.loads(mp.read_text(encoding="utf-8"))
    except Exception as e: raise RouterError(f"manifest unreadable: {e}") from e
    adapter=resolve_route(m,load_registry(registry_path))
    receipt,rp=run(mp)
    return {"status":receipt["status"],"adapter_id":adapter["id"],"task_type":m["task_type"],
            "operation":m["operation"],"output":receipt["output"],"receipt":str(rp),
            "release_status":receipt["release_status"]}

def main():
    p=argparse.ArgumentParser(); s=p.add_subparsers(dest="cmd",required=True)
    l=s.add_parser("list"); l.add_argument("--registry",default=str(DEFAULT_REGISTRY))
    r=s.add_parser("run"); r.add_argument("--manifest",required=True); r.add_argument("--registry",default=str(DEFAULT_REGISTRY))
    v=s.add_parser("verify"); v.add_argument("--receipt",required=True)
    a=p.parse_args()
    try:
        if a.cmd=="list": print(json.dumps(load_registry(a.registry),ensure_ascii=False,indent=2))
        elif a.cmd=="run": print(json.dumps(route_manifest(a.manifest,a.registry),ensure_ascii=False,indent=2))
        else: print(json.dumps(verify(a.receipt),ensure_ascii=False,indent=2))
        return 0
    except Exception as e:
        print(json.dumps({"status":"BLOCKED","error":str(e)},ensure_ascii=False,indent=2),file=sys.stderr); return 2
if __name__=="__main__": sys.exit(main())
