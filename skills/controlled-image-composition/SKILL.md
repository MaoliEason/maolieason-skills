---
name: controlled-image-composition
description: Use when editing, replacing, or combining existing images with strict preservation, geometric alignment, fixed-region, or verifiable acceptance requirements. Prefer deterministic compositing and explicit geometry checks over whole-image regeneration.
---

# Controlled Image Composition

Use this skill whenever a user supplies a baseline image and asks to modify only a region, install one visual module into another image, preserve existing geometry, or verify that a result is correct.

## Non-negotiable execution rule

Do not substitute a newly generated lookalike for an edit or composite of the supplied baseline. For strict local edits, do not use whole-image image generation as the final production path. If a separate generated asset is explicitly requested, it may be an intermediate asset only; the final composite must still use the locked baseline and a controlled mask and geometry workflow.

A written promise is not an execution step. Before editing, identify the actual executable tool and run it. If no executable method can satisfy the constraints, stop and report the blocker rather than producing a plausible-looking substitute.

## Required workflow

1. **Lock inputs.** Save exact copies of the approved baseline, source module, and any approved reference. Record SHA-256, dimensions, file format, and source paths. Never silently replace an input with a similarly named or stale image.
2. **Classify the geometry.** Decide whether the task is a planar 2D edit, a perspective-matched 2D insert, or a 3D viewpoint change. A 2D rotate, scale, or perspective warp cannot reproduce a new 3D viewpoint for a non-planar object. For viewpoint changes, reconstruct or model the geometry and render it using the baseline camera; do not claim a camera match based on appearance alone.
3. **Establish correspondence.** Record at least four fit anchors and two held-out validation anchors, in pixel coordinates, with names and evidence. Fit using the declared camera/model; report RMS and maximum error. Do not use the fit anchors as the only validation evidence.
4. **Define the editable mask.** White pixels are editable; black pixels are frozen. The mask must be approved for the current task, binary, and the same dimensions as the baseline. A proposal mask is not an approved mask.
5. **Build or adapt the module.** Preserve module design intent while adjusting geometry to the baseline coordinate system. Define platform edges, wall joints, stair top/bottom connections, and the clear path through the upper exit. For 3D work, use a real 3D scene/model and a calibrated camera; for 2D-only work, document the planar assumptions and do not claim 3D correctness.
6. **Composite onto the locked baseline.** Replace only pixels permitted by the approved mask. Do not regenerate or re-render frozen regions. Keep the candidate separate from the final/release directory.
7. **Run the release gate.** Run the Python script at skills/controlled-image-composition/scripts/release_gate.py with the check command, the manifest path, and a report path. The script verifies input hashes, output dimensions, frozen-region pixel identity, anchor residuals, geometric thresholds, required structure checks, and review-evidence hashes. A failed check must return a non-zero exit code.
8. **Human review before release.** Show the exact candidate and inspection crops to the user. Do not create or fabricate an approval file. Only after the user explicitly approves that exact candidate may a human approval file be supplied to the release command.
9. **Release.** Run the release command with the approval file and a new output path. It must refuse to overwrite an existing release, re-run all checks, bind approval to the exact candidate SHA-256, copy the candidate, and verify the copied file. The release artifact must include its validation report.
10. **Report truthfully.** Distinguish candidate generation, automated checks, human visual review, and release. Never call a result complete merely because a tool returned an image or a script exited successfully.

## Fail-closed conditions

Stop without releasing if any of these are true:

- source hashes or dimensions differ from the locked inputs;
- the approved mask is missing, unapproved, non-binary, or the wrong size;
- any frozen pixel changed;
- the base and adapted module do not use the same declared target camera/coordinate-system ID;
- fit/held-out anchors are insufficient or exceed their error limits;
- platform-edge, wall-joint, stair-top, stair-bottom, or upper-exit checks fail;
- evidence is missing;
- the user has not approved the exact candidate hash;
- the final output cannot be re-opened and verified.

## Important limitation

The release gate can objectively verify file identity, dimensions, pixel preservation, numeric anchor residuals, declared geometry measurements, and approval binding. It cannot infer from a JSON checkbox whether a railing physically blocks a walkway. Those structural judgments require actual image/model inspection and explicit human review of the exact candidate. Treat self-reported checks as untrusted until that review occurs.

## Deliverable format

Provide the candidate image directly for review, followed by a concise checklist of passed/failed items. Only label it FINAL after the release gate passes and the user has approved the exact candidate. If it fails, report the failing checks and do not disguise it as a finished result.
