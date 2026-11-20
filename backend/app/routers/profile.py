from fastapi import APIRouter, Depends
from .. import models, schemas
from ..security import get_current_user

router = APIRouter(prefix="/profile", tags=["Profil"])


@router.get("/me", response_model=schemas.UserProfile)
def get_my_profile(current_user: models.User = Depends(get_current_user)):
    return schemas.UserProfile(
        userId=current_user.UserId,
        nom=current_user.Nom,
        prenom=current_user.Prenom,
        email=current_user.Email,
        immeuble=current_user.Immeuble,
        etage=current_user.Etage,
    )
