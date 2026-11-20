"""
Service Groq pour le chatbot Helpdesk RMA.

Règles :
- Une seule solution à la fois.
- Les étapes sont toujours ligne par ligne.
- Le ticket n'est jamais créé par Groq.
- Le bouton de ticket est géré par FastAPI après 4 échecs.
"""

import base64
import importlib
import unicodedata

try:
    _groq = importlib.import_module("groq")
    Groq = getattr(_groq, "Groq", None)
except ImportError:
    Groq = None

from ..database import settings


# ============================================================
# CLIENT GROQ
# ============================================================

client = None

if Groq is not None:
    client = Groq(
        api_key=settings.GROQ_API_KEY
    )


# ============================================================
# MODELES
# ============================================================

MODELE_TEXTE = "openai/gpt-oss-120b"
MODELE_VISION = "qwen/qwen3.6-27b"


# ============================================================
# CONFIGURATION
# ============================================================

# Nombre d'échecs avant d'autoriser le bouton ticket.
SEUIL_ECHECS_AVANT_TICKET = 4


# ============================================================
# PROMPT SYSTEME
# ============================================================

PROMPT_SYSTEME = """
INTENTION DE L'UTILISATEUR :

Si l'utilisateur demande :
- "quel est le problème ?"
- "c'est quoi le problème ?"
- "quel est le problème sur la photo ?"
- "qu'est-ce que tu vois ?"
- "analyse la photo"
- "quelle est la cause ?"

Alors NE DONNE PAS de solution.

Réponds uniquement avec :
Problème identifié : [description claire du problème]

Cause probable : [cause si elle peut être déterminée]

Ne donne aucune étape de résolution dans cette réponse.

Si l'utilisateur demande comment résoudre le problème, alors seulement :
Solution : [une seule solution]

1. ...
2. ...
3. ...

Chaque étape doit être sur une ligne différente.
Tu es l'assistant Helpdesk IT de premier niveau de la compagnie RMA.

TON OBJECTIF :
Aider l'utilisateur à résoudre son problème informatique étape par étape.

REGLES ABSOLUES :

1. Donne UNE SEULE solution technique par réponse.

2. Ne donne jamais plusieurs solutions dans la même réponse.

3. Les étapes doivent toujours être numérotées.

4. Chaque étape doit être sur une ligne séparée.

5. Les étapes doivent être courtes, simples et directement exécutables.

6. Après les étapes, arrête-toi et attends la réponse de l'utilisateur.

7. Si l'utilisateur indique que la solution ne fonctionne pas,
   propose une AUTRE solution technique.

8. Ne répète jamais exactement la même solution.

9. Ne donne pas plusieurs procédures en avance.

10. Ne donne jamais une liste de plusieurs solutions.

11. N'écris jamais "Solution 1", "Solution 2", "Solution 3", etc.
    Utilise simplement :

    Solution : [titre]

12. Si une image ou un fichier est fourni, utilise les informations
    visibles dans le fichier pour comprendre le problème.

13. Ne demande pas inutilement à l'utilisateur de décrire une image
    si le problème peut être compris directement à partir de celle-ci.

14. Si l'image permet d'identifier un problème, donne directement
    une première action de résolution.

15. Ne prétends jamais avoir effectué une action que tu n'as pas effectuée.

FORMAT OBLIGATOIRE :

Solution : [titre court]

1. Première action.

2. Deuxième action.

3. Troisième action.

Puis arrête ta réponse.

IMPORTANT :
Chaque étape doit être sur sa propre ligne.

MAUVAIS FORMAT :

Solution : Vérifier le câble
1. Vérifiez le câble. 2. Vérifiez le projecteur. 3. Redémarrez le PC.

BON FORMAT :

Solution : Vérifier le câble

1. Vérifiez que le câble HDMI est correctement branché au PC.

2. Vérifiez que l'autre extrémité est correctement branchée au projecteur.

3. Testez un autre câble HDMI si possible.

Puis arrête-toi.

============================================================
GESTION DES ECHECS
============================================================

Un échec signifie que l'utilisateur indique que la solution précédente
n'a pas fonctionné.

Exemples :

- non
- toujours pas
- ne marche pas
- ça marche pas
- ca marche pas
- pas résolu
- pas resolu
- problème persiste
- probleme persiste
- ça n'a pas marché
- ca n'a pas marche
- ça ne marche toujours pas
- ca ne marche toujours pas
- ça fonctionne pas
- ca fonctionne pas
- ça ne fonctionne pas
- ca ne fonctionne pas

Lorsqu'un utilisateur indique un échec :

- ne demande pas immédiatement de créer un ticket ;
- ne dis pas que le ticket est créé ;
- propose une nouvelle solution technique ;
- ne répète pas la solution précédente.

============================================================
GESTION DES TICKETS
============================================================

IMPORTANT :

Tu ne crées JAMAIS de ticket.

Tu ne dois JAMAIS écrire :

"Le ticket a bien été créé."

"Votre ticket a été créé."

"Numéro du ticket."

"RMA-IT-..."

"Vous recevrez un e-mail."

"Le ticket sera envoyé au Helpdesk."

Tu ne dois jamais inventer de numéro de ticket.

La création du ticket est entièrement gérée par l'application.

L'application peut afficher un bouton de création de ticket
après avoir détecté suffisamment d'échecs.

Tu ne dois jamais prétendre qu'un ticket existe.

============================================================
STYLE
============================================================

Langue : français.

Style :
- professionnel ;
- clair ;
- direct ;
- court ;
- aucune phrase inutile ;
- une seule solution ;
- étapes numérotées ;
- une étape par ligne.

Ne donne jamais plusieurs solutions dans une seule réponse.
"""


# ============================================================
# MOTS INDIQUANT UN ECHEC
# ============================================================

MOTS_NON_RESOLU = [
    "non",
    "toujours pas",
    "ne marche pas",
    "ça marche pas",
    "ca marche pas",
    "pas resolu",
    "pas résolu",
    "probleme persiste",
    "problème persiste",
    "ça n'a pas marché",
    "ca n'a pas marche",
    "ça ne marche toujours pas",
    "ca ne marche toujours pas",
    "toujours le meme probleme",
    "toujours le même problème",
    "ça fonctionne pas",
    "ca fonctionne pas",
    "ça ne fonctionne pas",
    "ca ne fonctionne pas",
]


# ============================================================
# NORMALISATION
# ============================================================

def normaliser_texte(texte: str) -> str:
    """
    Convertit le texte en minuscules et supprime les accents.
    """

    texte = texte.lower().strip()

    texte = unicodedata.normalize(
        "NFD",
        texte
    )

    texte = "".join(
        caractere
        for caractere in texte
        if unicodedata.category(caractere) != "Mn"
    )

    return texte


# ============================================================
# DETECTION ECHEC
# ============================================================

def message_indique_non_resolu(texte: str) -> bool:
    """
    Retourne True si le message indique
    que la solution précédente n'a pas fonctionné.
    """

    if not texte:
        return False

    texte_normalise = normaliser_texte(texte)

    mots_normalises = [
        normaliser_texte(mot)
        for mot in MOTS_NON_RESOLU
    ]

    return any(
        mot in texte_normalise
        for mot in mots_normalises
    )


# ============================================================
# COMPTER LES ECHECS
# ============================================================

def compter_echecs(historique_messages: list[dict]) -> int:
    """
    Compte uniquement les messages utilisateur
    indiquant un échec.
    """

    compteur = 0

    for message in historique_messages:

        if message.get("role") != "user":
            continue

        contenu = message.get("content", "")

        if not isinstance(contenu, str):
            continue

        if message_indique_non_resolu(contenu):
            compteur += 1

    return compteur


# ============================================================
# AUTORISER LE TICKET
# ============================================================

def doit_proposer_ticket(
    historique_messages: list[dict],
) -> bool:
    """
    Le ticket est autorisé uniquement après 4 échecs.
    """

    nombre_echecs = compter_echecs(
        historique_messages
    )

    return nombre_echecs >= SEUIL_ECHECS_AVANT_TICKET


# ============================================================
# GENERER REPONSE TEXTE
# ============================================================

def generer_reponse(
    historique_messages: list[dict],
) -> str:
    """
    Génère une réponse avec une seule solution.
    """

    if client is None:
        raise RuntimeError(
            "Le client Groq n'est pas disponible."
        )

    messages = [
        {
            "role": "system",
            "content": PROMPT_SYSTEME,
        }
    ]

    messages.extend(historique_messages)

    completion = client.chat.completions.create(
        model=MODELE_TEXTE,
        messages=messages,
        temperature=0.2,
        max_tokens=400,
    )

    return (
        completion
        .choices[0]
        .message
        .content
        .strip()
    )


# ============================================================
# ANALYSE IMAGE
# ============================================================

def analyser_image(
    image_bytes: bytes,
    mime_type: str,
    texte_utilisateur: str | None = None,
) -> str:
    """
    Analyse une image avec le modèle vision.

    IMPORTANT :
    On demande directement une piste de résolution.
    On ne demande pas inutilement à l'utilisateur
    de décrire l'image.
    """

    if client is None:
        raise RuntimeError(
            "Le client Groq n'est pas disponible."
        )

    image_b64 = base64.b64encode(
        image_bytes
    ).decode("utf-8")

    data_url = (
        f"data:{mime_type};base64,{image_b64}"
    )

    if texte_utilisateur:
        question = f"""
Analyse cette image dans le contexte du support informatique.

Message de l'utilisateur :
{texte_utilisateur}

Identifie le problème visible et donne UNE SEULE solution
ou piste technique à essayer.

Ne demande pas simplement à l'utilisateur de décrire l'image
si tu peux déjà identifier le problème.

Respecte strictement le format :

Solution : [titre]

1. Première action.

2. Deuxième action.

3. Troisième action.
"""
    else:
        question = """
Analyse cette image dans le contexte du support informatique.

Identifie le problème visible.

Donne UNE SEULE solution technique à essayer.

Ne demande pas à l'utilisateur de décrire l'image
si le problème peut être identifié directement.

Respecte strictement le format :

Solution : [titre]

1. Première action.

2. Deuxième action.

3. Troisième action.
"""

    completion = client.chat.completions.create(
        model=MODELE_VISION,
        messages=[
            {
                "role": "system",
                "content": PROMPT_SYSTEME,
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": question,
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": data_url,
                        },
                    },
                ],
            },
        ],
        temperature=0.2,
        max_tokens=400,
    )

    return (
        completion
        .choices[0]
        .message
        .content
        .strip()
    )