from pathlib import Path

try:
    import chromadb  # type: ignore
except Exception:  # pragma: no cover - handle missing package during lint/type checks
    chromadb = None
try:
    from docx import Document  # type: ignore
except Exception:  # pragma: no cover - handle missing package during lint/type checks
    Document = None

try:
    from sentence_transformers import SentenceTransformer  # type: ignore
except Exception:  # pragma: no cover - handle missing package during lint/type checks
    SentenceTransformer = None


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DOCUMENTS_DIR = BASE_DIR / "knowledge_base" / "documents"
CHROMA_DIR = BASE_DIR / "knowledge_base" / "chroma_db"

COLLECTION_NAME = "rma_knowledge_base"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


# ---------------------------------------------------------
# Embedding model
# ---------------------------------------------------------

if SentenceTransformer is not None:
    embedding_model = SentenceTransformer(
        "sentence-transformers/all-MiniLM-L6-v2"
    )
else:
    embedding_model = None


# ---------------------------------------------------------
# ChromaDB
# ---------------------------------------------------------

if chromadb is not None:
    chroma_client = chromadb.PersistentClient(
        path=str(CHROMA_DIR)
    )

    collection = chroma_client.get_or_create_collection(
        name=COLLECTION_NAME
    )
else:
    chroma_client = None
    collection = None


# ---------------------------------------------------------
# Read DOCX
# ---------------------------------------------------------

def lire_docx(path: Path) -> str:
    if Document is None:
        raise RuntimeError(
            "python-docx is not installed. Install with: pip install python-docx"
        )

    document = Document(path)

    paragraphs = []

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()

        if text:
            paragraphs.append(text)

    return "\n".join(paragraphs)


# ---------------------------------------------------------
# Split text
# ---------------------------------------------------------

def decouper_texte(
    texte: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[str]:

    chunks = []

    start = 0
    text_length = len(texte)

    while start < text_length:

        end = start + chunk_size

        chunk = texte[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


# ---------------------------------------------------------
# Build knowledge base
# ---------------------------------------------------------

def construire_knowledge_base() -> int:

    DOCUMENTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    documents = list(DOCUMENTS_DIR.glob("*.docx"))

    if not documents:
        print(
            f"Aucun document Word trouvé dans : {DOCUMENTS_DIR}"
        )

        return 0

    if chroma_client is None or collection is None:
        raise RuntimeError(
            "chromadb is not available. Install chromadb and restart."
        )

    all_chunks = []
    all_ids = []
    all_metadatas = []

    counter = 0

    for document_path in documents:

        print(f"Lecture : {document_path.name}")

        texte = lire_docx(document_path)

        if not texte.strip():
            print(
                f"Document vide ignoré : {document_path.name}"
            )
            continue

        chunks = decouper_texte(texte)

        for index, chunk in enumerate(chunks):

            chunk_id = f"{document_path.stem}_{index}_{counter}"

            all_chunks.append(chunk)
            all_ids.append(chunk_id)

            all_metadatas.append(
                {
                    "source": document_path.name,
                    "chunk": index,
                }
            )

            counter += 1

    if not all_chunks:
        return 0

    if embedding_model is None:
        raise RuntimeError(
            "sentence-transformers is not available. Install sentence-transformers."
        )

    print(f"Création des embeddings pour {len(all_chunks)} chunks...")

    embeddings = embedding_model.encode(all_chunks).tolist()

    collection.add(
        ids=all_ids,
        documents=all_chunks,
        embeddings=embeddings,
        metadatas=all_metadatas,
    )

    print(
        f"Knowledge base créée : "
        f"{len(all_chunks)} chunks"
    )

    return len(all_chunks)


# ---------------------------------------------------------
# Search knowledge base
# ---------------------------------------------------------

def rechercher_knowledge_base(
    question: str,
    nombre_resultats: int = 5,
) -> list[dict]:

    if collection.count() == 0:
        return []

    question_embedding = embedding_model.encode(
        [question]
    ).tolist()[0]

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=min(
            nombre_resultats,
            collection.count(),
        ),
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    resultat = []

    for document, metadata in zip(
        documents,
        metadatas,
    ):
        resultat.append(
            {
                "text": document,
                "source": metadata.get("source"),
            }
        )

    return resultat
