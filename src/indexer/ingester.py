import logging
from tqdm import tqdm
from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.node_parser import MarkdownNodeParser, TokenTextSplitter

from config.config import Config
from config.config_rag import ConfigRag
from indexer.db.db_admin import DBAdmin
from indexer.loaders.doc_loader import DocumentLoader

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

class Ingester:
    def __init__(self, db_admin: DBAdmin, doc_loader: DocumentLoader):
        self.db_admin = db_admin
        self.doc_loader = doc_loader
    
    def ingest(self):
        self.db_admin.clean_db()
        
        embed_model = ConfigRag.get_embedding_model()
        check_dim = len(embed_model.get_text_embedding("try me"))
        if check_dim != Config.EMBEDDING_DIM:
            raise ValueError(f"Embedding dimension mismatch! Expected {Config.EMBEDDING_DIM}, got {check_dim}")
        
        documents = self.doc_loader.load_documents(Config.MD_DIR, '.md')
        
        for doc in tqdm(documents, desc="Processing documents", unit="doc"):
            first_line = doc.text.split('\n')[0] if doc.text else ""
            if first_line.startswith("# Source:"):
                doc.metadata['doc_source'] = first_line.replace("# Source:", "").strip()
        
        Settings.embed_model = embed_model
        vector_store = ConfigRag.get_vector_store()
        
        md_parser = MarkdownNodeParser(include_metadata=True, include_prev_next_rel=True)
        nodes = md_parser.get_nodes_from_documents(documents)
        
        for i, node in enumerate(tqdm(nodes, desc="Adding metadata", unit="node")):
            if not hasattr(node, 'metadata') or not node.metadata:
                node.metadata = {}
            node.metadata['page_number'] = i + 1
        
        text_splitter = TokenTextSplitter(chunk_size=1000, chunk_overlap=200, separator=" ")
        split_nodes = text_splitter.get_nodes_from_documents(nodes)
        
        index = VectorStoreIndex.from_vector_store(vector_store=vector_store, embed_model=Settings.embed_model)
        
        with tqdm(total=len(split_nodes), desc="Writing chunks", unit="chunks") as pbar:
            for i in range(0, len(split_nodes), 50):
                batch = split_nodes[i:i+50]
                index.insert_nodes(batch)
                pbar.update(len(batch))
        
        self.db_admin.check_index_in_db()

if __name__ == "__main__":
    Ingester(DBAdmin(), DocumentLoader()).ingest()