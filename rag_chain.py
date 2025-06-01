from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.vector_stores.chroma import ChromaVectorStore
from langchain.chat_models import ChatOpenAI
from chromadb import PersistentClient
from dotenv import load_dotenv
import os

# Charger les variables d'environnement
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Vérification
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY non trouvé dans .env")

# Initialiser le modèle LLM
llm = ChatOpenAI(
    temperature=0.3,
    openai_api_key=OPENAI_API_KEY
)

# Configuration du dossier de persistance
PERSIST_DIR = "vectorstore/chroma"
COLLECTION_NAME = "island_docs"

def generate_project_ideas():
    # Créer un client local Chroma persistant
    chroma_client = PersistentClient(path=PERSIST_DIR)

    # Obtenir ou créer la collection
    collection = chroma_client.get_or_create_collection(COLLECTION_NAME)

    # Créer un vector store avec la collection directement (contourne le bug)
    vector_store = ChromaVectorStore(chroma_collection=collection)

    # Créer le contexte de stockage
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # Vérifier si la collection est vide
    if len(collection.get()['ids']) == 0:
        print("⚠️ Vector store vide. Construction à partir des documents...")
        documents = SimpleDirectoryReader("data/documents").load_data()
        parser = SimpleNodeParser()
        nodes = parser.get_nodes_from_documents(documents)

        index = VectorStoreIndex(nodes, storage_context=storage_context)
        index.storage_context.persist()
    else:
        print("✅ Chargement depuis la base vectorielle existante...")
        index = VectorStoreIndex.from_vector_store(vector_store, storage_context=storage_context)

    # Interroger l'index
    query_engine = index.as_query_engine(llm=llm)
    response = query_engine.query("Generate 5 project ideas for island resilience.")
    return str(response)

if __name__ == "__main__":
    print(generate_project_ideas())
