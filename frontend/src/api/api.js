import axios from "axios";

const api = axios.create({
  baseURL:
    process.env.REACT_APP_API_URL ||
    "http://localhost:8000",
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});


// ============================================================
// AUTH
// ============================================================

export const registerUser = (data) =>
  api.post("/auth/register", data);

export const loginUser = (data) =>
  api.post("/auth/login", data);

export const forgotPassword = (email) =>
  api.post("/auth/forgot-password", {
    email,
  });

export const verifyResetCode = (email, code) =>
  api.post("/auth/verify-reset-code", {
    email,
    code,
  });

export const resetPassword = (
  email,
  code,
  newPassword
) =>
  api.post("/auth/reset-password", {
    email,
    code,
    new_password: newPassword,
  });


// ============================================================
// PROFIL
// ============================================================

export const getMyProfile = () =>
  api.get("/profile/me");


// ============================================================
// TICKETS
// ============================================================

export const createTicket = (data) =>
  api.post("/tickets", data);

export const getMyTickets = () =>
  api.get("/tickets");


// ============================================================
// CHAT
// ============================================================

export const sendChatMessage = (data) =>
  api.post("/chat/message", data);

export const markConversationResolved = (
  conversationId
) =>
  api.post(
    `/chat/${conversationId}/resolu`
  );

export const getChatHistory = () =>
  api.get("/chat/history");


export default api;