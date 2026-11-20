import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import ChatBot from "../components/ChatBot";
import TicketList from "../components/TicketList";
import ChatHistory from "../components/ChatHistory";
import Profile from "../components/Profile";

const TABS = [
  { key: "assistant", label: "Assistant" },
  { key: "tickets", label: "Mes tickets" },
  { key: "historique", label: "Historique des conversations" },
  { key: "profil", label: "Profil" },
];

export default function MainPage() {
  const [activeTab, setActiveTab] = useState("assistant");

  // Conversation sélectionnée depuis l'historique
  const [conversationToContinue, setConversationToContinue] =
    useState(null);

  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("token");
    navigate("/login");
  };

  // =========================================================
  // CONTINUER UNE ANCIENNE CONVERSATION
  // =========================================================

  const handleContinueConversation = (conversation) => {
    console.log(
      "Conversation sélectionnée :",
      conversation.conversationId
    );

    // Envoyer la conversation au ChatBot
    setConversationToContinue(conversation);

    // Aller automatiquement dans l'onglet Assistant
    setActiveTab("assistant");
  };

  // =========================================================
  // NOUVELLE CONVERSATION
  // =========================================================

  const handleNewConversation = () => {
    setConversationToContinue(null);
    setActiveTab("assistant");
  };

  return (
    <div className="app-shell">

      {/* =====================================================
          HEADER
      ====================================================== */}

      <header className="app-header">

        <div className="logo">
          <img
            src="/images/logo.jpeg"
            className="logo-icon"
            alt="RMA"
          />

          RMA HELPDESK AI
        </div>

        <div>
          <span className="user-pill">
            Assistant en ligne
          </span>

          <button
            className="logout-btn"
            onClick={handleLogout}
          >
            Deconnexion
          </button>
        </div>

      </header>

      {/* =====================================================
          NAVIGATION
      ====================================================== */}

      <nav className="tabs">

        {TABS.map((t) => (
          <div
            key={t.key}
            className={`tab ${
              activeTab === t.key ? "active" : ""
            }`}
            onClick={() => {
              setActiveTab(t.key);

              // Quand on clique directement sur Assistant,
              // on garde la conversation en cours.
            }}
          >
            {t.label}
          </div>
        ))}

      </nav>

      {/* =====================================================
          CONTENU
      ====================================================== */}

      <div className="tab-content">

        {/* ===================================================
            ASSISTANT
        ==================================================== */}

        <div
          style={{
            display:
              activeTab === "assistant"
                ? "block"
                : "none",
          }}
        >
          <ChatBot
            conversationToContinue={
              conversationToContinue
            }
          />
        </div>

        {/* ===================================================
            TICKETS
        ==================================================== */}

        <div
          style={{
            display:
              activeTab === "tickets"
                ? "block"
                : "none",
          }}
        >
          <TicketList />
        </div>

        {/* ===================================================
            HISTORIQUE
        ==================================================== */}

        <div
          style={{
            display:
              activeTab === "historique"
                ? "block"
                : "none",
          }}
        >
          <ChatHistory
            onContinueConversation={
              handleContinueConversation
            }
          />
        </div>

        {/* ===================================================
            PROFIL
        ==================================================== */}

        <div
          style={{
            display:
              activeTab === "profil"
                ? "block"
                : "none",
          }}
        >
          <Profile />
        </div>

      </div>

    </div>
  );
}