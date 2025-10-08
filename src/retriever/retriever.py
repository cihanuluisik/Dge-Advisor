import logging
from config.config_rag import ConfigRag
from llama_index.core import Settings, VectorStoreIndex

logger = logging.getLogger(__name__)

class Retriever:
    def __init__(self):
        self._setup_vector_store()
    
    def _setup_vector_store(self):
        try:
            Settings.embed_model = ConfigRag.get_embedding_model()
            Settings.llm = None
            vector_store = ConfigRag.get_vector_store()
            index = VectorStoreIndex.from_vector_store(
                vector_store=vector_store, 
                embed_model=Settings.embed_model
            )
            self.query_engine = index.as_query_engine(
                vector_store_query_mode="hybrid",
                llm=None,
                similarity_top_k=2,
                sparse_top_k=1,
                response_mode="no_text"
            )
        except Exception as e:
            logger.error(f"Failed to setup vector store: {e}")
            raise
    
    def search(self, query: str, min_score: float = 0.5) -> str:
        if not self.query_engine:
            raise ValueError("Vector store not initialized")
        
        response = self.query_engine.query(query)
        filtered_nodes = [n for n in response.source_nodes if n.score >= min_score]
        
        formatted_chunks = []
        for node in filtered_nodes:
            metadata = node.node.metadata if hasattr(node.node, 'metadata') else {}
            doc_name = metadata.get('doc_source') or metadata.get('file_name', 'Unknown Document')
            page_number = metadata.get('page_label', metadata.get('page_number', 'N/A'))
            
            formatted_chunks.append(
                f"--- Source Document ---\n"
                f"Document: {doc_name}\n"
                f"Page: {page_number}\n"
                f"Relevance Score: {node.score:.3f}\n"
                f"Content: {node.node.text}\n\n"
            )
        
        return "".join(formatted_chunks)