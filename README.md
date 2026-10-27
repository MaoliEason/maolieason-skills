# MaoliEason Skills

Reusable, auditable skills for AI agents and applications.

## Controlled Image Workflow

The image workflow is a **general-purpose reliability system**, not a staircase-specific tool. The staircase/spacecraft work is one acceptance-test case that exposed failures in method selection, geometry preservation, and release control.

### Task profiles

| Profile | Typical tasks | Production method | Key acceptance checks |
|---|---|---|---|
| Creative generation | New characters, scenes, illustrations, posters | Generative image tools, when explicitly appropriate | Content brief, composition, visual review |
| Strict local edit | Replace an object/person, remove an item, change a bounded region | Masked compositing or a dedicated local-edit adapter | Frozen-region pixel identity, approved mask, source hashes |
| Geometry/viewpoint adaptation | Match camera angle, perspective correction, rotate a 3D object | Reconstructed/modelled geometry and calibrated rendering; 2D transforms only for planar cases | Camera/axis fit, held-out anchors, silhouette and joint checks |
| Orthographic views | Front/side/top views of an existing design | One shared 3D model rendered with orthographic projection | Same model hash, projection metadata, dimensions/assumptions |
| Layout/composition | Place multiple supplied assets, posters, covers, thumbnails | Deterministic layout/compositing | Bounding boxes, occlusion rules, typography and source preservation |
| Batch transformation | Resize, crop, rotate, convert, optimize, watermark | Deterministic image operations | Dimensions, format, operation receipt, output hash |
| Quality assurance/release | Verify any candidate before delivery | Independent validation and explicit review | Task-specific gates, provenance, approval bound to exact hash |

### Architecture

1. **Task router** chooses a profile based on the user's requested output and preservation constraints.
2. **Method capability check** confirms that a real executable method exists before work begins.
3. **Adapters** implement specific methods: deterministic 2D operations, local masked compositing, 3D modelling/rendering, layout, and (for genuinely new creative work) generative creation.
4. **Immutable inputs and manifests** record source hashes, dimensions, allowed edit regions, model/camera identifiers, and task constraints.
5. **Independent validators** check objective properties and report limitations. A self-reported JSON checkbox is not proof of physical correctness.
6. **Review and release gate** keeps candidates separate from final outputs. Final release requires task-specific checks and, when required, user approval of the exact candidate hash.

### Current implementation status

- Implemented: allow-listed deterministic rotation and masked compositing runner, SHA-256 input locks, frozen-pixel verification, output receipts, and regression tests.
- Implemented: strict-edit execution guard and provenance checks for shared-model orthographic view sets.
- Not yet implemented as universal adapters: robust arbitrary object reconstruction, general camera calibration, physical/semantic structure validation, and every generative provider integration.
- Platform boundary: this repository can control artifacts processed and released through its runner. It cannot change ChatGPT's underlying tool dispatcher or prevent unrelated tools from being called outside the runner. Such outputs are not official controlled-workflow deliverables.

## Other skills

| Skill | Domain | Version | Status |
|---|---|---:|---|
| [Quant Factor Screener](./skills/quant-factor-screener/SKILL.md) | Finance | 0.1.0 | Beta |
| [Portfolio Health Check](./skills/portfolio-health-check/SKILL.md) | Finance | 0.1.0 | Beta |
| [Project Architecture](./skills/project-architecture/SKILL.md) | Engineering | 0.1.0 | Beta |
| [Database Optimization](./skills/database-optimization/SKILL.md) | Engineering | 0.1.0 | Beta |
| [Controlled Image Composition](./skills/controlled-image-composition/SKILL.md) | Creative tools | 0.2.0 | Beta |

## Run checks

```bash
npm test
python -m pip install -r skills/controlled-image-composition/requirements.txt
python -m unittest discover -s skills/controlled-image-composition/tests -p 'test_*.py' -v
```

## Safety and data handling

- Use synthetic data in examples and tests.
- Never commit credentials, private project context, production logs, or user data.
- Pin a released version or commit when integrating a skill into another project.

Licensed under Apache-2.0.
