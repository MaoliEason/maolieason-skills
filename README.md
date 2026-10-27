# MaoliEason Skills

Reusable, auditable skills for AI-assisted work. The image workflow is general-purpose: it routes image creation, editing, transformation, restoration, composition, style transfer, analysis, and multi-view derivation. It is not tied to any one subject or project.

## Skills

| Skill | Domain | Version | Status |
|---|---|---:|---|
| [Quant Factor Screener](./skills/quant-factor-screener/SKILL.md) | Finance | 0.1.0 | Beta |
| [Portfolio Health Check](./skills/portfolio-health-check/SKILL.md) | Finance | 0.1.0 | Beta |
| [Project Architecture](./skills/project-architecture/SKILL.md) | Engineering | 0.1.0 | Beta |
| [Database Optimization](./skills/database-optimization/SKILL.md) | Engineering | 0.1.0 | Beta |
| [Controlled Image Composition / Workbench](./skills/controlled-image-composition/SKILL.md) | Creative tools | 0.2.0 | Beta |

## Generic image task routing

Start by validating the task contract:

    python skills/controlled-image-composition/scripts/task_router.py --manifest task.json

A route approval is not proof that an image was produced. Use a method-specific adapter and verify the artifact.

The deterministic runner currently supports rotation and masked compositing:

    python skills/controlled-image-composition/scripts/controlled_image_runner.py run --manifest task.json
    python skills/controlled-image-composition/scripts/controlled_image_runner.py verify --receipt work/run_receipt.json

For exact local edits, use the execution guard and release gate. For true 3D viewpoint changes, a real model reconstruction/render adapter is still required; the router is not that adapter.

## Validate

    npm test
    python -m pip install -r skills/controlled-image-composition/requirements.txt
    python -m unittest discover -s skills/controlled-image-composition/tests -p 'test_*.py' -v

## Safety and provenance

- Use exact input hashes and task-specific approved masks.
- Do not store credentials, private context, or production user data in fixtures.
- Never claim exact preservation unless pixels/geometry were checked.
- Pin a released version or commit when integrating a skill elsewhere.

Licensed under Apache-2.0.
