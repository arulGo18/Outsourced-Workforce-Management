from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .routes import auth
from .routes import worker

from fastapi.middleware.cors import CORSMiddleware

from .database import engine
from . import models

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

app.include_router(worker.router)
app.include_router(auth.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== FRONTEND =====

app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

@app.get("/")
def home():
    return FileResponse("frontend/vendor/login.html")

@app.get("/admin")
def admin():
    return FileResponse("frontend/admin/login-admin.html")