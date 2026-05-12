import asyncio
from app.database import SessionLocal
from app.seeds import seed

async def main():
    async with SessionLocal() as db:
        await seed(db)
        print("Done!")

asyncio.run(main())