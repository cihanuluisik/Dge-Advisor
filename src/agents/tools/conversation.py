from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, Any
import psycopg2

from config.config import Config
from indexer.db.db_admin import DBAdmin

class ConversationInput(BaseModel):
    chat_id: str = Field(description="Chat session ID to retrieve or store messages")
    message: Optional[str] = Field(default=None, description="Message to store (leave empty to only retrieve)")
    role: str = Field(default="user", description="Message role: user or assistant")
    limit: int = Field(default=3, description="Number of recent messages to retrieve")

class ConversationTool(BaseTool):
    name: str = "conversation"
    description: str = """Retrieve conversation history from database. 
    Call this to get recent messages from the conversation to understand context.
    Example: conversation(chat_id='chat_123', limit=3) returns last 3 messages."""
    args_schema: type[BaseModel] = ConversationInput
    default_chat_id: Optional[str] = Field(default=None, exclude=True)
    
    def __init__(self, chat_id: Optional[str] = None):
        super().__init__()
        self.default_chat_id = chat_id
    
    def _run(self, chat_id: str, message: Optional[str] = None, role: str = "user", limit: int = 3) -> str:
        try:
            context = self.get_conversation_context(chat_id, limit=limit)
            
            if message:
                DBAdmin.execute_query([
                    ("INSERT INTO chat_sessions (chat_id) VALUES (%s) ON CONFLICT (chat_id) DO NOTHING", 
                     (chat_id,)),
                    ("INSERT INTO chat_messages (chat_id, message, role) VALUES (%s, %s, %s)",
                     (chat_id, message, role))
                ])
                return f"{context}\n{role}: {message}" if context != "No conversation history found" else f"{role}: {message}"
            
            return context
            
        except Exception as e:
            return f"Error: {str(e)}"
        
    def store_assistant_response(self, response: str) -> str:
        try:
            DBAdmin.execute_query([
                ("INSERT INTO chat_messages (chat_id, message, role) VALUES (%s, %s, %s)",
                 (self.default_chat_id, response, 'assistant'))
            ])
            return "Stored"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def get_conversation_context(self, chat_id: str, limit: int = 10) -> str:
        results = DBAdmin.execute_query([
            ("SELECT role, message FROM chat_messages WHERE chat_id = %s ORDER BY created_at DESC LIMIT %s",
             (chat_id, limit))
        ], fetch=True)
        messages = results[0] if results else []
        return "\n".join(f"{role}: {msg}" for role, msg in reversed(messages)) or "No conversation history found"
