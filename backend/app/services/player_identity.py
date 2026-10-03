"""Conservative headshot identity lookup from the offline NBA player registry."""
import re
import unicodedata
from collections import defaultdict
from functools import lru_cache

from nba_api.stats.static.players import get_players


def normalize_name(name: str) -> str:
    ascii_name = "".join(char for char in unicodedata.normalize("NFKD", name) if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]", "", ascii_name.casefold())


@lru_cache(maxsize=1)
def official_player_ids() -> dict[str, int]:
    candidates = defaultdict(set)
    for player in get_players():
        candidates[normalize_name(player["full_name"])].add(player["id"])
    return {name: next(iter(ids)) for name, ids in candidates.items() if len(ids) == 1}


def resolve_nba_id(name: str, existing_id: int | None) -> int | None:
    return existing_id if existing_id is not None else official_player_ids().get(normalize_name(name))
