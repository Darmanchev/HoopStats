from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import teams, games, injuries

app = FastAPI(title="HoopStats API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(teams.router)
app.include_router(games.router)
app.include_router(injuries.router)

@app.get("/health")
async def health():
    return {"status": "ok"}