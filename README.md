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
