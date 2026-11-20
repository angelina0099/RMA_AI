from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import get_current_user
from ..services.email_service import envoyer_email_ticket
from ..services.file_storage import sauvegarder_fichier


router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"]
)


# =========================================================
# CREATION D'UN TICKET EN BASE
# =========================================================

def _creer_ticket(
    db: Session,
    user: models.User,
    payload: schemas.TicketCreate
) -> models.Ticket:
    """
    Crée un ticket en pré-remplissant automatiquement
    les informations du profil utilisateur.
    """

    ticket = models.Ticket(
        UserId=user.UserId,
        TypeProbleme=payload.typeProbleme,
        Description=payload.description,
        NomDemandeur=user.Nom,
        PrenomDemandeur=user.Prenom,
        Immeuble=user.Immeuble,
        Etage=user.Etage,
        OrigineCreation=payload.origineCreation,
        ConversationId=payload.conversationId,
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return ticket


# =========================================================
# CREER UN TICKET
# =========================================================

@router.post(
    "",
    response_model=schemas.TicketOut,
    status_code=201
)
async def creer_ticket(
    payload: schemas.TicketCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Crée un ticket et envoie automatiquement
    un email à l'équipe Helpdesk.
    """

    # -----------------------------------------------------
    # 1. Créer le ticket dans la base
    # -----------------------------------------------------

    ticket = _creer_ticket(
        db,
        current_user,
        payload
    )

    # -----------------------------------------------------
    # 2. Envoyer le ticket par email au Helpdesk
    # -----------------------------------------------------

    try:
        await envoyer_email_ticket(ticket)

        print(
            f"Email Helpdesk envoyé pour le ticket "
            f"#{ticket.TicketId}"
        )

    except Exception as e:
        # IMPORTANT :
        # Le ticket reste enregistré en base même si
        # l'envoi de l'email échoue.
        print(
            f"Erreur lors de l'envoi de l'email "
            f"du ticket #{ticket.TicketId}: {e}"
        )

    # -----------------------------------------------------
    # 3. Retourner le ticket au frontend
    # -----------------------------------------------------

    return schemas.TicketOut(
        ticketId=ticket.TicketId,
        typeProbleme=ticket.TypeProbleme,
        description=ticket.Description,
        statut=ticket.Statut,
        priorite=ticket.Priorite,
        nomDemandeur=ticket.NomDemandeur,
        prenomDemandeur=ticket.PrenomDemandeur,
        immeuble=ticket.Immeuble,
        etage=ticket.Etage,
        origineCreation=ticket.OrigineCreation,
        dateCreation=ticket.DateCreation,
    )


# =========================================================
# MES TICKETS
# =========================================================

@router.get(
    "",
    response_model=List[schemas.TicketOut]
)
def mes_tickets(
    statut: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Retourne les tickets de l'utilisateur connecté.

    Sans filtre :
        retourne tous ses tickets.

    Avec ?statut=...
        filtre par statut.
    """

    query = (
        db.query(models.Ticket)
        .filter(
            models.Ticket.UserId == current_user.UserId
        )
    )

    if statut:
        query = query.filter(
            models.Ticket.Statut == statut
        )

    tickets = (
        query
        .order_by(
            models.Ticket.DateCreation.desc()
        )
        .all()
    )

    return [
        schemas.TicketOut(
            ticketId=t.TicketId,
            typeProbleme=t.TypeProbleme,
            description=t.Description,
            statut=t.Statut,
            priorite=t.Priorite,
            nomDemandeur=t.NomDemandeur,
            prenomDemandeur=t.PrenomDemandeur,
            immeuble=t.Immeuble,
            etage=t.Etage,
            origineCreation=t.OrigineCreation,
            dateCreation=t.DateCreation,
            fichierUrl=getattr(
                t,
                "FichierUrl",
                None
            ),
            fichierNom=getattr(
                t,
                "FichierNomOriginal",
                None
            ),
        )
        for t in tickets
    ]


# =========================================================
# HISTORIQUE DES TICKETS
# =========================================================

@router.get(
    "/historique",
    response_model=List[schemas.TicketOut]
)
def historique_tickets(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Retourne les tickets résolus ou fermés
    de l'utilisateur connecté.
    """

    tickets = (
        db.query(models.Ticket)
        .filter(
            models.Ticket.UserId == current_user.UserId
        )
        .filter(
            models.Ticket.Statut.in_(
                ["Resolu", "Ferme"]
            )
        )
        .order_by(
            models.Ticket.DateMaJ.desc()
        )
        .all()
    )

    return [
        schemas.TicketOut(
            ticketId=t.TicketId,
            typeProbleme=t.TypeProbleme,
            description=t.Description,
            statut=t.Statut,
            priorite=t.Priorite,
            nomDemandeur=t.NomDemandeur,
            prenomDemandeur=t.PrenomDemandeur,
            immeuble=t.Immeuble,
            etage=t.Etage,
            origineCreation=t.OrigineCreation,
            dateCreation=t.DateCreation,
            fichierUrl=getattr(
                t,
                "FichierUrl",
                None
            ),
            fichierNom=getattr(
                t,
                "FichierNomOriginal",
                None
            ),
        )
        for t in tickets
    ]


# =========================================================
# AJOUTER UNE PIECE JOINTE A UN TICKET
# =========================================================

@router.post(
    "/{ticket_id}/piece-jointe",
    response_model=schemas.TicketOut
)
def joindre_fichier(
    ticket_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Ajoute une pièce jointe à un ticket appartenant
    à l'utilisateur connecté.
    """

    # -----------------------------------------------------
    # 1. Vérifier que le ticket appartient à l'utilisateur
    # -----------------------------------------------------

    ticket = (
        db.query(models.Ticket)
        .filter(
            models.Ticket.TicketId == ticket_id,
            models.Ticket.UserId == current_user.UserId
        )
        .first()
    )

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket introuvable"
        )

    # -----------------------------------------------------
    # 2. Sauvegarder le fichier
    # -----------------------------------------------------

    try:
        url_fichier, nom_original = sauvegarder_fichier(
            file,
            sous_dossier="tickets"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'enregistrement du fichier : {e}"
        )

    # -----------------------------------------------------
    # 3. Enregistrer le fichier dans le ticket
    # -----------------------------------------------------

    ticket.FichierUrl = url_fichier
    ticket.FichierNomOriginal = nom_original

    db.commit()
    db.refresh(ticket)

    # -----------------------------------------------------
    # 4. Retourner le ticket
    # -----------------------------------------------------

    return schemas.TicketOut(
        ticketId=ticket.TicketId,
        typeProbleme=ticket.TypeProbleme,
        description=ticket.Description,
        statut=ticket.Statut,
        priorite=ticket.Priorite,
        nomDemandeur=ticket.NomDemandeur,
        prenomDemandeur=ticket.PrenomDemandeur,
        immeuble=ticket.Immeuble,
        etage=ticket.Etage,
        origineCreation=ticket.OrigineCreation,
        dateCreation=ticket.DateCreation,
        fichierUrl=ticket.FichierUrl,
        fichierNom=ticket.FichierNomOriginal,
    )