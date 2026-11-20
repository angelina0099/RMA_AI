import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { registerUser } from "../api/api";

const IMMEUBLES = ["A", "B", "C", "BGD"];
// Etage 0 et Etage 00 sont deux etages distincts, suivis des etages 1 a 15
const ETAGES = ["0", "00", ...Array.from({ length: 15 }, (_, i) => String(i + 1))];

export default function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    nom: "",
    prenom: "",
    email: "",
    password: "",
    immeuble: "",
    etage: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const update = (key) => (e) => setForm({ ...form, [key]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!form.immeuble || !form.etage) {
      setError("Merci de selectionner votre immeuble et votre etage.");
      return;
    }

    setLoading(true);
    try {
      const res = await registerUser(form);
      localStorage.setItem("token", res.data.access_token);
      navigate("/");
    } catch (err) {
      setError(err.response?.data?.detail || "Impossible de creer le compte.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-shell">
      <div className="auth-card" style={{ maxWidth: 460 }}>
        <div className="auth-brand">
          <h1>Creer un compte</h1>
          <span>Renseignez vos informations pour acceder au Helpdesk</span>
        </div>

        {error && <div className="error-msg">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="field-row">
            <div className="field">
              <label>Nom</label>
              <input value={form.nom} onChange={update("nom")} required />
            </div>
            <div className="field">
              <label>Prenom</label>
              <input value={form.prenom} onChange={update("prenom")} required />
            </div>
          </div>

          <div className="field">
            <label>Email professionnel</label>
            <input type="email" value={form.email} onChange={update("email")} required />
          </div>

          <div className="field">
            <label>Mot de passe</label>
            <input type="password" value={form.password} onChange={update("password")} required minLength={6} />
          </div>

          <div className="field-row">
            <div className="field">
              <label>Immeuble</label>
              <select value={form.immeuble} onChange={update("immeuble")} required>
                <option value="">Selectionner</option>
                {IMMEUBLES.map((im) => (
                  <option key={im} value={im}>{im}</option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Etage</label>
              <select value={form.etage} onChange={update("etage")} required>
                <option value="">Selectionner</option>
                {ETAGES.map((et) => (
                  <option key={et} value={et}>Etage {et}</option>
                ))}
              </select>
            </div>
          </div>

          <button className="btn-primary" type="submit" disabled={loading}>
            {loading ? "Creation..." : "Creer mon compte"}
          </button>
        </form>

        <div className="auth-links">
          <Link to="/login">J'ai deja un compte</Link>
        </div>
      </div>
    </div>
  );
}
