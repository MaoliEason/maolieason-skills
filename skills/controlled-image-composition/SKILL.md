---
name: controlled-image-composition
description: Route and execute image creation, editing, transformation, restoration, composition, and multi-view derivation with method-specific controls and verifiable acceptance.
---

# Controlled Image Workbench

This is a general-purpose image workflow, not a stair-generation tool. It covers people, animals, products, architecture, vehicles, posters, diagrams, and other image subjects. Select the method from the user's actual intent and preservation requirements.

## Choose the method from the task

- Create from scratch: image generation is appropriate when there is no fixed baseline to preserve.
- Edit an existing image: lock the baseline and identify the allowed edit region. Use deterministic operations for exact edits; use an image-edit model only when explicitly requested and the user accepts that unchanged pixels or geometry may not be preserved exactly.
- Transform an existing image: use deterministic crop, rotate, resize, perspective, or color operations when sufficient.
- Compose multiple images: lock the base image, source module, and approved mask; preserve pixels outside the mask.
- Change a non-planar object's viewpoint or derive front/side/top views: use one reconstructed 3D model and calibrated camera or orthographic projections. A 2D rotate/scale cannot create a true new view of a 3D object.
- Restore or style-transfer: use the explicitly requested method and disclose where generative reconstruction may alter source details.
- Analyze an image: inspect and report; do not create a replacement unless requested.

Do not use "never generate images" as a universal rule. Never substitute generation for a requested controlled edit, and never claim exact preservation unless verified.

## Mandatory preflight

For manifest-based work, run scripts/task_router.py before selecting an adapter. It checks task/method agreement, locked input hashes, strict-preservation constraints, approved masks, and shared-model orthographic view requirements.

For supported deterministic 2D operations, use scripts/controlled_image_runner.py. It currently supports allow-listed rotation and masked composition. It does not implement 3D rendering or generative creation.

For strict edits, also run scripts/execution_guard.py and scripts/release_gate.py. For any other task family, use the matching implemented adapter. Do not imply a method is implemented merely because the router recognizes the task. If the required adapter is unavailable, stop and report the gap rather than silently falling back.

## Required workflow

1. Identify the intended output: new image, edit, transform, composite, true viewpoint change, restoration, style transfer, or analysis.
2. Lock exact inputs by path, dimensions, format, and SHA-256; never substitute stale or lookalike files.
3. Record frozen and editable regions. Exact local edits require an explicitly approved binary mask.
4. Run the task router and choose only an implemented method.
5. Execute through the method-specific adapter and record the actual method/tools used. Preflight is not execution.
6. Verify readability, dimensions, hashes, pixel preservation where required, geometric correspondence, and task-specific acceptance criteria.
7. Show the exact candidate and relevant close-ups for human review. Never fabricate approval.
8. Release only after required checks and explicit approval bound to the exact candidate hash.
9. Report routing, execution, automated verification, human review, and release separately.

## Fail-closed conditions

Stop if sources are missing or stale, the required adapter is unavailable, the method conflicts with task intent, a strict edit routes to generation, an approved mask is missing, frozen pixels changed, geometry checks fail, or required review has not occurred.

## Limits

The router only guards work that passes through the controlled workflow. It cannot prevent ChatGPT's platform-level dispatcher from calling tools outside this runner. It also cannot prove physical structure from a JSON checkbox. Official outputs must come from a controlled adapter; structural claims require inspection of the actual model or candidate.

Show the actual result when one exists. State task type, method executed, checks passed/failed, and whether the result is a candidate or approved final. Never label a plan, prompt, mock-up, or generated lookalike as a completed controlled edit.
