from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path
from app.routes.generator import router as gen_router

app = FastAPI(title="Cisco Config Generator", version="1.0.0")
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent.parent / "static")), name="static")
app.include_router(gen_router)


@app.get("/", response_class=HTMLResponse)
async def index():
    html = (Path(__file__).parent.parent / "web" / "index.html").read_text()
    return HTMLResponse(html)
