from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus
import logging

from sqlalchemy import create_engine  # type: ignore[import]
from sqlalchemy.exc import SQLAlchemyError  # type: ignore[import]
from sqlalchemy.orm import sessionmaker, declarative_base  # type: ignore[import]
import importlib
from typing import Any

# Try to load pydantic-settings dynamically; fall back to pydantic for older setups
_pydantic_settings = importlib.util.find_spec("pydantic_settings")
if _pydantic_settings is not None:
    _mod = importlib.import_module("pydantic_settings")
    BaseSettings = getattr(_mod, "BaseSettings")
    SettingsConfigDict = getattr(_mod, "SettingsConfigDict")
else:  # pragma: no cover - fallback for environments without pydantic-settings
    try:
        _mod = importlib.import_module("pydantic_settings")
        BaseSettings = getattr(_mod, "BaseSettings")
    except ImportError:
        from pydantic import BaseSettings  # type: ignore[import]

    # Provide a compatible fallback for SettingsConfigDict used in pydantic-settings
    SettingsConfigDict = dict  # type: Any


logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # =========================================================
    # DATABASE
    # =========================================================

    DATABASE_URL: str = ""

    SQLITE_FALLBACK: bool = False
    DATABASE_URL="mssql+pyodbc://sa:riri123456@localhost/RMA_Helpdesk?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
    DB_SERVER: str = "localhost"
    DB_NAME: str = "RMA_Helpdesk"
    DB_USER: str = "sa"
    DB_PASSWORD: str = "riri123456"
    DB_DRIVER: str = "ODBC Driver 18 for SQL Server"

    # =========================================================
    # SECURITY
    # =========================================================

    SECRET_KEY: str = "change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # =========================================================
    # GROQ
    # =========================================================

    GROQ_API_KEY: str = ""

    # =========================================================
    # EMAIL / SMTP
    # =========================================================

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587

    # Compte utilisé pour se connecter au serveur SMTP
    SMTP_USER: str = ""

    # Mot de passe SMTP ou App Password
    SMTP_PASSWORD: str = ""

    # Adresse affichée comme expéditeur
    SMTP_FROM: str = ""

    # Adresse qui reçoit les tickets Helpdesk
    HELPDESK_EMAIL: str = ""

    # =========================================================
    # PASSWORD RESET
    # =========================================================

    FRONTEND_RESET_URL: str = "http://localhost:3000/reset-password"

    # =========================================================
    # PYDANTIC SETTINGS
    # =========================================================

    model_config = SettingsConfigDict(
        env_file=str(
            Path(__file__).resolve().parent.parent / ".env"
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )


# =============================================================
# SQLITE FALLBACK
# =============================================================

def _sqlite_url() -> str:
    path = Path(__file__).resolve().parent / "app.db"
    return f"sqlite:///{path}"


# =============================================================
# SQL SERVER URL
# =============================================================

def _build_sql_server_url(settings: Settings) -> str:
    db_user = quote_plus(settings.DB_USER)
    db_password = quote_plus(settings.DB_PASSWORD)
    driver = quote_plus(settings.DB_DRIVER)

    return (
        f"mssql+pyodbc://"
        f"{db_user}:{db_password}"
        f"@{settings.DB_SERVER}/"
        f"{settings.DB_NAME}"
        f"?driver={driver}"
        f"&TrustServerCertificate=yes"
    )


# =============================================================
# CREATE ENGINE
# =============================================================

def _create_engine(url: str):
    create_kwargs = {
        "pool_pre_ping": True,
    }

    if url.startswith("sqlite:"):
        create_kwargs["connect_args"] = {
            "check_same_thread": False
        }

    return create_engine(
        url,
        **create_kwargs
    )


# =============================================================
# LOAD SETTINGS
# =============================================================

settings = Settings()


# =============================================================
# DATABASE CONNECTION
# =============================================================

if settings.DATABASE_URL:
    CONNECTION_STRING = settings.DATABASE_URL
else:
    CONNECTION_STRING = _build_sql_server_url(settings)


engine = _create_engine(CONNECTION_STRING)


# =============================================================
# TEST DATABASE CONNECTION
# =============================================================

try:
    with engine.connect():
        logger.info("Connexion à la base de données réussie.")

except SQLAlchemyError as exc:

    if settings.SQLITE_FALLBACK:

        logger.warning(
            "Connexion SQL Server échouée."
            " Passage à SQLite : %s",
            exc,
        )

        CONNECTION_STRING = _sqlite_url()

        engine = _create_engine(
            CONNECTION_STRING
        )

    else:

        raise RuntimeError(
            "Impossible de se connecter à SQL Server. "
            "Vérifiez les paramètres DB dans le fichier .env "
            "ou activez SQLITE_FALLBACK=true."
        ) from exc


# =============================================================
# SQLALCHEMY
# =============================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


# =============================================================
# INITIALISATION DATABASE
# =============================================================

def init_db():
    """
    Crée les tables SQLAlchemy en développement.

    En production, utilisez plutôt votre schema.sql
    ou un système de migrations.
    """

    Base.metadata.create_all(
        bind=engine
    )


# =============================================================
# CHECK SQLITE
# =============================================================

def uses_sqlite() -> bool:
    return engine.url.drivername == "sqlite"


# =============================================================
# DATABASE DEPENDENCY
# =============================================================

def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()