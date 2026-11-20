import React, { useEffect, useState } from "react";
import { getMyTickets } from "../api/api";

export default function TicketList() {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMyTickets()
      .then((res) => setTickets(res.data))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="empty-state">
        Chargement de vos tickets...
      </div>
    );
  }

  if (tickets.length === 0) {
    return (
      <div className="empty-state">
        Vous n'avez aucun ticket pour le moment.
      </div>
    );
  }

  return (
    <div>
      {tickets.map((t) => (
        <div className="ticket-item" key={t.ticketId}>
          <div>
            <div className="type">
              #{t.ticketId} — {t.typeProbleme}
            </div>

            <div className="meta">
              {t.immeuble} · Etage {t.etage} · Créé le{" "}
              {new Date(t.dateCreation).toLocaleDateString("fr-FR")}
            </div>

            {/* Fichiers éventuellement attachés au ticket */}
            {t.fichiers && t.fichiers.length > 0 && (
              <div
                style={{
                  marginTop: 8,
                  display: "flex",
                  gap: 8,
                  flexWrap: "wrap",
                }}
              >
                {t.fichiers.map((fichier, index) => (
                  <span
                    key={index}
                    style={{
                      fontSize: 12,
                      background: "#e8f5e9",
                      padding: "2px 10px",
                      borderRadius: 12,
                      display: "inline-flex",
                      alignItems: "center",
                      gap: 4,
                    }}
                  >
                    📎 {fichier.nom || fichier}
                  </span>
                ))}
              </div>
            )}
          </div>

          <span className="status-badge status-sent">
            Envoyé à l'agent Helpdesk
          </span>
        </div>
      ))}
    </div>
  );
}