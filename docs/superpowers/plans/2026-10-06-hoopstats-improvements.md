# HoopStats Improvements Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement task-by-task. Steps use checkbox syntax.

**Goal:** Implement the twelve approved reliability and exploration improvements on develop.
**Architecture:** Extend current routes with filtered queries, shared eligible-game logic, versioned ML artifacts, and small React components. Keep data-source failures local to the affected section.
**Tech Stack:** FastAPI, SQLAlchemy, PostgreSQL, Redis, scikit-learn, React, TypeScript, Vitest.
**Spec:** docs/superpowers/specs/2026-10-06-hoopstats-improvements-design.md

## Global Constraints
- Develop on `develop`.
- Keep existing API routes backward compatible; add optional fields and new endpoints.
- Use English for user-visible text.
- Never substitute invented statistics or probabilities for missing data.
- Keep favorites in browser local storage; no accounts or server persistence.
- Use existing dependencies unless implementation proves a new dependency necessary.
- Do not deploy, push, or replace production data as part of implementation.
- Offline tests must not call NBA providers or require API keys.

## Review Focus
- Null predictions and missing teams must render explicit fallbacks.
- Historical Elo and held-out model fitting must exclude future outcomes.
- Filters and favorite subsets must be applied before pagination.
- Partial provider responses must preserve stored periods and scores.
- Route changes, stale requests and invalid storage must not retain unrelated results.

### Task 1: Query reliability and source accuracy
**Files:** backend/app/routers/games.py, analytics.py, players.py; backend/app/ml/features.py; backend/app/models/game.py; backend/app/cache.py; backend/tests/test_exploration_api.py; backend/tests/test_ml_improvements.py.
**Interfaces:** `GET /games/` returns items,total; `/games/months` returns sorted month keys; `/analytics/elo?season=` returns existing entry list; `ids` on `/players/` filters before paging.
- [x] Write regression tests for filter/pagination, missing season Elo, eligibility, home/away mapping, and pre-game season regression.
- [x] Run targeted pytest; expect failures for missing routes/behavior.
- [x] Implement database filters with deterministic ordering and shared eligibility.
- [x] Run targeted tests; expect PASS.

### Task 2: Search, logs and quarter data
**Files:** backend/app/routers/search.py, player_games.py; backend/app/main.py; backend/app/services/clients/nba.py; backend/app/services/live_box_scores.py; backend/app/schemas/game.py; backend/alembic/versions/20261006_game_period_scores.py; backend/tests/test_exploration_api.py, test_nba_live_client.py.
**Interfaces:** `/search?q&limit` returns grouped id,label,url entries; `/players/{id}/games?season&skip&limit` returns items,total,coverage; Game.period_scores is nullable list of period,score1,score2.
- [x] Test escaped wildcard search, unresolved identity logs, multi-game pagination, NBA periods and preservation.
- [x] Run targeted tests and observe missing functionality.
- [x] Implement routes, migration, conservative identity joins and optional period normalization.
- [x] Run targeted tests; expect PASS.

### Task 3: Predictions and evaluation
**Files:** backend/app/ml/features.py, train.py, predict.py, evaluation.py; backend/app/services/predictions.py; backend/scripts/train_model.py; backend/app/routers/analytics.py; backend/tests/test_ml_improvements.py.
**Interfaces:** feature version 2; model bundle contains feature names/version; evaluation report version 1; `/analytics/model-performance?skip&limit` returns report metadata plus paginated held-out games.
- [x] Test home/rest inputs, no future feature leakage, missing/old artifacts, chronological holdout and report metrics.
- [x] Run targeted tests; expect FAIL.
- [x] Implement atomic artifacts, timestamp-based reload, evaluation/calibration and baseline probabilities.
- [x] Run targeted tests; expect PASS.

### Task 4: Frontend reliability and match/schedule details
**Files:** frontend/src/lib/api.ts, types/index.ts, hooks/useMatch.ts, pages/MatchDetail.tsx, Schedule.tsx; components/matches/*; frontend/src/pages/MatchDetail.test.tsx, Schedule.test.tsx.
**Interfaces:** `getSchedule(params)`, `getScheduleMonths(season)`; useMatch supplies game,stats,boxScore,errors,retry with independent data states; LiveGame.periodScores optional.
- [x] Test missing prediction, partial failures, live polling and server pagination.
- [x] Run targeted Vitest; expect FAIL.
- [x] Implement schedule filters/paging, match status/score/periods/boxscores and remove all fake 50% defaults.
- [x] Run targeted Vitest; expect PASS.

### Task 5: Frontend exploration
**Files:** hooks/useFavorites.ts, components/ui/FavoriteButton.tsx, components/layout/GlobalSearch.tsx, pages/PlayerCompare.tsx, components/players/PlayerGameLog.tsx, components/dashboard/FavoritesWidget.tsx; App.tsx, TopHeader.tsx, Players.tsx, PlayerDetail.tsx, Teams.tsx, TeamDetail.tsx, Dashboard.tsx; tests for search/favorites/comparison/logs.
**Interfaces:** useFavorites exposes teams,players,toggleTeam,togglePlayer; comparison URL left,right,season; getSearch/getPlayerGames consume task 2 routes.
- [x] Test corrupt storage, subscriber updates, search debounce/stale results/keyboard, shared comparison season and log missing coverage.
- [x] Run targeted Vitest; expect FAIL.
- [x] Implement accessible search, favorite toggles/filters/dashboard links, comparison and game logs.
- [x] Run targeted Vitest; expect PASS.

### Task 6: Analytics and verification
**Files:** pages/Analytics.tsx, hooks/useAnalytics.ts, components/analytics/ModelPerformance.tsx; README.md; Analytics.test.tsx.
**Interfaces:** season-specific getElo/getLeaders and model-performance endpoint; comparison/calibration views consume held-out report only.
- [x] Test season labels, missing datasets and missing evaluation report.
- [x] Run targeted Vitest; expect FAIL.
- [x] Implement season-aware Analytics and evaluation UI; update operational documentation.
- [x] Run `.venv/bin/pytest -q`, `npm test`, `npm run lint`, `npm run build`; expect all PASS.
- [x] Review complete diff and migration; resolve material findings and re-run affected checks.

## Execution ledger
User explicitly requested code changes after approving the specification; execute inline on develop. No push or deployment. Preserve changes for review, with commits only when a tested group is complete.
