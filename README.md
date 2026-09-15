# MaoliEason Skills

Reusable, auditable skills for AI agents and applications.

This repository contains general-purpose skill instructions, deterministic scripts, input contracts, methodology references, and synthetic regression tests. It does not contain private project code, credentials, production configuration, or user data.

## Skills

| Skill | Domain | Version | Status |
|---|---|---:|---|
| [Quant Factor Screener](./skills/quant-factor-screener/SKILL.md) | Finance | 0.1.0 | Beta |
| [Portfolio Health Check](./skills/portfolio-health-check/SKILL.md) | Finance | 0.1.0 | Beta |

## Use

Each directory under `skills/` is self-contained. Read its `SKILL.md`, then load only the referenced methodology or contract needed for the task. Deterministic scripts do not fetch market data or modify source data.

Run all validation and tests:

```bash
npm test
```

## Safety

- Use synthetic data in examples and tests.
- Never commit credentials, private project context, production logs, or real portfolio data.
- Treat outputs as analytical aids, not investment advice.
- Pin a released version or commit when integrating a skill into another project.

Licensed under Apache-2.0.

