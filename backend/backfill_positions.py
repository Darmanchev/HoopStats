"""Разовый бэкфилл позиций игроков из NBA API.

LeagueDashPlayerStats (которым работает sync_players) позицию не отдаёт,
поэтому позиция тянется отдельным запросом commonplayerinfo на каждого
игрока. Запускать разово:

    docker compose exec backend python backfill_positions.py

Позиция нормализуется в одну букву (G / F / C), чтобы совпадать с фильтром
на фронтенде и условием `Player.position == position.upper()` в роутере.
"""
import asyncio

from nba_api.stats.endpoints import commonplayerinfo
from sqlalchemy import select

from app.database import SessionLocal
from app.models.player import Player


def normalize_position(raw: str) -> str:
    """'Guard-Forward' -> 'G', 'Center' -> 'C'. Берём основную позицию."""
    if not raw:
        return "N/A"
    first = raw.strip().split("-")[0].strip().upper()
    return first[0] if first[:1] in ("G", "F", "C") else "N/A"


async def main():
    async with SessionLocal() as db:
        players = (await db.execute(select(Player))).scalars().all()
        total = len(players)
        print(f"Игроков для бэкфилла: {total}")

        updated = 0
        failed = 0
        for idx, player in enumerate(players, 1):
            try:
                info = commonplayerinfo.CommonPlayerInfo(player_id=player.nba_id)
                rs = info.get_dict()["resultSets"][0]
                data = dict(zip(rs["headers"], rs["rowSet"][0]))
                player.position = normalize_position(data.get("POSITION", ""))
                updated += 1
            except Exception as e:
                failed += 1
                print(f"  [{idx}] {player.name} (nba_id={player.nba_id}): "
                      f"{type(e).__name__}: {e}")

            await asyncio.sleep(0.6)  # уважаем rate limit NBA API
            if idx % 50 == 0:
                await db.commit()
                print(f"  ...{idx}/{total}")

        await db.commit()
        print(f"Готово: {updated} обновлено, {failed} ошибок")


if __name__ == "__main__":
    asyncio.run(main())
