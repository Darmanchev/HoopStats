# HoopStats improvements design

## Approved scope and purpose

Implement all six fixes and all six features from the project review. Develop on the existing `develop` branch. Preserve existing data and unrelated work. Improve the reliability of displayed statistics and predictions, then make league exploration and model evaluation useful to a basketball fan. Extend the existing FastAPI/PostgreSQL/Redis and React/TypeScript application without introducing accounts or paid data dependencies.

## Global constraints

- Develop on `develop`.
- Keep existing API routes backward compatible; add optional fields and new endpoints.
- Use English for user-visible text.
- Never substitute invented statistics or probabilities for missing data.
- Keep favorites in browser local storage; no accounts or server persistence.
- Use existing dependencies unless implementation proves a new dependency necessary.
- Do not deploy, push, or replace production data as part of implementation.
- Offline tests must not call NBA providers or require API keys.

## Architecture and delivery order

Deliver three independently testable groups in order: accuracy and query reliability; exploration features; prediction improvements and evaluation. Share API contracts and small reusable components rather than duplicating page logic. Keep provider parsing in clients, persistence in repositories, and model feature construction in the ML package.

The existing imports consistently store `team1` as away and `team2` as home. Preserve that ordering, correct the misleading SQLAlchemy relationship mapping, and expose explicit home/away information where required. Check existing legacy imports before interpreting venue in model features; skip unverified historical venue inputs rather than guessing.

## Group 1: accuracy and reliability

### Missing predictions

Audit all probability widgets, including match details and schedule/dashboard cards. A null probability must display “Prediction unavailable” and no win-probability bar or favorite label. A real 50% prediction remains a valid even matchup. Missing team information produces a visible fallback instead of a blank page.

### Season consistency

Analytics gets a season selector populated from available imported data. Player leaders and Elo use the selected season; page labels derive from that selection. Elo for a historical season is calculated chronologically using eligible results through the end of that season, never later results. Earlier seasons may initialize ratings. Report separately when selected-season player or game data is unavailable. Preserve existing no-season API behavior. Season-specific cache keys prevent cross-season contamination.

### Independent match data failures

Load the game as the essential request. Team statistics and box scores have independent loading/error/empty states. Failure of a supplementary request must not hide a successfully loaded game. Changing the match ID discards stale results. Provide retry actions for failed sections.

### Eligible model history

Use completed regular-season and playoff games with valid teams, non-null scores, and non-tied results for ratings and training. Exclude preseason consistently in training, current predictions, and Elo. Generate predictions only for eligible regular-season and playoff fixtures; clear obsolete preseason predictions. Prepare the season transition before computing its first game features, so offseason regression happens before a prediction rather than after it. Document this policy.

### Schedule query performance

Add `GET /games/` with optional season, competition type, status, team, date range, weekday, skip and limit filters. Return `{items, total}` using game-detail schemas with stable ordering by date/start time and ID. Limit defaults to 50 and is capped at 250. Filter in the database and paginate without downloading the full history. Schedule defaults to the latest available season, supports “All seasons,” resets pagination when filters change, and exposes Previous/Next plus total results. Month choices come from the selected season's metadata, not only the current page. Favorites filtering occurs before pagination by passing selected team abbreviations. Existing `/past` and `/upcoming` remain compatible.

## Group 2: exploration features

### Global search

Add `GET /search?q=...&limit=...` returning grouped player, team and game matches. Trim input, escape wildcard characters, cap query length at 100 and cap results at 10 per group. Search game teams by abbreviation/city/name and match dates; keep results deterministic. The header searches after a 250 ms debounce with at least two characters and links to existing detail routes. Support keyboard navigation, Enter, Escape, clear, loading, empty and failure states. Ignore stale requests. Make search accessible on mobile as well as desktop.

### Complete match details

Display scheduled/live/final status, start time, away/home designation, scores when available, current period and clock, and box scores grouped by team. Refresh live detail data every 30 seconds while the page is visible; clean up polling on navigation. The existing provider synchronization interval remains unchanged and the interface shows source freshness where known.

Persist per-period points (including overtime) through a nullable JSON field on Game with an Alembic migration. Normalize available official NBA period arrays and map them to the stored away/home ordering. Do not infer quarters from the final score; display “Quarter scores unavailable” when absent. Preserve previously imported period data when a later provider response omits it. Box scores show the existing points, rebounds, assists, steals, blocks and minutes fields.

### Player comparison

Add `/players/compare` with two searchable player selectors and one shared season selector. Show games played, points, rebounds, assists, steals, blocks, minutes and shooting percentages side by side using imported season averages. Show missing season data explicitly. Preserve selected player IDs and season in URL parameters for shareable comparisons. Prevent accidental duplicate player selection. Add an entry point from Players and player details.

### Player game logs and trends

Add `GET /players/{player_id}/games` with season, skip and limit. Resolve the official NBA ID using the existing conservative identity service, then join imported player box scores to completed games. Return date, game ID, team, opponent, home/away, result, and individual statistics, ordered newest first with deterministic ID ordering. Return total and coverage metadata; unresolved identities or absent imports produce explicit empty states. Player details show a paginated table and a recent points trend using these rows. Explain that historical coverage depends on imported box scores; do not make extra provider calls while viewing a page.

### Favorites

Add a shared favorites hook/context storing versioned team abbreviations and local player IDs. Toggle favorites from team/player cards and details, with accessible pressed state. A dashboard favorites section links to saved teams and players. Schedule supports favorite-team filtering; Players supports favorite-player filtering with correct server-side pagination. Handle malformed or unavailable local storage gracefully without breaking pages. Persist on reload and update subscribers in the same tab.

## Group 3: predictions and evaluation

### Home advantage and rest

Extend the model feature vector with a verified home indicator and rest-day difference. Calculate rest from the preceding eligible game date, capped at seven days; for teams without a preceding game use zero difference and do not claim a rest advantage. Maintain identical feature construction for training, held-out evaluation and inference. Preserve existing form, win percentage, scoring margin and Elo features. Rename scoring-margin explanations accurately: points-per-game differential is not possession-adjusted net rating.

Store feature schema/version with model artifacts and validate it on load. An old artifact must produce an explicit unavailable prediction state with retraining instructions in operational output, never an accidental feature-count crash. Model reload must detect a replaced artifact. Write model files atomically after successful training; regenerate predictions after retraining.

### Historical evaluation and calibration

Evaluate with a chronological holdout: train on earlier seasons and evaluate the latest eligible season. Feature histories may contain prior test-season results available before each game, but model fitting cannot see held-out outcomes. If fewer than two eligible seasons or classes are available, report insufficient evaluation data rather than displaying training accuracy as test accuracy.

Persist a versioned JSON report beside the model artifact containing evaluation season, training/test counts, model feature version, training timestamp, accuracy, log loss, Brier score and AUC when defined. Compare model results with a probability-based Elo baseline and a home-team baseline. Include ten fixed probability bins with sample counts, average predicted probability and observed win rate; omit empty-bin observed rates. Export per-game held-out predictions sufficient to inspect results. The report must describe a held-out evaluator even though the final deployed model is refit on all eligible games.

Expose `GET /analytics/model-performance` and render a performance section in Analytics with metrics, baselines, calibration and a paginated held-out results table. A missing report shows “Model evaluation unavailable.” Do not manufacture historic pregame production predictions; label these results as held-out evaluation. Validate report shape and expose no local filesystem paths.

## Verification and acceptance

Each group receives focused backend and frontend regression tests before implementation, then existing relevant suites. Final verification runs the complete backend tests, frontend tests, frontend lint and production build. Check migrations upgrade/downgrade, JSON period preservation, away/home ordering, old model artifacts, empty data, partial request failures, pagination/filter interactions, race conditions, season changes, corrupt favorites storage and held-out feature leakage.

Use the existing development checkout on `develop`; no isolated branch is requested. Changes are complete when all twelve items work with available imported data, unavailable datasets are clearly identified, required checks pass, and any environment-related verification limits are reported. Update README operational and model documentation to match final behavior.
