import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv

load_dotenv()


# ============================================================
# SMTP CONFIGURATION
# ============================================================

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.office365.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

HELPDESK_TICKET_EMAIL = os.getenv("HELPDESK_TICKET_EMAIL")


# ============================================================
# COMMON EMAIL SENDER
# ============================================================

def envoyer_email(
    destinataire: str,
    sujet: str,
    contenu: str,
):
    """
    Envoie un email via le serveur SMTP configuré.
    """

    if not SMTP_USER:
        raise RuntimeError(
            "SMTP_USER manquante dans le fichier .env"
        )

    if not SMTP_PASSWORD:
        raise RuntimeError(
            "SMTP_PASSWORD manquante dans le fichier .env"
        )

    if not destinataire:
        raise RuntimeError(
            "Adresse email du destinataire manquante"
        )

    message = EmailMessage()

    message["From"] = SMTP_USER
    message["To"] = destinataire
    message["Subject"] = sujet

    message.set_content(contenu)

    try:
        with smtplib.SMTP(
            SMTP_HOST,
            SMTP_PORT
        ) as server:

            server.starttls()

            server.login(
                SMTP_USER,
                SMTP_PASSWORD
            )

            server.send_message(message)

        print(
            f"Email envoyé avec succès à {destinataire}"
        )

        return True

    except Exception as e:

        print(
            f"Erreur lors de l'envoi de l'email : {e}"
        )

        raise RuntimeError(
            f"Erreur lors de l'envoi de l'email : {e}"
        )


# ============================================================
# EMAIL : NOUVEAU TICKET HELPDESK
# ============================================================

async def envoyer_email_ticket(ticket):
    """
    Envoie automatiquement les informations du ticket
    au service Helpdesk après sa création.
    """

    if not HELPDESK_TICKET_EMAIL:
        raise RuntimeError(
            "HELPDESK_TICKET_EMAIL manquante dans le fichier .env"
        )

    contenu = f"""
NOUVEAU TICKET HELPDESK RMA

Ticket : #{ticket.TicketId}

========================================

DEMANDEUR

Nom : {ticket.NomDemandeur}
Prénom : {ticket.PrenomDemandeur}
Immeuble : {ticket.Immeuble}
Étage : {ticket.Etage}

========================================

TICKET

Type de problème :
{ticket.TypeProbleme}

Priorité :
{ticket.Priorite}

Statut :
{ticket.Statut}

Description :
{ticket.Description}

========================================

ORIGINE

{ticket.OrigineCreation}

Conversation ID :
{ticket.ConversationId or "Aucune"}

========================================

Date de création :
{ticket.DateCreation}

RMA Helpdesk
Email automatique
"""

    envoyer_email(
        destinataire=HELPDESK_TICKET_EMAIL,
        sujet=f"[RMA Helpdesk] Nouveau ticket #{ticket.TicketId}",
        contenu=contenu,
    )

    print(
        f"Email Helpdesk envoyé pour le ticket #{ticket.TicketId}"
    )

    return True


# ============================================================
# EMAIL : CODE DE RÉINITIALISATION
# ============================================================

async def envoyer_email_code_reset(
    email: str,
    code: str,
):
    """
    Envoie le code de réinitialisation du mot de passe
    à l'utilisateur.
    """

    contenu = f"""
Bonjour,

Vous avez demandé la réinitialisation de votre mot de passe
pour votre compte RMA Helpdesk.

Votre code de réinitialisation est :

    {code}

Ce code est valable pendant 10 minutes.

Si vous n'êtes pas à l'origine de cette demande,
vous pouvez ignorer cet email.

Cordialement,

RMA Helpdesk
Email automatique
"""

    envoyer_email(
        destinataire=email,
        sujet="[RMA Helpdesk] Code de réinitialisation",
        contenu=contenu,
    )

    print(
        f"Code de réinitialisation envoyé à {email}"
    )

    return True