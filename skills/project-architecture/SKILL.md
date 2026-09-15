---
name: project-architecture
description: Use for feature work, refactors, navigation changes, data-flow changes, shared-component work, or tasks that may affect multiple modules. Establish ownership, source of truth, request topology, and impact before editing code.
---

# Project Architecture

Use this skill before changing work that crosses pages, APIs, database models, shared components, navigation, or derived data.

## Establish the project contract

Read the target repository's governance, skill mapping, project context, current code, schema or migrations, workflows, and runtime configuration. Treat current repository and runtime evidence as authoritative over prior chat or an earlier assistant statement.

## Decision gate

Classify the change as one or more of:

- label-only rename;
- navigation or route mapping;
- UI or component change;
- data-source or calculation change;
- API or request-topology change;
- schema or migration change;
- deployment or runtime change.

For every affected domain object, identify its stable ID, display label, source of truth, derived selectors, owning module, consumers, and mutation/invalidation path.

For data-heavy products, check whether multiple pages independently fetch or calculate the same core data. Record that as a structural issue and prefer a shared snapshot or query layer over another page-local patch.

## Design rules

- One domain fact has one owner. Views may filter, sort, aggregate, or format; they must not create a competing fact.
- Core data flows through a shared snapshot, repository, service, or query layer appropriate to the stack.
- Shared components own repeated row, detail, table, empty, loading, stale, error, and success behavior.
- Stable IDs, database fields, API contracts, and route keys are not display labels.
- Navigation is a mapping layer; moving a menu item must not silently move domain ownership.
- A visual patch must not conceal a data or component boundary problem.
- Financial or operational fact changes require an impact check across schema, API, manual input, imports, scheduled jobs, derived calculations, backups, and health checks.

## Implementation sequence

1. Write acceptance conditions.
2. Map affected objects, owners, data sources, requests, and consumers.
3. Search for duplicate calculations, requests, route aliases, and parallel components.
4. Place the fix in the owning data layer, selector, shared component, route mapping, or page composition.
5. Implement the shared layer first, then connect consumers.
6. Run applicable lint, typecheck, tests, build, migration checks, and real UI/API verification.
7. Update project context only with evidence-backed state and remaining risks.

## Stop conditions

Stop and report instead of guessing when a field has multiple plausible authorities, a migration may alter user data without an exact target, a rename may change an external contract, or required CI/deployment/runtime evidence is unavailable.

Report file changes, final commit CI, deployment, real verification, missing evidence, and blockers separately. Never call a change complete merely because a file write or commit succeeded.
