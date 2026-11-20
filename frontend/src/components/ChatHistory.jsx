import React, { useEffect, useState } from "react";
import { getChatHistory } from "../api/api";

function formatDate(d) {
  return new Date(d).toLocaleString("fr-FR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function ChatHistory({ onContinueConversation }) {
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openId, setOpenId] = useState(null);

  useEffect(() => {
    getChatHistory()
      .then((res) => setConversations(res.data))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="empty-state">
        Chargement de l'historique...
      </div>
    );
  }

  if (conversations.length === 0) {
    return (
      <div className="empty-state">
        Vous n'avez aucune conversation pour le moment.
      </div>
    );
  }

  const toggle = (id) => {
    setOpenId((current) => (current === id ? null : id));
  };

  const continuerConversation = (conversation) => {
    if (onContinueConversation) {
      onContinueConversation(conversation);
    }
  };

  return (
    <div>
      {conversations.map((c) => {
        const isOpen = openId === c.conversationId;
        const dernierMessage =
          c.messages[c.messages.length - 1];

        return (
          <div
            className="ticket-item chat-history-item"
            key={c.conversationId}
          >
            <div
              className="chat-history-row"
              onClick={() => toggle(c.conversationId)}
            >
              <div>
                <div className="type">
                  Conversation du {formatDate(c.dateDebut)}
                </div>

                <div className="meta">
                  {c.messages.length} message
                  {c.messages.length > 1 ? "s" : ""}

                  {dernierMessage
                    ? ` · Dernier message : "${dernierMessage.contenu.slice(
                        0,
                        60
                      )}${
                        dernierMessage.contenu.length > 60
                          ? "…"
                          : ""
                      }"`
                    : ""}

                  {c.ticketIdGenere
                    ? ` · Ticket #${c.ticketIdGenere} envoyé à l'agent Helpdesk`
                    : ""}
                </div>
              </div>

              <span className="status-badge status-sent">
                {c.resolue ? "Résolue" : "Clôturée"}
              </span>
            </div>

            {isOpen && (
              <div className="chat-history-messages">

                {c.messages.map((m, idx) => (
                  <div
                    key={idx}
                    className={`msg ${m.emetteur}`}
                  >
                    {m.contenu}
                  </div>
                ))}

                {/* Bouton pour continuer */}
                <div className="chat-history-actions">
                  <button
                    type="button"
                    className="continue-chat-button"
                    onClick={(event) => {
                      event.stopPropagation();
                      continuerConversation(c);
                    }}
                  >
                    ↩ Continuer la conversation
                  </button>
                </div>

              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}