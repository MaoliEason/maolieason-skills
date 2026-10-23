# Acceptance contract

## Source-of-truth rules

- **base_image** is the exact approved image whose unchanged regions must be preserved.
- **source_module** is the approved module reference; it is not automatically compatible with the baseline camera.
- **adapted_module** is the actual output rendered or transformed for the baseline camera.
- **editable_mask** is a task-specific, explicitly approved binary mask: white (255) means allowed to change; black (0) means frozen.
- **candidate_image** is the proposed composite, never the release artifact.
- **review_evidence** is a contact sheet or close-up set showing the geometry anchors and critical joints.

Every file entry must contain a path relative to the manifest directory and the file SHA-256. Absolute paths and path traversal are rejected.

## Geometry measurements

**fit_anchors** and **holdout_anchors** are lists of named point pairs. Each point pair contains **expected_px** (the measured point on the baseline/target geometry) and **actual_px** (the corresponding point in the adapted render/composite). Coordinates must be measured in the same final pixel coordinate system. The gate calculates Euclidean residuals rather than trusting supplied RMS numbers.

At least four fit anchors and two held-out anchors are required. Fit and held-out RMS must meet their declared limits. The maximum platform-edge and wall-joint errors must be below the declared maximum. Stair-top and stair-bottom gaps must be below the connection-gap limit. Upper-exit clearance must meet its declared minimum.

## Structural review

The manifest must explicitly record these checks as true:

- platform_edge_aligned
- wall_joint_aligned
- stair_top_connected
- stair_bottom_connected
- upper_exit_clear
- railing_does_not_block_exit

These booleans are not computer-vision proof. The exact candidate and evidence must be inspected. The separate approval file is required to release and must name the SHA-256 of the reviewed candidate.

## Approval file

Example created only after explicit user approval:

    {
      "schema_version": 1,
      "approved": true,
      "reviewer_type": "human",
      "reviewer": "project-owner",
      "candidate_sha256": "exact candidate SHA-256",
      "reviewed_at": "2026-10-23T12:00:00+08:00"
    }

Never manufacture this file or infer approval from silence, an earlier approval of another version, or the fact that the image looks plausible.
