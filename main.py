from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()
app.mount("/static", StaticFiles(directory="frontend/pages"), name="static")

@app.get("/")
async def root():
    return FileResponse("frontend/pages/HoopStats.html")