from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os  # NOUVEAU - Ajout de l'import os

from .database import Base, engine, init_db, uses_sqlite
from .routers import auth, tickets, chat, profile

app = FastAPI(
    title="RMA Helpdesk API",
    description="API du Helpdesk RMA avec assistant chatbot (Microsoft Copilot Studio)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # a restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CORRECTION - Gestion robuste du dossier uploads
UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
try:
    # Utiliser os.makedirs au lieu de mkdir pour plus de robustesse
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    print(f"Dossier uploads prêt : {UPLOAD_DIR}")
except PermissionError:
    print(f"Erreur: Permission refusée pour créer le dossier {UPLOAD_DIR}")
    raise
except Exception as e:
    print(f"Erreur lors de la création du dossier uploads: {e}")
    raise

# Vérifier que le dossier existe et est accessible
if not UPLOAD_DIR.exists():
    raise RuntimeError(f"Impossible de créer le dossier {UPLOAD_DIR}")

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(tickets.router)
app.include_router(chat.router)

# Create tables automatically on startup. For SQL Server, this ensures the
# schema exists before the first request if the database is reachable.
init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


# NB: les tables sont creees via database/schema.sql (SQL Server).
# Base.metadata.create_all(bind=engine) peut etre utilise en developpement
# uniquement, le schema.sql reste la source de verite en production.