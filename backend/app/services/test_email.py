import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
HELPDESK_TICKET_EMAIL = os.getenv("HELPDESK_TICKET_EMAIL")

message = EmailMessage()

message["From"] = SMTP_USER
message["To"] = HELPDESK_TICKET_EMAIL
message["Subject"] = "[RMA Helpdesk] Test SMTP"

message.set_content("""
Bonjour,

Ceci est un test SMTP du Helpdesk RMA.

Si vous recevez cet email, la configuration SMTP fonctionne correctement.

RMA Helpdesk
""")

try:
    print("Connexion au serveur SMTP...")

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()

        print("Authentification...")

        server.login(
            SMTP_USER,
            SMTP_PASSWORD
        )

        print("Envoi de l'email...")

        server.send_message(message)

    print("✅ Email envoyé avec succès !")

except Exception as e:
    print("❌ Erreur SMTP :")
    print(e)