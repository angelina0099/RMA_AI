import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import (
    hash_password,
    verify_password,
    create_access_token,
)
from ..services.email_service import envoyer_email_code_reset


router = APIRouter(
    prefix="/auth",
    tags=["Authentification"],
)


# ============================================================
# REGISTER
# ============================================================

@router.post(
    "/register",
    response_model=schemas.Token,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: schemas.UserRegister,
    db: Session = Depends(get_db),
):
    existing = (
        db.query(models.User)
        .filter(
            models.User.Email == payload.email
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail=(
                "Un compte existe deja "
                "avec cet email"
            ),
        )

    user = models.User(
        Nom=payload.nom,
        Prenom=payload.prenom,
        Email=payload.email,
        PasswordHash=hash_password(
            payload.password
        ),
        Immeuble=payload.immeuble,
        Etage=payload.etage,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(
        {
            "sub": str(user.UserId)
        }
    )

    return schemas.Token(
        access_token=token
    )


# ============================================================
# LOGIN
# ============================================================

@router.post(
    "/login",
    response_model=schemas.Token,
)
def login(
    payload: schemas.UserLogin,
    db: Session = Depends(get_db),
):
    user = (
        db.query(models.User)
        .filter(
            models.User.Email == payload.email
        )
        .first()
    )

    if not user or not verify_password(
        payload.password,
        user.PasswordHash,
    ):
        raise HTTPException(
            status_code=401,
            detail=(
                "Email ou mot de passe incorrect"
            ),
        )

    if not user.EstActif:
        raise HTTPException(
            status_code=403,
            detail=(
                "Compte desactive, "
                "contactez le Helpdesk"
            ),
        )

    token = create_access_token(
        {
            "sub": str(user.UserId)
        }
    )

    return schemas.Token(
        access_token=token
    )


# ============================================================
# FORGOT PASSWORD
# ============================================================

@router.post("/forgot-password")
async def forgot_password(
    payload: schemas.ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    """
    Génère un code à 6 chiffres et l'envoie
    à l'adresse email de l'utilisateur.
    """

    user = (
        db.query(models.User)
        .filter(
            models.User.Email == payload.email
        )
        .first()
    )

    # Ne révèle pas si l'email existe
    if not user:
        return {
            "message": (
                "Si ce compte existe, "
                "un code de reinitialisation "
                "a ete envoye."
            )
        }

    # --------------------------------------------------------
    # Invalider les anciens codes
    # --------------------------------------------------------

    anciens_codes = (
        db.query(models.PasswordResetToken)
        .filter(
            models.PasswordResetToken.UserId
            == user.UserId
        )
        .filter(
            models.PasswordResetToken.Utilise
            == False
        )
        .all()
    )

    for ancien_code in anciens_codes:
        ancien_code.Utilise = True

    # --------------------------------------------------------
    # Générer le nouveau code
    # --------------------------------------------------------

    code = f"{secrets.randbelow(1_000_000):06d}"

    reset_token = models.PasswordResetToken(
        UserId=user.UserId,
        Token=code,
        DateExpiration=(
            datetime.utcnow()
            + timedelta(minutes=10)
        ),
        Utilise=False,
    )

    db.add(reset_token)
    db.commit()

    # --------------------------------------------------------
    # Envoyer le code par email
    # --------------------------------------------------------

    try:
        await envoyer_email_code_reset(
            email=user.Email,
            code=code,
        )

    except Exception as e:

        reset_token.Utilise = True
        db.commit()

        print(
            f"Erreur envoi code reset : {e}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Impossible d'envoyer "
                "le code de reinitialisation."
            ),
        )

    return {
        "message": (
            "Si ce compte existe, "
            "un code de reinitialisation "
            "a ete envoye."
        )
    }


# ============================================================
# VERIFY RESET CODE
# ============================================================

@router.post("/verify-reset-code")
def verify_reset_code(
    payload: schemas.VerifyResetCodeRequest,
    db: Session = Depends(get_db),
):
    """
    Vérifie le code envoyé par email.
    """

    user = (
        db.query(models.User)
        .filter(
            models.User.Email == payload.email
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=400,
            detail="Code invalide ou expire",
        )

    reset_token = (
        db.query(models.PasswordResetToken)
        .filter(
            models.PasswordResetToken.UserId
            == user.UserId
        )
        .filter(
            models.PasswordResetToken.Token
            == payload.code
        )
        .filter(
            models.PasswordResetToken.Utilise
            == False
        )
        .filter(
            models.PasswordResetToken.DateExpiration
            > datetime.utcnow()
        )
        .first()
    )

    if not reset_token:
        raise HTTPException(
            status_code=400,
            detail="Code invalide ou expire",
        )

    return {
        "message": "Code valide."
    }


# ============================================================
# RESET PASSWORD
# ============================================================

@router.post("/reset-password")
def reset_password(
    payload: schemas.ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    """
    Vérifie le code puis change le mot de passe.
    """

    user = (
        db.query(models.User)
        .filter(
            models.User.Email == payload.email
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=400,
            detail="Code invalide ou expire",
        )

    reset_token = (
        db.query(models.PasswordResetToken)
        .filter(
            models.PasswordResetToken.UserId
            == user.UserId
        )
        .filter(
            models.PasswordResetToken.Token
            == payload.code
        )
        .filter(
            models.PasswordResetToken.Utilise
            == False
        )
        .filter(
            models.PasswordResetToken.DateExpiration
            > datetime.utcnow()
        )
        .first()
    )

    if not reset_token:
        raise HTTPException(
            status_code=400,
            detail="Code invalide ou expire",
        )

    # --------------------------------------------------------
    # Changer le mot de passe
    # --------------------------------------------------------

    user.PasswordHash = hash_password(
        payload.new_password
    )

    # --------------------------------------------------------
    # Invalider le code
    # --------------------------------------------------------

    reset_token.Utilise = True

    db.commit()

    return {
        "message": (
            "Mot de passe reinitialise "
            "avec succes."
        )
    }