# RMA_AI — Assistant Chatbot IA (niveau 1 de support)

Application de support interne pour RMA : un chatbot (Microsoft Copilot
Studio) répond en premier niveau aux demandes fréquentes des employés
(mot de passe, accès applicatifs, procédures RH, messagerie...). Quand il
n'arrive pas à résoudre la demande, il propose de créer automatiquement un
ticket Helpdesk, pré-rempli avec les informations du profil de l'employé
(nom, prénom, immeuble, étage).

## Stack technique
- **Backend** : Python / FastAPI
- **Frontend** : React
- **Base de données** : SQL Server
- **IA** : Microsoft Copilot Studio (agent conversationnel), intégré au
  backend via le **Direct Line API** (canal officiellement recommandé par
  Microsoft pour connecter un agent Copilot Studio à une application
  personnalisée — cf. doc Microsoft Learn "Publish an agent to mobile or
  custom apps").

## Structure du projet
```
rma-helpdesk/
├── database/
│   └── schema.sql              # Script de création SQL Server
├── backend/
│   ├── requirements.txt
│   ├── .env.example
│   └── app/
│       ├── main.py             # Point d'entrée FastAPI
│       ├── database.py         # Connexion SQL Server + settings
│       ├── models.py           # Modèles SQLAlchemy
│       ├── schemas.py          # Schémas Pydantic (validation immeuble/étage)
│       ├── security.py         # JWT + hash des mots de passe
│       ├── routers/
│       │   ├── auth.py         # Inscription / connexion / mot de passe oublié
│       │   ├── profile.py      # Profil utilisateur
│       │   ├── tickets.py      # Création, liste, historique des tickets
│       │   └── chat.py         # Échange avec Copilot Studio + suggestion ticket
│       └── services/
│           └── copilot_service.py  # Client Direct Line API
└── frontend/
    ├── package.json
    ├── public/index.html
    └── src/
        ├── App.jsx             # Routage (login, register, page principale)
        ├── styles.css
        ├── api/api.js          # Client Axios centralisé
        ├── pages/
        │   ├── Login.jsx
        │   ├── Register.jsx
        │   ├── ForgotPassword.jsx
        │   └── MainPage.jsx    # Onglets : Assistant / Mes tickets / Historique / Profil
        └── components/
            ├── ChatBot.jsx
            ├── TicketList.jsx
            ├── TicketHistory.jsx
            └── Profile.jsx
```

## Mise en route

### 1. Base de données
```bash
sqlcmd -S localhost -U sa -P <votre_mdp> -i database/schema.sql
```

### 2. Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate   # ou venv\Scripts\activate sous Windows
pip install -r requirements.txt
cp .env.example .env   # puis renseigner DB_*, SECRET_KEY, COPILOT_DIRECTLINE_SECRET...
uvicorn app.main:app --reload --port 8000
```
API disponible sur `http://localhost:8000` (doc interactive : `/docs`).

> Note: cette commande doit être lancée depuis le dossier `backend`. Si vous préférez rester à la racine du projet, utilisez `python -m uvicorn backend.app.main:app --reload --port 8000`.

### 3. Frontend
```bash
cd frontend
npm install
npm start
```
Application disponible sur `http://localhost:3000`.

> Astuce : si le port `3000` est déjà occupé, Create React App propose automatiquement un autre port (par exemple `3001`). Acceptez la proposition ou définissez `set PORT=3001` avant d'exécuter `npm start` sous Windows.

## Intégration Microsoft Copilot Studio
1. Créer/publier votre agent dans Copilot Studio (sujets : mot de passe,
   accès applicatifs, procédures RH, messagerie, + un sujet **Escalade**
   qui déclenche un événement `EscaladeHelpdesk` quand l'agent ne peut pas
   résoudre la demande).
2. Activer le canal **Direct Line** dans Paramètres > Canaux, récupérer le
   secret.
3. Renseigner `COPILOT_DIRECTLINE_SECRET` dans `.env`.
4. Le backend (`services/copilot_service.py`) gère : démarrage de
   conversation, envoi des messages utilisateur, récupération des réponses
   du bot, détection de l'événement d'escalade.
5. Le frontend (`ChatBot.jsx`) affiche l'échange et propose la création
   d'un ticket dès que :
   - l'agent déclenche l'événement d'escalade, **ou**
   - un seuil de tentatives infructueuses est atteint (3 par défaut,
     réglable via `SEUIL_ECHECS_AVANT_TICKET`).

## Points à finaliser avant mise en production
- Implémenter l'envoi d'email réel pour "mot de passe oublié" (table
  `PasswordResetTokens` déjà prévue dans `schema.sql`) et la route
  `reset-password`.
- Restreindre les origines CORS (`app/main.py`) au domaine réel du
  frontend.
- Ajouter la pagination sur `/tickets` et `/tickets/historique` si le
  volume devient important.
- Ajouter un rôle "Agent Helpdesk" (back-office) pour la prise en charge
  des tickets créés — non couvert dans ce squelette, qui se concentre sur
  le parcours employé.
