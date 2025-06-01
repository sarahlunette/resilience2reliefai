import os
from huggingface_hub import snapshot_download, login
from transformers import AutoTokenizer, AutoModelForCausalLM
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.huggingface import HuggingFaceLLM
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from chromadb import PersistentClient
from dotenv import load_dotenv


# Load environment variables from .env
load_dotenv()

# Optional: read from environment variable or store securely
HF_TOKEN = os.getenv("HF_TOKEN") or "your_hf_token_here"

# Log in to the Hugging Face Hub
login(token=HF_TOKEN)

# --- Configuration
HF_MODEL_NAME = "mistralai/Mistral-7B-Instruct-v0.1"
CACHE_DIR = "models/local_llm"
PERSIST_DIR = "vectorstore/chroma"
COLLECTION_NAME = "island_docs"

def ensure_model_downloaded(model_name, cache_dir):
    """Download the Hugging Face model if not already cached"""
    model_path = os.path.join(cache_dir, model_name.replace("/", "_"))
    if not os.path.exists(model_path):
        print("⬇️ Downloading model from Hugging Face...")
        snapshot_download(repo_id=model_name, cache_dir=cache_dir, local_dir=model_path, local_dir_use_symlinks=False)
    else:
        print("✅ Model already cached.")
    return model_path

def load_local_model(model_name="mistralai/Mistral-7B-Instruct-v0.1", cache_dir="./models"):
    local_folder_name = model_name.replace("/", "_")
    model_path = os.path.join(cache_dir, local_folder_name)

    if not os.path.exists(model_path):
        print(f"Téléchargement de {model_name} vers {model_path}...")
        snapshot_download(
            repo_id=model_name,
            cache_dir=cache_dir,
            local_dir=model_path,
            local_dir_use_symlinks=False
        )

    print(f"Chargement du modèle depuis {model_path}...")
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(model_path)

    return tokenizer, model

def generate_project_ideas():
    # Ensure model is downloaded
    model_path = ensure_model_downloaded(HF_MODEL_NAME, CACHE_DIR)
    tokenizer, model = load_local_model(model_path)

    llm = HuggingFaceLLM(
        context_window=3900,
        max_new_tokens=512,
        generate_kwargs={"temperature": 0.3, "do_sample": True},
        tokenizer=tokenizer,
        model=model,
        tokenizer_name=HF_MODEL_NAME,
        model_name=HF_MODEL_NAME,
        device_map="auto"
    )

    # Setup embedding model (✅ Correction here)
    embed_model = HuggingFaceEmbedding(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    # Setup Chroma vector store
    try:
        chroma_client = PersistentClient(path=PERSIST_DIR)
        collection = chroma_client.get_or_create_collection(COLLECTION_NAME)
        vector_store = ChromaVectorStore(chroma_collection=collection)
    except Exception as e:
        print("⚠️ Vector store error, deleting and rebuilding:", e)
        import shutil
        shutil.rmtree(PERSIST_DIR)
        chroma_client = PersistentClient(path=PERSIST_DIR)
        collection = chroma_client.get_or_create_collection(COLLECTION_NAME)
        vector_store = ChromaVectorStore(chroma_collection=collection)

    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    index_path = os.path.join(PERSIST_DIR, "index_store.json")
    if not os.path.exists(index_path):
        print("⚠️ Vector store not found. Building from scratch...")
        documents = SimpleDirectoryReader("data/documents").load_data()
        parser = SimpleNodeParser()
        nodes = parser.get_nodes_from_documents(documents)
        index = VectorStoreIndex(nodes, storage_context=storage_context, embed_model=embed_model)
        index.storage_context.persist()
    else:
        print("✅ Loading from existing vector store...")
        index = VectorStoreIndex.from_vector_store(vector_store, storage_context=storage_context, embed_model=embed_model)

    # Query the index
    query_engine = index.as_query_engine(llm=llm)
    response = query_engine.query("Generate 5 project ideas for island resilience.")
    return str(response)

if __name__ == "__main__":
    print(generate_project_ideas())
