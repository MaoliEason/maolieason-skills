# MaoliEason Skills

Reusable, auditable skills for AI agents and applications. Each skill combines instructions with executable validation where appropriate.

## Skills

| Skill | Domain | Version | Status |
|---|---|---:|---|
| [Quant Factor Screener](./skills/quant-factor-screener/SKILL.md) | Finance | 0.1.0 | Beta |
| [Portfolio Health Check](./skills/portfolio-health-check/SKILL.md) | Finance | 0.1.0 | Beta |
| [Project Architecture](./skills/project-architecture/SKILL.md) | Engineering | 0.1.0 | Beta |
| [Database Optimization](./skills/database-optimization/SKILL.md) | Engineering | 0.1.0 | Beta |
| [Controlled Image Composition](./skills/controlled-image-composition/SKILL.md) | Creative tools | 0.1.0 | Beta |

## Controlled Image Production

**Controlled Image Composition is a general image-production workflow, not a staircase-specific tool.** The SHIP-001 staircase task is one test case used to expose workflow failures; it must not define the system's scope.

The system's purpose is to select a method appropriate to the user's actual image task, preserve explicit invariants, produce inspectable intermediate artifacts, and prevent unverified candidates from being represented as completed work.

Supported deterministic runner operations today:
- **Rotate** a locked image with an explicit angle and resampling mode.
- **Masked composite** a module onto a locked baseline with a binary mask and a frozen-pixel check.
- **Provenance verification** using SHA-256 receipts and output revalidation.

The broader workflow should route different task classes to dedicated adapters, each with its own constraints and tests:
- local raster edits and cleanup;
- crop, resize, rotate, perspective correction, and alignment;
- object removal/replacement and layered compositing;
- vector/diagram/document image production;
- 3D reconstruction, model editing, camera matching, and orthographic rendering;
- image sequence and multi-view consistency checks.

Do not claim an adapter exists until it is implemented and tested. The current deterministic runner does **not** yet implement general 3D reconstruction or camera calibration. For tasks needing those capabilities, the correct behavior is to stop at the capability boundary or invoke a separately implemented and verified 3D adapter—not fall back to whole-image generation.

## Use and validate

Each directory under `skills/` is self-contained. Read its `SKILL.md`, then load only referenced methodology or contracts.

Run repository checks:

```bash
npm test
python -m pip install -r skills/controlled-image-composition/requirements.txt
python -m unittest discover -s skills/controlled-image-composition/tests -p 'test_*.py' -v
```

The controlled image composition skill includes a fail-closed candidate validation and release gate. Technical checks do not replace visual review; a separate human approval must bind to the exact candidate SHA-256.

## Safety

- Use synthetic data in examples and tests.
- Never commit credentials, private project context, production logs, or user data.
- Pin a released version or commit when integrating a skill into another project.

Licensed under Apache-2.0.
