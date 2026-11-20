import React, { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { sendChatMessage, createTicket } from "../api/api";
const TYPES_PROBLEME = [
  "Matériel",
  "Logiciel & Système",
  "Réseau",
  "E-mail & Messagerie",
  "Téléphonie",
  "Session & Comptes",
  "Périphériques",
  "Sécurité",
  "Stockage",
  "Autre",
];

export default function ChatBot({ conversationToContinue = null }) {
  const [messages, setMessages] = useState([
    {
      emetteur: "bot",
      contenu:
        "Bonjour ! Je suis l'assistant Helpdesk RMA. Comment puis-je vous aider aujourd'hui ?",
    },
  ]);

  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState(null);
  const [suggestTicket, setSuggestTicket] = useState(false);
  const [showTicketForm, setShowTicketForm] = useState(false);
  const [typeProbleme, setTypeProbleme] = useState(TYPES_PROBLEME[0]);
  const [sending, setSending] = useState(false);
  const [ticketCree, setTicketCree] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);

  const fileInputRef = useRef(null);
  const bottomRef = useRef(null);

  // =========================================================
  // CHARGER UNE ANCIENNE CONVERSATION
  // =========================================================

  useEffect(() => {
    if (!conversationToContinue) {
      return;
    }

    console.log(
      "Continuation de la conversation :",
      conversationToContinue.conversationId
    );

    setConversationId(conversationToContinue.conversationId);

    if (
      conversationToContinue.messages &&
      conversationToContinue.messages.length > 0
    ) {
      setMessages(conversationToContinue.messages);
    }

    // On remet les états du chat à zéro
    setSuggestTicket(false);
    setShowTicketForm(false);
    setTicketCree(null);
    setInput("");
    setSelectedFile(null);
  }, [conversationToContinue]);

  // =========================================================
  // SCROLL AUTOMATIQUE
  // =========================================================

  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, suggestTicket, showTicketForm]);


  // =========================================================
  // ENVOI MESSAGE
  // =========================================================

  const handleSend = async (e) => {
    e.preventDefault();

    if (
      (!input.trim() && !selectedFile) ||
      sending ||
      uploading
    ) {
      return;
    }

    const texte = input.trim();

    // =======================================================
    // ENVOI AVEC FICHIER
    // =======================================================

    if (selectedFile) {
      setUploading(true);

      const messageUtilisateur = {
        emetteur: "user",
        contenu:
          texte ||
          `📎 Fichier joint : ${selectedFile.name}`,
      };

      setMessages((prev) => [
        ...prev,
        messageUtilisateur,
      ]);

      setInput("");

      try {
        const formData = new FormData();

        // IMPORTANT :
        // Si on continue une ancienne conversation,
        // on utilise son conversationId.
        formData.append(
          "conversationId",
          conversationId || ""
        );

        formData.append("message", texte || "");

        formData.append("fichier", selectedFile);

        const response = await fetch(
          "http://localhost:8000/chat/message-with-file",
          {
            method: "POST",
            headers: {
              Authorization: `Bearer ${localStorage.getItem(
                "token"
              )}`,
            },
            body: formData,
          }
        );

        if (!response.ok) {
          throw new Error(
            "Erreur lors de l'envoi du message"
          );
        }

        const data = await response.json();

        setConversationId(data.conversationId);

        setMessages((prev) => [
          ...prev,
          {
            emetteur: "bot",
            contenu: data.reply,
          },
        ]);

        setSuggestTicket(data.suggestTicket);
      } catch (err) {
        console.error("Erreur :", err);

        setMessages((prev) => [
          ...prev,
          {
            emetteur: "bot",
            contenu:
              "Désolé, une erreur est survenue lors de l'envoi du fichier.",
          },
        ]);

        setSuggestTicket(true);
      } finally {
        setUploading(false);

        setSelectedFile(null);

        if (fileInputRef.current) {
          fileInputRef.current.value = "";
        }
      }

      return;
    }

    // =======================================================
    // ENVOI SANS FICHIER
    // =======================================================

    setMessages((prev) => [
      ...prev,
      {
        emetteur: "user",
        contenu: texte,
      },
    ]);

    setInput("");
    setSending(true);

    try {
      const res = await sendChatMessage({
        // IMPORTANT :
        // Si conversationId existe, le backend continue
        // cette conversation.
        conversationId: conversationId,
        message: texte,
      });

      setConversationId(res.data.conversationId);

      setMessages((prev) => [
        ...prev,
        {
          emetteur: "bot",
          contenu: res.data.reply,
        },
      ]);

      setSuggestTicket(res.data.suggestTicket);
    } catch (err) {
      console.error("Erreur :", err);

      setMessages((prev) => [
        ...prev,
        {
          emetteur: "bot",
          contenu:
            "Désolé, une erreur est survenue. Vous pouvez créer un ticket directement.",
        },
      ]);

      setSuggestTicket(true);
    } finally {
      setSending(false);
    }
  };

  // =========================================================
  // CREATION TICKET
  // =========================================================

  const handleCreateTicket = async (e) => {
    e.preventDefault();

    try {
      const res = await createTicket({
        typeProbleme,

        description: messages
          .filter((m) => m.emetteur === "user")
          .map((m) => m.contenu)
          .join(" | "),

        conversationId,

        origineCreation: "Chatbot",
      });

      setTicketCree(res.data);

      setShowTicketForm(false);

      setSuggestTicket(false);
    } catch (err) {
      console.error(err);

      alert(
        "Impossible de créer le ticket pour le moment."
      );
    }
  };

  // =========================================================
  // NOUVELLE CONVERSATION
  // =========================================================

  const nouvelleConversation = () => {
    setConversationId(null);

    setMessages([
      {
        emetteur: "bot",
        contenu:
          "Bonjour ! Je suis l'assistant Helpdesk RMA. Comment puis-je vous aider aujourd'hui ?",
      },
    ]);

    setInput("");
    setSuggestTicket(false);
    setShowTicketForm(false);
    setTicketCree(null);
    setSelectedFile(null);

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  // =========================================================
  // INTERFACE
  // =========================================================

  return (
    <div>
      <div className="chat-wrapper">

        {/* ================================================
            HEADER DU CHAT
        ================================================= */}

        {conversationId && (
          <div
            style={{
              padding: "10px 15px",
              background: "#f5f7fb",
              borderBottom: "1px solid #e5e7eb",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              fontSize: "13px",
            }}
          >
            <span>
              Conversation en cours
            </span>

            <button
              type="button"
              onClick={nouvelleConversation}
              style={{
                border: "none",
                background: "transparent",
                color: "#667eea",
                cursor: "pointer",
                fontWeight: 600,
              }}
            >
              + Nouvelle conversation
            </button>
          </div>
        )}

      {/* ================================================
    MESSAGES
================================================= */}

<div className="chat-messages">

  {messages.map((m, i) => (
    <div
      key={i}
      className={`msg ${m.emetteur}`}
    >
      {m.emetteur === "bot" ? (
        <ReactMarkdown>
          {m.contenu}
        </ReactMarkdown>
      ) : (
        m.contenu
      )}
    </div>
  ))}

  {(sending || uploading) && (
    <div className="msg bot">
      …
    </div>
  )}

  <div ref={bottomRef} />

</div>

        {/* ================================================
            SUGGESTION TICKET
        ================================================= */}

        {suggestTicket &&
          !showTicketForm &&
          !ticketCree && (
            <div className="ticket-suggest-banner">
              <span>
                Le problème ne semble pas résolu.
                Voulez-vous transférer votre demande
                au Helpdesk ?
              </span>

              <button
                onClick={() =>
                  setShowTicketForm(true)
                }
              >
                Créer un ticket
              </button>
            </div>
          )}

        {/* ================================================
            INPUT
        ================================================= */}

        <form
          className="chat-input-bar"
          onSubmit={handleSend}
        >

          

          <input
            placeholder={
              selectedFile
                ? `Fichier: ${selectedFile.name}`
                : "Écrivez votre message..."
            }
            value={input}
            onChange={(e) =>
              setInput(e.target.value)
            }
            disabled={sending || uploading}
            style={
              selectedFile
                ? { borderColor: "#667eea" }
                : {}
            }
          />

          {/* Bouton envoyer */}

          <button
            type="submit"
            disabled={
              sending ||
              uploading ||
              (!input.trim() && !selectedFile)
            }
            style={{
              padding: "10px 20px",
              background:
                sending ||
                uploading ||
                (!input.trim() && !selectedFile)
                  ? "#aab0c6"
                  : "#667eea",
              color: "white",
              border: "none",
              borderRadius: "25px",
              cursor:
                sending ||
                uploading ||
                (!input.trim() && !selectedFile)
                  ? "not-allowed"
                  : "pointer",
              fontWeight: 600,
            }}
          >
            {uploading
              ? "📎 Envoyer"
              : "Envoyer"}
          </button>

        </form>

      </div>

      {/* ================================================
          FORMULAIRE TICKET
      ================================================= */}

      {showTicketForm && (
        <div
          className="card"
          style={{ marginTop: 16 }}
        >
          <h3 style={{ marginTop: 0 }}>
            Créer un ticket Helpdesk
          </h3>

          <p
            style={{
              fontSize: 13,
              color: "#6B7280",
            }}
          >
            Vos informations (nom, prénom,
            immeuble, étage) sont récupérées
            automatiquement depuis votre profil.
          </p>

          <form onSubmit={handleCreateTicket}>

            <div className="field">
              <label>
                Type de problème
              </label>

              <select
                value={typeProbleme}
                onChange={(e) =>
                  setTypeProbleme(e.target.value)
                }
              >
                {TYPES_PROBLEME.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>

            <button
              className="btn-primary"
              type="submit"
            >
              Confirmer la création du ticket
            </button>

          </form>
        </div>
      )}

      {/* ================================================
          TICKET CREE
      ================================================= */}

      {ticketCree && (
        <div
          className="success-msg"
          style={{ marginTop: 16 }}
        >
          Ticket #{ticketCree.ticketId} créé avec
          succès ({ticketCree.typeProbleme}).
          Un agent Helpdesk va prendre en charge
          votre demande.
        </div>
      )}
    </div>
  );
}