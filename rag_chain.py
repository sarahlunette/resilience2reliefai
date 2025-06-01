from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from langchain.chat_models import ChatOpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.storage.vector_stores.chroma import ChromaVectorStore
from llama_index.storage.storage_context import StorageContext

llm = ChatOpenAI(temperature=0.3)

def generate_project_ideas():
    docs = SimpleDirectoryReader("data/documents").load_data()
    storage_context = StorageContext.from_defaults(persist_dir="vectorstore/chroma")
    vector_index = VectorStoreIndex.from_documents(docs, storage_context=storage_context)

    query_engine = vector_index.as_query_engine(llm=llm)
    response = query_engine.query("How can this disaster be used to rebuild with more resilience?")
    return {"project_ideas": response.response}
