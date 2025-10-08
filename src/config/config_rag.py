import os
from dotenv import load_dotenv
from llama_index.embeddings.ollama import OllamaEmbedding
from config.config import Config
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.storage.docstore.postgres import PostgresDocumentStore

load_dotenv()

class ConfigRag:
    __embed_model = OllamaEmbedding(
        model_name=Config.EMBEDDING_MODEL_NAME,
        base_url=Config.OLLAMA_BASE_URL,
    )

    __vector_store = PGVectorStore.from_params(
        database=Config.DNAME, 
        host=Config.DHOST, 
        port=Config.DPORT, 
        user=Config.DUSER, 
        password=Config.DPASSWORD,
        embed_dim=Config.EMBEDDING_DIM,
        hybrid_search=True,
        text_search_config="english",
        hnsw_kwargs={
            "hnsw_m": 24,
            "hnsw_ef_construction": 128,
            "hnsw_ef_search": 64,
            "hnsw_dist_method": "vector_cosine_ops"
        }
    )

    __docstore = PostgresDocumentStore.from_params(
        database=Config.DNAME,
        host=Config.DHOST,
        port=Config.DPORT,
        user=Config.DUSER,
        password=Config.DPASSWORD,
    )

    @classmethod
    def get_embedding_model(cls):
        return cls.__embed_model

    @classmethod
    def get_vector_store(cls):
        return cls.__vector_store
    
    @classmethod
    def get_docstore(cls):
        return cls.__docstore
