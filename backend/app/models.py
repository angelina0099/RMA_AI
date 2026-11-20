from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "Users"

    UserId = Column("UserId", Integer, primary_key=True, index=True)
    Nom = Column(String(100), nullable=False)
    Prenom = Column(String(100), nullable=False)
    Email = Column(String(255), unique=True, nullable=False, index=True)
    PasswordHash = Column(String(255), nullable=False)
    Immeuble = Column(String(3), nullable=False)   # A, B, C, BGD
    Etage = Column(String(3), nullable=False)      # 0, 00, 1-15
    DateCreation = Column(DateTime, default=datetime.utcnow)
    EstActif = Column(Boolean, default=True)

    tickets = relationship("Ticket", back_populates="user")
    chat_conversations = relationship("ChatConversation", back_populates="user", cascade="all, delete-orphan")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")


class Ticket(Base):
    __tablename__ = "Tickets"

    TicketId = Column(Integer, primary_key=True, index=True)
    UserId = Column(Integer, ForeignKey("Users.UserId"), nullable=False)
    TypeProbleme = Column(String(100), nullable=False)
    Description = Column(Text, nullable=False)
    Statut = Column(String(20), default="Ouvert")
    Priorite = Column(String(20), default="Normale")

    NomDemandeur = Column(String(100), nullable=False)
    PrenomDemandeur = Column(String(100), nullable=False)
    Immeuble = Column(String(3), nullable=False)
    Etage = Column(String(3), nullable=False)

    OrigineCreation = Column(String(20), default="Chatbot")
    ConversationId = Column(String(255), nullable=True)

    DateCreation = Column(DateTime, default=datetime.utcnow)
    DateMaJ = Column(DateTime, default=datetime.utcnow)
    AgentAssigne = Column(String(100), nullable=True)

    user = relationship("User", back_populates="tickets")
    historique = relationship("TicketHistorique", back_populates="ticket", cascade="all, delete-orphan")
    FichierUrl = Column(String(500), nullable=True)
    FichierNomOriginal = Column(String(255), nullable=True)


class ChatConversation(Base):
    __tablename__ = "ChatConversations"

    ConversationId = Column(String(255), primary_key=True)
    UserId = Column(Integer, ForeignKey("Users.UserId"), nullable=False)
    DateDebut = Column(DateTime, default=datetime.utcnow)
    DateFin = Column(DateTime, nullable=True)
    NombreEchanges = Column(Integer, default=0)
    Resolue = Column(Boolean, default=False)
    TicketIdGenere = Column(Integer, ForeignKey("Tickets.TicketId"), nullable=True)

    user = relationship("User", back_populates="chat_conversations")
    messages = relationship("ChatMessage", back_populates="conversation", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "ChatMessages"

    MessageId = Column(Integer, primary_key=True, index=True)
    ConversationId = Column(String(255), ForeignKey("ChatConversations.ConversationId"), nullable=False)
    Emetteur = Column(String(20), nullable=False)  # 'user' ou 'bot'
    Contenu = Column(Text, nullable=False)
    DateEnvoi = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("ChatConversation", back_populates="messages")

    FichierUrl = Column(String(500), nullable=True)
    FichierNomOriginal = Column(String(255), nullable=True)


class PasswordResetToken(Base):
    __tablename__ = "PasswordResetTokens"

    TokenId = Column(Integer, primary_key=True, index=True)
    UserId = Column(Integer, ForeignKey("Users.UserId"), nullable=False)
    Token = Column(String(255), unique=True, nullable=False)
    DateExpiration = Column(DateTime, nullable=False)
    Utilise = Column(Boolean, default=False)
    DateCreation = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="password_reset_tokens")


class TicketHistorique(Base):
    __tablename__ = "TicketHistorique"

    HistoId = Column(Integer, primary_key=True, index=True)
    TicketId = Column(Integer, ForeignKey("Tickets.TicketId"), nullable=False)
    Action = Column(String(255), nullable=False)
    Commentaire = Column(Text, nullable=True)
    DateAction = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="historique")
