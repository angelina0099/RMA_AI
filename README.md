# RMA_AI — Level 1 Helpdesk Chatbot

## Description

An internal support application for RMA. A chatbot powered by Microsoft
Copilot Studio provides first-level assistance with common employee
requests, including password issues, application access, HR procedures,
and email. When it cannot resolve a request, it offers to create a
helpdesk ticket prefilled with the employee's profile information (first
name, last name, building, and floor).

## Technology stack
- **Backend:** Python / FastAPI
- **Frontend:** React
- **Database:** SQL Server
- **AI:** Microsoft Copilot Studio, integrated with the backend through the
  **Direct Line API** for connecting the agent to a custom application.

## Project structure
```
rma-helpdesk/
├── database/
│   └── schema.sql                 # SQL Server database creation script
├── backend/
│   ├── requirements.txt
│   ├── .env.example
│   └── app/
│       ├── main.py                # FastAPI entry point
│       ├── database.py            # SQL Server connection and settings
│       ├── models.py              # SQLAlchemy models
│       ├── schemas.py             # Pydantic schemas and input validation
│       ├── security.py            # JWT and password hashing
│       ├── routers/
│       │   ├── auth.py            # Registration, login, and password reset
│       │   ├── profile.py         # User profile
│       │   ├── tickets.py         # Ticket creation, list, and history
│       │   └── chat.py            # Copilot Studio chat and ticket suggestions
│       └── services/
│           ├── email_service.py   # Email delivery
│           ├── file_storage.py    # Uploaded file storage
│           ├── groq_service.py    # Groq AI integration
│           └── knowledge_base.py  # Knowledge base search
└── frontend/
    ├── package.json
    ├── public/index.html
    └── src/
        ├── App.jsx                # Application routing
        ├── styles.css
        ├── api/api.js             # Centralized Axios client
        ├── pages/
        │   ├── Login.jsx
        │   ├── Register.jsx
        │   ├── ForgotPassword.jsx
        │   └── MainPage.jsx       # Assistant, tickets, history, and profile
        └── components/
            ├── ChatBot.jsx
            ├── ChatHistory.jsx
            ├── TicketList.jsx
            └── Profile.jsx
```

## Getting started

### 1. Database
Run the schema script against your SQL Server instance:
```bash
sqlcmd -S localhost -U sa -P <your_password> -i database/schema.sql
```

### 2. Backend
```bash
cd backend
python -m venv venv
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and provide your database, secret key, AI, and email settings.
Then start the API:
```bash
uvicorn app.main:app --reload --port 8000
```

The API is available at `http://localhost:8000`. Interactive API
documentation is at `http://localhost:8000/docs`.

> Run the command from the `backend` directory. Alternatively, from the
> project root, run `python -m uvicorn backend.app.main:app --reload --port 8000`.

### 3. Frontend
```bash
cd frontend
npm install
npm start
```

The application is available at `http://localhost:3000`. If port 3000 is
already in use, Create React App will offer another port (such as 3001).
On Windows, you can also set a different port with `set PORT=3001` before
running `npm start`.

## Microsoft Copilot Studio integration
1. Create and publish your agent in Copilot Studio. Configure topics for
   password issues, application access, HR procedures, and email. Add an
   **Escalation** topic that triggers the `EscaladeHelpdesk` event when the
   agent cannot resolve a request.
2. Enable the **Direct Line** channel under Settings > Channels and obtain
   its secret.
3. Set `COPILOT_DIRECTLINE_SECRET` in `.env`.
4. The backend starts conversations, sends user messages, retrieves bot
   replies, and detects the escalation event.
5. The frontend (`ChatBot.jsx`) displays the conversation and offers to
   create a ticket when either:
   - The agent triggers the escalation event; or
   - The configured threshold for unsuccessful attempts is reached (3 by
     default, configurable with `SEUIL_ECHECS_AVANT_TICKET`).

## Before production
- Implement actual email delivery for password resets and add the
  `reset-password` route. The `PasswordResetTokens` table is already
  defined in `schema.sql`.
- Restrict CORS origins in `app/main.py` to the production frontend domain.
- Add pagination to `/tickets` and `/tickets/historique` if the number of
  records grows.
- Add a back-office "Helpdesk Agent" role for handling submitted tickets.
  This starter project focuses on the employee experience and does not
  include that role.
