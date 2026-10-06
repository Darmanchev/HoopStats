"""Select validated chronological evaluation archives without loading the model."""
from pathlib import Path
import re

from .evaluation import read_report


def valid_season(value: str) -> bool:
    match = re.fullmatch(r"(\d{4})-(\d{2})", value)
    return bool(match and int(match[2]) == (int(match[1]) + 1) % 100)


def read_performance(path: Path, *, skip: int = 0, limit: int = 20, season: str | None = None) -> dict:
    latest = read_report(path)
    reports = {}
    for archive in path.parent.glob('evaluation-????-??.json'):
        name = archive.stem.removeprefix('evaluation-')
        if not valid_season(name):
            continue
        report = read_report(archive)
        if report and report.get('available') and report.get('test_season') == name:
            reports[name] = report
    if latest and latest.get('available'):
        reports[latest['test_season']] = latest
    selected = season or (latest.get('test_season') if latest else None)
    report = reports.get(selected) if selected else None
    if report is None:
        return {
            'available': False,
            'reason': (latest or {}).get('reason', 'Model evaluation unavailable') if season is None else 'No held-out evaluation for this season',
            'games': [], 'total': 0, 'seasons': sorted(reports, reverse=True),
            'selected_season': selected, 'season_metrics': None,
        }
    games = report['games']
    return {**report, 'games': games[skip:skip + limit], 'total': len(games),
            'seasons': sorted(reports, reverse=True), 'selected_season': selected,
            'season_metrics': report['metrics']}
