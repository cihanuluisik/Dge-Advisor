import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DOCUMENTS_FOLDER = os.getenv("DOCUMENTS_FOLDER", "data/raw")
    MD_DIR = os.getenv("MD_DIR", "data/md")
    
    DHOST = os.getenv("DHOST", "localhost")
    DPORT = int(os.getenv("DPORT", "5432"))
    DNAME = os.getenv("DNAME", "ragdb")
    DUSER = os.getenv("DUSER", "user")
    DPASSWORD = os.getenv("DPASSWORD", "password")
    TABLE_NAME = os.getenv("TABLE_NAME", "data_llamaindex")
    DOCSTORE_TABLE = os.getenv("DOCSTORE_TABLE", "data_docstore")
    
    @classmethod
    def get_durl(cls):
        return f"postgresql://{cls.DUSER}:{cls.DPASSWORD}@{cls.DHOST}:{cls.DPORT}/{cls.DNAME}"
    
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL")
    EMBEDDING_DIM = int(os.getenv("EMBEDDING_MODEL_DIM"))
    LLM_MODEL_NAME = os.getenv("LLM_MODEL", "gemma3:12b")
