from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from agents.tools.conversation import ConversationTool
from agents.tools.reranker import RerankerTool
from retriever.retriever import Retriever


class RetrieverRerankerInput(BaseModel):
    query: str = Field(description="User query to search")
    chat_id: str = Field(description="Chat session ID")


class RetrieverRerankerTool(BaseTool):
    name: str = "retriever_reranker"
    description: str = "Retrieve relevant documents using chat context memory"
    args_schema: type[BaseModel] = RetrieverRerankerInput
    
    def _run(self, query: str, chat_id: str) -> str:
        retriever = Retriever()
        retrieved = retriever.search(query)
        
        reranker = RerankerTool()
        reranked = reranker._run(documents=retrieved)
        
        return reranked
