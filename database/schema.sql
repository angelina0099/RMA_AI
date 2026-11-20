/* =========================================================
   RMA Helpdesk - Schema SQL Server
   ========================================================= */

IF DB_ID('RMA_Helpdesk') IS NULL
BEGIN
    CREATE DATABASE RMA_Helpdesk;
END
GO

USE RMA_Helpdesk;
GO

-- ==================== UTILISATEURS ====================
-- Drop child tables first (in reverse dependency order)
IF OBJECT_ID('dbo.ChatMessages', 'U') IS NOT NULL DROP TABLE dbo.ChatMessages;
GO
IF OBJECT_ID('dbo.ChatConversations', 'U') IS NOT NULL DROP TABLE dbo.ChatConversations;
GO
IF OBJECT_ID('dbo.TicketHistorique', 'U') IS NOT NULL DROP TABLE dbo.TicketHistorique;
GO
IF OBJECT_ID('dbo.PasswordResetTokens', 'U') IS NOT NULL DROP TABLE dbo.PasswordResetTokens;
GO
IF OBJECT_ID('dbo.Tickets', 'U') IS NOT NULL DROP TABLE dbo.Tickets;
GO
IF OBJECT_ID('dbo.Users', 'U') IS NOT NULL DROP TABLE dbo.Users;
GO

-- Create tables in parent-to-child order
CREATE TABLE dbo.Users (
    UserId          INT IDENTITY(1,1) PRIMARY KEY,
    Nom             NVARCHAR(100) NOT NULL,
    Prenom          NVARCHAR(100) NOT NULL,
    Email           NVARCHAR(255) NOT NULL UNIQUE,
    PasswordHash    NVARCHAR(255) NOT NULL,
    Immeuble        CHAR(3) NOT NULL,
    Etage           VARCHAR(3) NOT NULL,
    DateCreation    DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    EstActif        BIT NOT NULL DEFAULT 1,

    CONSTRAINT CK_Users_Immeuble
        CHECK (Immeuble IN ('A', 'B', 'C', 'BGD')),

    CONSTRAINT CK_Users_Etage
        CHECK (Etage IN (
            '0','00','1','2','3','4','5','6','7','8','9',
            '10','11','12','13','14','15'
        ))
);
GO

-- ============== REINITIALISATION MOT DE PASSE ==============
CREATE TABLE dbo.PasswordResetTokens (
    TokenId         INT IDENTITY(1,1) PRIMARY KEY,
    UserId          INT NOT NULL FOREIGN KEY REFERENCES dbo.Users(UserId),
    Token           NVARCHAR(255) NOT NULL UNIQUE,
    DateExpiration  DATETIME2 NOT NULL,
    Utilise         BIT NOT NULL DEFAULT 0,
    DateCreation    DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

-- ==================== TICKETS ====================
CREATE TABLE dbo.Tickets (
    TicketId            INT IDENTITY(1,1) PRIMARY KEY,
    UserId              INT NOT NULL FOREIGN KEY REFERENCES dbo.Users(UserId),
    TypeProbleme        NVARCHAR(100) NOT NULL,
    Description         NVARCHAR(MAX) NOT NULL,
    Statut              NVARCHAR(20) NOT NULL DEFAULT 'Ouvert',
    Priorite            NVARCHAR(20) NOT NULL DEFAULT 'Normale',
    NomDemandeur        NVARCHAR(100) NOT NULL,
    PrenomDemandeur     NVARCHAR(100) NOT NULL,
    Immeuble            CHAR(3) NOT NULL,
    Etage               VARCHAR(3) NOT NULL,
    OrigineCreation     NVARCHAR(20) NOT NULL DEFAULT 'Chatbot',
    ConversationId      NVARCHAR(255) NULL,
    DateCreation        DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    DateMaJ             DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    AgentAssigne        NVARCHAR(100) NULL,

    CONSTRAINT CK_Tickets_Etage
        CHECK (Etage IN (
            '0','00','1','2','3','4','5','6','7','8','9',
            '10','11','12','13','14','15'
        ))
);
GO

-- ==================== HISTORIQUE / SUIVI DES TICKETS ====================
CREATE TABLE dbo.TicketHistorique (
    HistoId         INT IDENTITY(1,1) PRIMARY KEY,
    TicketId        INT NOT NULL FOREIGN KEY REFERENCES dbo.Tickets(TicketId),
    Action          NVARCHAR(255) NOT NULL,
    Commentaire     NVARCHAR(MAX) NULL,
    DateAction      DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

-- ==================== CONVERSATIONS CHATBOT ====================
CREATE TABLE dbo.ChatConversations (
    ConversationId      NVARCHAR(255) PRIMARY KEY,
    UserId              INT NOT NULL FOREIGN KEY REFERENCES dbo.Users(UserId),
    DateDebut           DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    DateFin             DATETIME2 NULL,
    NombreEchanges      INT NOT NULL DEFAULT 0,
    Resolue             BIT NOT NULL DEFAULT 0,
    TicketIdGenere      INT NULL FOREIGN KEY REFERENCES dbo.Tickets(TicketId)
);
GO

CREATE TABLE dbo.ChatMessages (
    MessageId       INT IDENTITY(1,1) PRIMARY KEY,
    ConversationId  NVARCHAR(255) NOT NULL FOREIGN KEY REFERENCES dbo.ChatConversations(ConversationId),
    Emetteur        NVARCHAR(20) NOT NULL,
    Contenu         NVARCHAR(MAX) NOT NULL,
    DateEnvoi       DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

-- ==================== INDEX UTILES ====================
CREATE INDEX IX_Tickets_UserId ON dbo.Tickets(UserId);
CREATE INDEX IX_Tickets_Statut ON dbo.Tickets(Statut);
CREATE INDEX IX_ChatMessages_ConversationId ON dbo.ChatMessages(ConversationId);
GO
ALTER TABLE ChatMessages 
ADD FichierUrl NVARCHAR(500) NULL,
    FichierNomOriginal NVARCHAR(255) NULL;
    
 ALTER TABLE Tickets 
ADD FichierUrl NVARCHAR(500) NULL;

ALTER TABLE Tickets 
ADD FichierNomOriginal NVARCHAR(255) NULL;