import React, { useEffect, useState } from "react";
import { getMyProfile } from "../api/api";

export default function Profile() {
  const [profile, setProfile] = useState(null);

  useEffect(() => {
    getMyProfile().then((res) => setProfile(res.data));
  }, []);

  if (!profile) return <div className="empty-state">Chargement du profil...</div>;

  return (
    <div className="card">
      <div className="profile-row">
        <span className="label">Nom</span>
        <span className="value">{profile.nom}</span>
      </div>
      <div className="profile-row">
        <span className="label">Prenom</span>
        <span className="value">{profile.prenom}</span>
      </div>
      <div className="profile-row">
        <span className="label">Email</span>
        <span className="value">{profile.email}</span>
      </div>
      <div className="profile-row">
        <span className="label">Immeuble</span>
        <span className="value">{profile.immeuble}</span>
      </div>
      <div className="profile-row">
        <span className="label">Etage</span>
        <span className="value">{profile.etage}</span>
      </div>
    </div>
  );
}
