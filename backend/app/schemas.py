from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, Literal
from datetime import datetime


IMMEUBLES_VALIDES = {
    "A",
    "B",
    "C",
    "BGD",
}


# Etage 0 et Etage 00 sont deux etages distincts
ETAGES_VALIDES = {
    "0",
    "00",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10",
    "11",
    "12",
    "13",
    "14",
    "15",
}


def valider_etage(v: str) -> str:
    v = (v or "").strip()

    if v not in ETAGES_VALIDES:
        raise ValueError(
            "Etage invalide "
            "(valeurs autorisees: 0, 00, 1 a 15)"
        )

    return v


def valider_immeuble(v: str) -> str:
    if v not in IMMEUBLES_VALIDES:
        raise ValueError(
            "Immeuble invalide "
            "(valeurs autorisees: A, B, C, BGD)"
        )

    return v


# ============================================================
# AUTH
# ============================================================

class UserRegister(BaseModel):
    nom: str
    prenom: str
    email: EmailStr
    password: str
    immeuble: str
    etage: str

    _v1 = field_validator("immeuble")(
        lambda cls, v: valider_immeuble(v)
    )

    _v2 = field_validator("etage")(
        lambda cls, v: valider_etage(v)
    )


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


# ============================================================
# PASSWORD RESET
# ============================================================

class VerifyResetCodeRequest(BaseModel):
    email: EmailStr
    code: str


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserProfile(BaseModel):
    userId: int
    nom: str
    prenom: str
    email: EmailStr
    immeuble: str
    etage: str

    class Config:
        from_attributes = True


# ============================================================
# TICKETS
# ============================================================

class TicketCreate(BaseModel):
    typeProbleme: str
    description: str
    conversationId: Optional[str] = None
    origineCreation: Literal[
        "Chatbot",
        "Manuel"
    ] = "Chatbot"


class TicketOut(BaseModel):
    ticketId: int
    typeProbleme: str
    description: str
    statut: str
    priorite: str
    nomDemandeur: str
    prenomDemandeur: str
    immeuble: str
    etage: str
    origineCreation: str
    dateCreation: datetime
    fichierUrl: Optional[str] = None
    fichierNom: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================
# CHAT
# ============================================================

class ChatMessageIn(BaseModel):
    conversationId: Optional[str] = None
    message: str


# NOUVEAU - Pour la gestion des fichiers
class ChatMessageWithFileIn(BaseModel):
    conversationId: Optional[str] = None
    message: str
    fichierUrl: Optional[str] = None
    fichierNom: Optional[str] = None


class ChatMessageOut(BaseModel):
    conversationId: str
    reply: str
    suggestTicket: bool = False
    echecsConsecutifs: int = 0


class ChatMessageHistoryItem(BaseModel):
    emetteur: str
    contenu: str
    dateEnvoi: datetime
    fichierUrl: Optional[str] = None
    fichierNom: Optional[str] = None

    class Config:
        from_attributes = True


class ChatConversationHistory(BaseModel):
    conversationId: str
    dateDebut: datetime
    dateFin: Optional[datetime] = None
    resolue: bool
    ticketIdGenere: Optional[int] = None
    messages: list[ChatMessageHistoryItem]

    class Config:
        from_attributes = True