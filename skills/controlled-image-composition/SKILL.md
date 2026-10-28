---
name: controlled-image-composition
description: General controlled image-production workflow for precise edits, compositing, transformations, reconstruction, rendering, and verification while preserving user-approved constraints.
---

# Controlled Image Production

This Skill is a **general-purpose controlled image-production workflow**. It is not tied to SHIP-001, staircases, spacecraft interiors, or any single asset type. Those are example tasks and regression cases, not the scope of the project.

Its job is to:
- classify the actual image task;
- choose a method and tool that can meet the user's constraints;
- lock the source of truth and preserve frozen regions;
- run a reproducible operation through a known execution path;
- inspect the actual result and reject failures;
- release only the exact candidate that has passed the required checks.

## Mandatory execution rule

Do not treat a written plan, a Skill invocation, a generated preview, or a passing synthetic test as proof that a real task was completed. Run the selected tool on the actual input files and inspect its outputs.

For strict edits of supplied images, whole-image generation, text-to-image generation, and generative redraw are forbidden as substitutes for local editing, deterministic compositing, or model-based rendering. A generated asset may be used only when the task explicitly requests generation; it must not be represented as a pixel-preserving edit of an existing image.

For supported deterministic raster operations, use `scripts/task_router.py run --manifest <manifest.json>` as the production entry point. The router reads `adapters/registry.json`, dispatches only to an explicitly supported adapter, and refuses unsupported routes instead of falling back to a different method. The current runner supports rotation, crop, resize, flip, caller-calibrated planar perspective warp, and binary-mask compositing. Every run verifies locked inputs, refuses overwrites, and writes a hash-bound receipt. Do not claim that this runner supports capabilities it does not implement.

## Task routing

Classify each task before selecting a tool:

1. **New image generation:** the user explicitly wants a new image or concept. Use a generative image tool and evaluate its output against the brief.
2. **Deterministic 2D transform:** rotate, crop, resize, flip, or apply a known transform. Use a deterministic raster/vector tool and preserve source provenance.
3. **Local edit/composite:** remove, replace, or add an element while freezing the rest. Use a precise mask, layers, and pixel-difference checks.
4. **Perspective or planar alignment:** establish control points and apply a homography or other declared transform. Report residual errors and assumptions.
5. **3D reconstruction/viewpoint change:** reconstruct or edit a real 3D model, calibrate the target camera, then render from that camera. A 2D rotation cannot create a new view of a non-planar object.
6. **Orthographic views/multi-view consistency:** produce front, side, and top views from one shared model and orthographic cameras. Do not independently generate each view from prose.
7. **Diagram/vector/document graphics:** use the appropriate structured drawing or vector tool where geometry, text, or editability matters.
8. **Unknown or unsupported task:** stop at the capability boundary and state what input/tool is missing. Never substitute a visually plausible but technically different output.

## Required workflow

1. Lock exact source files with SHA-256, dimensions, formats, and paths. Never silently substitute a similarly named or stale image.
2. Write down task type, approved invariants, editable regions, target output, and acceptance criteria.
3. Confirm the selected tool actually supports the needed operation. If not, stop before producing an artifact.
4. For geometry-dependent tasks, record control points/anchors and distinguish fit points from held-out validation points.
5. Use an explicitly approved binary editable mask for pixel-preserving composites. White means editable; black means frozen.
6. Execute through the adapter appropriate to the task. Each adapter must declare its capabilities and reject unsupported operations.
7. Run task-specific validation: hashes and pixel preservation for raster edits; geometric residuals for alignment; topology, camera, and connection checks for 3D; text/shape checks for vector or diagram outputs.
8. Keep candidates separate from released outputs. Show the exact candidate to the user for visual review.
9. Release only after automated checks pass and, when required, the user approves the exact candidate hash.
10. Report what was actually run, what passed, what failed, and what remains unverified.

## Fail-closed conditions

Stop without claiming completion if source files are missing or stale, the method cannot meet the task's constraints, a required adapter is absent, a frozen pixel changes, geometric validation fails, a result cannot be reproduced, or required approval is missing.

## Current capability boundary

The deterministic raster runner currently supports:
- image rotation, crop, resize, and horizontal/vertical flip;
- a caller-calibrated perspective warp (it does not estimate the homography or camera parameters);
- binary-mask compositing onto a locked baseline;
- SHA-256 provenance receipts and receipt verification.

The adapter registry also explicitly records capabilities that are not implemented: object segmentation/inpainting, general 3D reconstruction, camera calibration, and orthographic rendering. The router must reject these tasks. Implement each as a separate adapter with real execution and regression tests before production use. If a task requires an unavailable adapter, do not bypass the limitation by calling a generative tool and describing it as a deterministic result.

The execution gate controls artifacts that pass through the controlled runner; it does not alter ChatGPT's underlying tool dispatcher. Therefore, official deliverables must be produced and verified by the controlled workflow, not merely by an unrelated tool call.

## Reporting format

For each task, report:
- **Method selected**
- **Actual execution performed**
- **Validation results**
- **Candidate/release status**
- **Known limitations**

Never say “done” when only a plan, prompt, or unverified preview exists.
