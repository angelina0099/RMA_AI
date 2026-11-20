import uuid
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)

from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import get_current_user
from ..services.file_storage import sauvegarder_fichier

from ..services.groq_service import (
    generer_reponse,
    compter_echecs,
    SEUIL_ECHECS_AVANT_TICKET,
)


router = APIRouter(
    prefix="/chat",
    tags=["Chatbot"],
)


# ============================================================
# RÉCUPÉRER OU CRÉER UNE CONVERSATION
# ============================================================

def recuperer_ou_creer_conversation(
    conversation_id: Optional[str],
    db: Session,
    current_user: models.User,
):

    if conversation_id:

        conv = (
            db.query(
                models.ChatConversation
            )
            .filter(
                models.ChatConversation.ConversationId
                == conversation_id
            )
            .filter(
                models.ChatConversation.UserId
                == current_user.UserId
            )
            .first()
        )

        if not conv:

            raise HTTPException(
                status_code=404,
                detail="Conversation introuvable",
            )

        return conv

    conv = models.ChatConversation(
        ConversationId=str(
            uuid.uuid4()
        ),
        UserId=current_user.UserId,
    )

    db.add(conv)
    db.commit()
    db.refresh(conv)

    return conv


# ============================================================
# CONSTRUIRE L'HISTORIQUE
# ============================================================

def construire_historique(
    conv,
    db: Session,
):

    messages_precedents = (
        db.query(
            models.ChatMessage
        )
        .filter(
            models.ChatMessage.ConversationId
            == conv.ConversationId
        )
        .order_by(
            models.ChatMessage.DateEnvoi
        )
        .all()
    )

    historique = []

    for message in messages_precedents:

        historique.append(
            {
                "role": (
                    "user"
                    if message.Emetteur == "user"
                    else "assistant"
                ),
                "content": message.Contenu,
            }
        )

    return historique


# ============================================================
# CALCULER LE NOMBRE D'ÉCHECS
# ============================================================

def calculer_nombre_echecs(
    historique: list[dict],
) -> int:

    return compter_echecs(
        historique
    )


# ============================================================
# DÉTERMINER SI LE TICKET PEUT ÊTRE PROPOSÉ
# ============================================================

def calculer_suggestion_ticket(
    historique: list[dict],
):

    nombre_echecs = (
        calculer_nombre_echecs(
            historique
        )
    )

    suggest_ticket = (
        nombre_echecs
        >= SEUIL_ECHECS_AVANT_TICKET
    )

    return (
        suggest_ticket,
        nombre_echecs,
    )


# ============================================================
# ENVOYER UN MESSAGE TEXTE
# ============================================================

@router.post(
    "/message",
    response_model=schemas.ChatMessageOut,
)
def envoyer_message(
    payload: schemas.ChatMessageIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        get_current_user
    ),
):

    # --------------------------------------------------------
    # 1. Récupérer ou créer la conversation
    # --------------------------------------------------------

    conv = recuperer_ou_creer_conversation(
        payload.conversationId,
        db,
        current_user,
    )

    # --------------------------------------------------------
    # 2. Enregistrer le message utilisateur
    # --------------------------------------------------------

    nouveau_message = models.ChatMessage(
        ConversationId=conv.ConversationId,
        Emetteur="user",
        Contenu=payload.message,
    )

    db.add(nouveau_message)
    db.commit()
    db.refresh(nouveau_message)

    # --------------------------------------------------------
    # 3. Construire l'historique
    # --------------------------------------------------------

    historique = construire_historique(
        conv,
        db,
    )

    # --------------------------------------------------------
    # 4. Générer la réponse Groq
    # --------------------------------------------------------

    try:

        bot_text = generer_reponse(
            historique
        )

    except Exception as exc:

        print(
            "Erreur Groq :",
            exc,
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "Le service assistant est "
                "momentanément indisponible."
            ),
        )

    # --------------------------------------------------------
    # 5. Enregistrer la réponse du bot
    # --------------------------------------------------------

    db.add(
        models.ChatMessage(
            ConversationId=conv.ConversationId,
            Emetteur="bot",
            Contenu=bot_text,
        )
    )

    # --------------------------------------------------------
    # 6. Compter les échecs
    # --------------------------------------------------------

    nombre_echecs = (
        compter_echecs(
            historique
        )
    )

    # --------------------------------------------------------
    # 7. Ticket UNIQUEMENT après 4 échecs
    # --------------------------------------------------------

    suggest_ticket = (
        nombre_echecs
        >= SEUIL_ECHECS_AVANT_TICKET
    )

    # --------------------------------------------------------
    # 8. Nombre total d'échanges
    #
    # Ce compteur ne déclenche PAS le ticket.
    # --------------------------------------------------------

    conv.NombreEchanges += 1

    db.commit()

    # --------------------------------------------------------
    # 9. Retourner au frontend
    # --------------------------------------------------------

    return schemas.ChatMessageOut(
        conversationId=conv.ConversationId,
        reply=bot_text,
        suggestTicket=suggest_ticket,
        echecsConsecutifs=nombre_echecs,
    )


# ============================================================
# MESSAGE AVEC FICHIER
# ============================================================

@router.post(
    "/message-with-file",
    response_model=schemas.ChatMessageOut,
)
def envoyer_message_avec_fichier(
    conversationId: Optional[str] = Form(None),
    message: str = Form(""),
    fichier: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        get_current_user
    ),
):

    # --------------------------------------------------------
    # 1. Récupérer ou créer la conversation
    # --------------------------------------------------------

    conv = recuperer_ou_creer_conversation(
        conversationId,
        db,
        current_user,
    )

    # --------------------------------------------------------
    # 2. Sauvegarder le fichier
    # --------------------------------------------------------

    fichier_url = None
    fichier_nom = None

    if fichier:

        try:

            (
                fichier_url,
                fichier_nom,
            ) = sauvegarder_fichier(
                fichier,
                sous_dossier="chat",
            )

        except Exception as exc:

            raise HTTPException(
                status_code=500,
                detail=(
                    "Erreur lors de l'upload "
                    f"du fichier : {str(exc)}"
                ),
            )

    # --------------------------------------------------------
    # 3. Construire le contenu du message
    # --------------------------------------------------------

    if message and message.strip():

        contenu_message = (
            message.strip()
        )

    elif fichier_nom:

        contenu_message = (
            f"Fichier joint : {fichier_nom}"
        )

    else:

        contenu_message = (
            "Fichier joint"
        )

    # --------------------------------------------------------
    # 4. Enregistrer le message utilisateur
    # --------------------------------------------------------

    nouveau_message = models.ChatMessage(
        ConversationId=conv.ConversationId,
        Emetteur="user",
        Contenu=contenu_message,
        FichierUrl=fichier_url,
        FichierNomOriginal=fichier_nom,
    )

    db.add(nouveau_message)
    db.commit()
    db.refresh(nouveau_message)

    # --------------------------------------------------------
    # 5. Construire l'historique
    # --------------------------------------------------------

    historique = construire_historique(
        conv,
        db,
    )

    # --------------------------------------------------------
    # 6. Générer la réponse Groq
    # --------------------------------------------------------

    try:

        bot_text = generer_reponse(
            historique
        )

    except Exception as exc:

        print(
            "Erreur Groq :",
            exc,
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "Le service assistant est "
                "momentanément indisponible."
            ),
        )

    # --------------------------------------------------------
    # 7. Enregistrer la réponse du bot
    # --------------------------------------------------------

    db.add(
        models.ChatMessage(
            ConversationId=conv.ConversationId,
            Emetteur="bot",
            Contenu=bot_text,
        )
    )

    # --------------------------------------------------------
    # 8. Compter les échecs
    # --------------------------------------------------------

    nombre_echecs = (
        compter_echecs(
            historique
        )
    )

    # --------------------------------------------------------
    # 9. Ticket UNIQUEMENT après 4 échecs
    # --------------------------------------------------------

    suggest_ticket = (
        nombre_echecs
        >= SEUIL_ECHECS_AVANT_TICKET
    )

    # --------------------------------------------------------
    # 10. Nombre total d'échanges
    # --------------------------------------------------------

    conv.NombreEchanges += 1

    db.commit()

    # --------------------------------------------------------
    # 11. Retour
    # --------------------------------------------------------

    return schemas.ChatMessageOut(
        conversationId=conv.ConversationId,
        reply=bot_text,
        suggestTicket=suggest_ticket,
        echecsConsecutifs=nombre_echecs,
    )


# ============================================================
# MARQUER LA CONVERSATION COMME RÉSOLUE
# ============================================================

@router.post(
    "/{conversation_id}/resolu"
)
def marquer_resolu(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        get_current_user
    ),
):

    conv = (
        db.query(
            models.ChatConversation
        )
        .filter(
            models.ChatConversation.ConversationId
            == conversation_id
        )
        .filter(
            models.ChatConversation.UserId
            == current_user.UserId
        )
        .first()
    )

    if not conv:

        raise HTTPException(
            status_code=404,
            detail="Conversation introuvable",
        )

    conv.Resolue = True

    db.commit()

    return {
        "message": (
            "Merci, ravi d'avoir pu vous aider !"
        )
    }


# ============================================================
# HISTORIQUE DES CONVERSATIONS
# ============================================================

@router.get(
    "/history",
    response_model=List[
        schemas.ChatConversationHistory
    ],
)
def historique_conversations(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        get_current_user
    ),
):

    conversations = (
        db.query(
            models.ChatConversation
        )
        .filter(
            models.ChatConversation.UserId
            == current_user.UserId
        )
        .order_by(
            models.ChatConversation.DateDebut.desc()
        )
        .all()
    )

    resultat = []

    for conv in conversations:

        messages_tries = sorted(
            conv.messages,
            key=lambda m: m.DateEnvoi,
        )

        resultat.append(
            schemas.ChatConversationHistory(
                conversationId=conv.ConversationId,
                dateDebut=conv.DateDebut,
                dateFin=conv.DateFin,
                resolue=conv.Resolue,
                ticketIdGenere=conv.TicketIdGenere,
                messages=[
                    schemas.ChatMessageHistoryItem(
                        emetteur=m.Emetteur,
                        contenu=m.Contenu,
                        dateEnvoi=m.DateEnvoi,
                        fichierUrl=m.FichierUrl,
                        fichierNom=m.FichierNomOriginal,
                    )
                    for m in messages_tries
                ],
            )
        )

    return resultat