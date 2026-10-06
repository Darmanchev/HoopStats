# Operational Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Improve reliable startup, import visibility, season evaluation, mobile use, and release verification.
**Architecture:** Extend existing Redis status and scheduler flows; keep report files beside shared model artifacts. Preserve PostgreSQL volumes.
**Tech Stack:** FastAPI, Redis, PostgreSQL, React, GitHub Actions.
**Spec:** docs/superpowers/specs/2026-10-06-operational-improvements-design.md

## Global Constraints
- Work on develop as explicitly requested; do not delete database volumes.
- No public unauthenticated import writes; no browser token persistence.
- Evaluate using earlier seasons only; label results as held-out.

## Review Focus
- Duplicate scheduler and retry execution must not race or lose queued work.
- Unavailable Redis must produce clear errors and retain previous imported data.
- Missing/corrupt evaluation archives must never crash analytics.
- New filters must reset pagination and ignore stale requests.
- Mobile navigation must remain keyboard accessible.

### Task 1: Import monitoring and retries
Files: backend scheduler/status/config/analytics; frontend dashboard/API.
- [x] Add failing tests for auth, deduplication, busy scheduler and timestamp retention.
- [x] Implement allowlisted retry queue and execution timing; operator-token retry UI.
- [x] Verify backend and dashboard suites.

### Task 2: Historical holdout reports
Files: backend/app/ml/train.py, performance.py; frontend ModelPerformance/API.
- [x] Add failing tests for earlier-season training, archived season selection, missing report and pagination.
- [x] Publish per-season reports and retain latest evaluation.json compatibility.
- [x] Verify ML and evaluation UI tests.

### Task 3: Docker, mobile, performance and CI
Files: Compose/Makefile, layout/components, timing middleware, models/migration, CI, README.
- [x] Measure current schedule query and add failing migration/timing tests.
- [x] Share artifacts, remove obsolete containers on startup, add measured indexes and request timings.
- [x] Implement small-screen navigation and table containment.
- [x] Add CI checks and document retry/token/model/migration workflows.
- [x] Run complete tests, lint, build, Compose checks and real PostgreSQL migration validation.

### Task 4: Review and completion
- [x] Independent review, address material findings and repeat affected checks.
- [x] Report changes and any verification limitations.
