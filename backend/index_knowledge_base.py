
from app.services.knowledge_base import construire_knowledge_base


if __name__ == "__main__":
    nombre = construire_knowledge_base()

    print(f"Indexation terminée : {nombre} chunks.")

