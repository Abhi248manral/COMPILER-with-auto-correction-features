"""
Grammar-Aware Online Compiler — FastAPI Application
====================================================
Serves the frontend (homepage, login, editor) and API endpoints.

REFACTORED:
  - Added homepage and login page routing
  - Added auth API endpoints (register, login, logout)
  - Mounted static file serving
  - Multi-language compile endpoint via api/compile.py
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os

app = FastAPI(title="CompilerFix — Multi-Language Online Compiler")

# ── CORS ─────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Paths ────────────────────────────────────────────────────────────
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))

# ── Static file mounts (CSS, JS, images) ─────────────────────────────
app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_DIR, "js")), name="js")

# ── Page Routes ──────────────────────────────────────────────────────
@app.get("/")
async def read_home():
    """Serve the animated homepage."""
    return FileResponse(os.path.join(FRONTEND_DIR, "home.html"))

@app.get("/login")
async def read_login():
    """Serve the login/register page."""
    return FileResponse(os.path.join(FRONTEND_DIR, "login.html"))

@app.get("/editor")
async def read_editor():
    """Serve the code editor page."""
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.get("/health")
async def health():
    return {"status": "ok"}

# ── Auth API ─────────────────────────────────────────────────────────
class AuthRequest(BaseModel):
    username: str
    password: str

class TokenRequest(BaseModel):
    token: str

@app.post("/api/register")
async def register(req: AuthRequest):
    from backend.auth.auth_handler import register_user
    result = register_user(req.username, req.password)
    if result["success"]:
        return result
    return JSONResponse(status_code=400, content=result)

@app.post("/api/login")
async def login(req: AuthRequest):
    from backend.auth.auth_handler import login_user
    result = login_user(req.username, req.password)
    if result["success"]:
        return result
    return JSONResponse(status_code=401, content=result)

@app.post("/api/logout")
async def logout(req: TokenRequest):
    from backend.auth.auth_handler import logout
    logout(req.token)
    return {"success": True}

# ── Compile Router ───────────────────────────────────────────────────
from backend.api import compile
app.include_router(compile.router)

# ── Run ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)