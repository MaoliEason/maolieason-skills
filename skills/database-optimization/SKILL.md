---
name: database-optimization
description: Use for schema, migration, query, index, ORM, transaction, cache, or data-consistency work in D1, SQLite, Drizzle, or similar relational storage. Analyze correctness and query shape before changing the database.
---

# Database Optimization

Use this skill for database structure, SQL, ORM queries, migrations, financial ledgers, imports, scheduled jobs, or derived read models.

## Establish correctness first

Identify authoritative fact tables, derived tables and rebuild rules, primary keys, stable external identifiers, entity relationships, currency and time semantics, lifecycle states, idempotency, duplicate protections, and correction/audit behavior.

Do not optimize by merging fields with different fact roles. Cash-flow ownership, asset ownership, transaction state, valuation, and unrealized results must remain distinguishable.

## Review queries and indexes

For each affected query:

- capture filters, joins, sort order, pagination, and expected cardinality;
- inspect existing indexes before adding one;
- verify a composite index matches leading equality predicates and sort order;
- avoid duplicate-prefix indexes and unnecessary write cost;
- inspect query plans where supported;
- measure result size and request count, not only single-query latency;
- prefer a shared snapshot or read model when multiple consumers request the same core data.

Optimization must not weaken user scoping, entity scoping, state filters, currency handling, or audit visibility.

## Migration rules

- Make the smallest reversible migration that satisfies the measured need.
- Never edit an already-applied migration; add a new migration.
- Test local and remote migration paths separately when both exist.
- Verify recovery before destructive changes.
- Validate existing rows, nullability, uniqueness, foreign keys, indexes, and forward/rollback behavior.
- Update API writes, forms, imports, jobs, derived calculations, backups, and health checks together.

## Shared data and caching

For repeated quote, NAV, FX, dashboard, holding, portfolio, or watchlist data, define freshness and stale behavior; centralize loading, caching, retry, timeout, and fallback policy; expose timestamp and status; never turn missing data into zero; and invalidate dependent read models after authoritative mutations.

## Verification

Run the narrowest useful checks first, then full project checks: schema and migration validation, representative query tests, duplicate/idempotency tests, lint, typecheck, build, project tests, authorized local/remote migration checks, and API or real-page verification.

Report query/index changes, correctness evidence, migration result, CI, deployment, real-data verification, and remaining risks separately.
