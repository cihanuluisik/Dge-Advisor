from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Union, List, Dict, Any

class RerankerInput(BaseModel):
    documents: Union[str, List[Dict[str, Any]]] = Field(description="Retrieved documents to re-rank")

class RerankerTool(BaseTool):
    name: str = "reranker"
    description: str = "Re-ranks retrieved documents by relevance score"
    args_schema: type[BaseModel] = RerankerInput
    
    def _run(self, documents) -> str:
        try:
            if not isinstance(documents, str):
                documents = str(documents)
            
            doc_sections = documents.split("--- Source Document")
            docs = [self._parse(s) for s in doc_sections[1:] if s.strip()]
            docs = [d for d in docs if d]
            
            if not docs:
                return "No documents found"
            
            docs.sort(key=lambda x: x['score'], reverse=True)
            top_doc = docs[0]
            
            result = f"Document: {top_doc['name']}"
            if top_doc.get('page') and top_doc['page'] != 'N/A':
                result += f"\nPage: {top_doc['page']}"
            result += f"\n\n{top_doc['content']}"
            
            return result
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _parse(self, section: str):
        doc = {}
        lines = section.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('Document:'):
                doc['name'] = line.replace('Document:', '').strip()
            elif line.startswith('Page:'):
                doc['page'] = line.replace('Page:', '').strip()
            elif line.startswith('Relevance Score:'):
                try:
                    doc['score'] = float(line.replace('Relevance Score:', '').strip())
                except (ValueError, TypeError):
                    doc['score'] = 0.0
            elif line.startswith('Content:'):
                content_start = section.find('Content:')
                if content_start != -1:
                    doc['content'] = section[content_start + 8:].strip()
        
        return doc if all(k in doc for k in ['name', 'content', 'score']) else None
