---
name: controlled-image-composition
description: Use when editing, replacing, or combining existing images with strict preservation, geometric alignment, fixed-region, or verifiable acceptance requirements.
---

# Controlled Image Composition

## Mandatory execution lock

For strict edits of supplied images, whole-image generation, text-to-image generation, and generative redraw are forbidden production paths. Do not call an image-generation tool as a substitute for local compositing or model-based rendering. If such a tool is accidentally called, its output is not a candidate and must not be shown or delivered as the task result.

For three-view requests, do not generate three separate views from prose and do not invent a new design. Front, side, and top views must be orthographic renders from the same reconstructed 3D model, derived from the exact approved source module. If the source is only a perspective image and its geometry cannot be reconstructed reliably, stop and report the missing geometry rather than fabricating a technical drawing.

Before production, run `scripts/execution_guard.py --manifest <manifest.json>`. If the guard fails, stop. After production, run `scripts/release_gate.py check --manifest <manifest.json>`; release only with explicit approval of the exact candidate hash.

## Required workflow

1. Lock exact approved input files with SHA-256, dimensions, formats, and source paths. Never silently substitute a similarly named or stale image.
2. Classify the task as planar 2D edit, perspective-matched insert, 3D viewpoint change, or orthographic views from one model. A 2D transform cannot create a new view of a non-planar object.
3. For image installation, record at least four fit anchors and two held-out validation anchors. For orthographic views, record source-image hash, model-source hash, reconstruction assumptions, and known/unknown dimensions.
4. Use an explicitly approved binary editable mask. White means editable; black means frozen. A proposal mask is not approved.
5. Build/adapt the module with a real 3D model for viewpoint changes. Define platform edges, wall joints, stair top/bottom connections, and the clear upper-exit path.
6. Composite deterministically only within the approved mask. For three views, render front, side, and top from one shared model hash using orthographic projection.
7. Run the execution guard. Strict edits only permit `deterministic_2d_composite` or `3d_model_render_and_composite`. Three-view tasks only permit `orthographic_render_from_single_3d_model`.
8. Run the release gate. It must verify source hashes, output dimensions, frozen pixels, anchor errors, geometry thresholds, and structure checks.
9. Show the exact candidate and close-ups to the user. Never fabricate approval. Release requires explicit human approval bound to the exact candidate SHA-256.
10. Report model reconstruction, candidate creation, automated checks, human review, and release separately.

## Fail-closed conditions

Stop without producing a final deliverable if source files/hashes are missing, geometry cannot be reconstructed reliably, method declarations are missing or generative, the mask is unapproved, frozen pixels changed, camera IDs mismatch, anchors fail, required joints or exit checks fail, three views do not share one model hash and orthographic projection, or the exact candidate has not been approved.

## Limitations

The guard checks declared methods, hashes, and view-set provenance. It cannot stop ChatGPT from calling a tool outside the controlled runner, and it cannot infer physical truth from a JSON checkbox. The release gate controls only artifacts that pass through it; it does not alter ChatGPT's underlying tool dispatcher. Keep official deliverables inside the controlled runner. Structural judgments require inspection of the actual model/candidate and explicit human review.

Only label an output FINAL after the release gate passes and the user approves that exact candidate. If geometry is unavailable or checks fail, report the blocker; never substitute a generated lookalike.
