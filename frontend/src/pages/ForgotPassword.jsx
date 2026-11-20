import React, { useState } from "react";
import { Link } from "react-router-dom";

import {
  forgotPassword,
  verifyResetCode,
  resetPassword,
} from "../api/api";


export default function ForgotPassword() {
  const [step, setStep] = useState(1);

  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");

  const [newPassword, setNewPassword] =
    useState("");

  const [confirmPassword, setConfirmPassword] =
    useState("");

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const [loading, setLoading] =
    useState(false);


  // ==========================================================
  // STEP 1
  // SEND RESET CODE
  // ==========================================================

  const handleSendCode = async (e) => {
    e.preventDefault();

    setError("");
    setMessage("");
    setLoading(true);

    try {
      const res = await forgotPassword(email);

      setMessage(res.data.message);

      // Go to code verification
      setStep(2);

    } catch (err) {
      setError(
        err?.response?.data?.detail ||
          "Une erreur est survenue. Reessayez plus tard."
      );

    } finally {
      setLoading(false);
    }
  };


  // ==========================================================
  // STEP 2
  // VERIFY CODE
  // ==========================================================

  const handleVerifyCode = async (e) => {
    e.preventDefault();

    setError("");
    setMessage("");
    setLoading(true);

    try {
      const res = await verifyResetCode(
        email,
        code
      );

      setMessage(res.data.message);

      // Go to new password
      setStep(3);

    } catch (err) {
      setError(
        err?.response?.data?.detail ||
          "Code invalide ou expire."
      );

    } finally {
      setLoading(false);
    }
  };


  // ==========================================================
  // STEP 3
  // RESET PASSWORD
  // ==========================================================

  const handleResetPassword = async (e) => {
    e.preventDefault();

    setError("");
    setMessage("");

    if (newPassword !== confirmPassword) {
      setError(
        "Les mots de passe ne correspondent pas."
      );
      return;
    }

    if (newPassword.length < 8) {
      setError(
        "Le mot de passe doit contenir au moins 8 caracteres."
      );
      return;
    }

    setLoading(true);

    try {
      const res = await resetPassword(
        email,
        code,
        newPassword
      );

      setMessage(res.data.message);

      // Return to login after successful reset
      setTimeout(() => {
        window.location.href = "/login";
      }, 1500);

    } catch (err) {
      setError(
        err?.response?.data?.detail ||
          "Impossible de reinitialiser le mot de passe."
      );

    } finally {
      setLoading(false);
    }
  };


  // ==========================================================
  // RENDER
  // ==========================================================

  return (
    <div className="auth-shell">

      <div className="auth-card">

        <div className="auth-brand">

          <h1>
            Mot de passe oublie
          </h1>

          <span>
            Reinitialisez votre mot de passe
          </span>

        </div>


        {/* ================================================== */}
        {/* ERROR */}
        {/* ================================================== */}

        {error && (
          <div className="error-msg">
            {error}
          </div>
        )}


        {/* ================================================== */}
        {/* SUCCESS */}
        {/* ================================================== */}

        {message && (
          <div className="success-msg">
            {message}
          </div>
        )}


        {/* ================================================== */}
        {/* STEP 1 - EMAIL */}
        {/* ================================================== */}

        {step === 1 && (

          <form onSubmit={handleSendCode}>

            <div className="field">

              <label>
                Email professionnel
              </label>

              <input
                type="email"
                value={email}
                onChange={(e) =>
                  setEmail(e.target.value)
                }
                placeholder="nom@entreprise.com"
                required
              />

            </div>


            <button
              className="btn-primary"
              type="submit"
              disabled={loading}
            >

              {loading
                ? "Envoi..."
                : "Envoyer le code"}

            </button>

          </form>

        )}


        {/* ================================================== */}
        {/* STEP 2 - CODE */}
        {/* ================================================== */}

        {step === 2 && (

          <form onSubmit={handleVerifyCode}>

            <div className="field">

              <label>
                Code de verification
              </label>

              <input
                type="text"
                value={code}
                onChange={(e) =>
                  setCode(
                    e.target.value
                      .replace(/\D/g, "")
                      .slice(0, 6)
                  )
                }
                placeholder="123456"
                maxLength={6}
                inputMode="numeric"
                autoComplete="one-time-code"
                required
              />

            </div>


            <button
              className="btn-primary"
              type="submit"
              disabled={
                loading ||
                code.length !== 6
              }
            >

              {loading
                ? "Verification..."
                : "Verifier le code"}

            </button>


            <button
              type="button"
              className="btn-secondary"
              onClick={() => {
                setStep(1);
                setCode("");
                setError("");
                setMessage("");
              }}
            >
              Modifier l'email
            </button>

          </form>

        )}


        {/* ================================================== */}
        {/* STEP 3 - NEW PASSWORD */}
        {/* ================================================== */}

        {step === 3 && (

          <form onSubmit={handleResetPassword}>

            <div className="field">

              <label>
                Nouveau mot de passe
              </label>

              <input
                type="password"
                value={newPassword}
                onChange={(e) =>
                  setNewPassword(
                    e.target.value
                  )
                }
                placeholder="Nouveau mot de passe"
                autoComplete="new-password"
                required
              />

            </div>


            <div className="field">

              <label>
                Confirmer le mot de passe
              </label>

              <input
                type="password"
                value={confirmPassword}
                onChange={(e) =>
                  setConfirmPassword(
                    e.target.value
                  )
                }
                placeholder="Confirmer le mot de passe"
                autoComplete="new-password"
                required
              />

            </div>


            <button
              className="btn-primary"
              type="submit"
              disabled={loading}
            >

              {loading
                ? "Reinitialisation..."
                : "Reinitialiser le mot de passe"}

            </button>

          </form>

        )}


        {/* ================================================== */}
        {/* LOGIN LINK */}
        {/* ================================================== */}

        <div className="auth-links">

          <Link to="/login">
            Retour a la connexion
          </Link>

        </div>

      </div>

    </div>
  );
}