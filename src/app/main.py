from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from src.app.api.routes import router
from src.app.api.runs import router as runs_router
from src.app.api.legacy_routes import legacy_router
from protein_viewer_web import page_html

app = FastAPI(title="BioNeMo Lab by ZRT219")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
def root_page():
    return HTMLResponse(content=page_html())

# Include API routers
app.include_router(router, prefix="/api")
app.include_router(runs_router, prefix="/api")
app.include_router(legacy_router)
