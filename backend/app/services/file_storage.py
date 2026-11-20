"""
Stockage simple des fichiers uploades (chat et tickets) sur disque local,
dans backend/uploads/. Les fichiers sont servis via /uploads/... (voir le
montage StaticFiles dans main.py).
"""
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"

EXTENSIONS_AUTORISEES = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp",  # images
    ".pdf", ".doc", ".docx", ".txt",           # documents
}
TAILLE_MAX_OCTETS = 10 * 1024 * 1024  # 10 Mo


def sauvegarder_fichier(file: UploadFile, sous_dossier: str) -> tuple[str, str]:
    """
    Sauvegarde le fichier uploade sur disque et retourne (url_publique, nom_original).
    Leve une HTTPException si le fichier est invalide.
    """
    ext = Path(file.filename or "").suffix.lower()
    if ext not in EXTENSIONS_AUTORISEES:
        raise HTTPException(
            status_code=400,
            detail=f"Type de fichier non autorise ({ext}). Formats acceptes: {', '.join(sorted(EXTENSIONS_AUTORISEES))}",
        )

    contenu = file.file.read()
    if len(contenu) > TAILLE_MAX_OCTETS:
        raise HTTPException(status_code=400, detail="Fichier trop volumineux (10 Mo maximum)")

    dossier_cible = UPLOAD_DIR / sous_dossier
    dossier_cible.mkdir(parents=True, exist_ok=True)

    nom_stocke = f"{uuid.uuid4().hex}{ext}"
    with open(dossier_cible / nom_stocke, "wb") as f:
        f.write(contenu)

    url_publique = f"/uploads/{sous_dossier}/{nom_stocke}"
    return url_publique, file.filename