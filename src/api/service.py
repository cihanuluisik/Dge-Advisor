import os, sys, uuid, json, logging, re
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
from phoenix.otel import register

from agents.crew import PolicyCrew
from api.request_response import ChatCompletionRequest

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

phoenix_host = os.getenv("PHOENIX_HOST", "host.docker.internal")
phoenix_endpoint = f"http://{phoenix_host}:6006"
os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = phoenix_endpoint
tracer_provider = register(
    project_name="default",
    endpoint=f"{phoenix_endpoint}/v1/traces",
    auto_instrument=True
)
logging.info(f"Phoenix tracing initialized at {phoenix_endpoint}")

app = FastAPI(title="Policy RAG API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

crew_instance = PolicyCrew()

def extract_pga4_session_from_cookie(cookie_header: str) -> str:
    if not cookie_header:
        return None
    match = re.search(r'pga4_session=([^;]+)', cookie_header)
    if match:
        session_value = match.group(1).strip('"')
        if '!' in session_value:
            session_value = session_value.split('!')[0]
        return session_value
    return None


@app.post("/v1/chat/completions")
async def chat_completions(body: ChatCompletionRequest, request: Request):
    try:
        cookie_header = request.headers.get("cookie", "")
        pga4_session = extract_pga4_session_from_cookie(cookie_header)
        chat_id = pga4_session or body.chat_id or f"chat_{uuid.uuid4().hex[:16]}"
        
        logging.info(f"chat_id: {chat_id}, stream: {body.stream}")
        
        user_message = next((m.content for m in reversed(body.messages) if m.role == "user"), None)
        if not user_message:
            raise HTTPException(status_code=400, detail="No user message found")
        
        flow_inputs = {'query': user_message, 'chat_id': chat_id}
        response_id = f"chatcmpl-{uuid.uuid4().hex[:29]}"
        created_timestamp = int(datetime.now().timestamp())
        
        def generate_stream():
            result = crew_instance.crew().kickoff(inputs=flow_inputs)
            response_text = result.raw if hasattr(result, 'raw') and result.raw else str(result)
            
            data = {
                "id": response_id,
                "object": "chat.completion.chunk",
                "created": created_timestamp,
                "model": body.model,
                "choices": [{
                    "index": 0,
                    "delta": {"role": "assistant", "content": response_text}
                }]
            }
            yield f"data: {json.dumps(data)}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/v1/models")
async def get_models():
    return {
        "object": "list",
        "data": [{
            "id": "dge-policy-rag",
            "object": "model",
            "created": 1690000000,
            "owned_by": "organization",
            "permission": [],
            "root": "dge-policy-rag",
            "parent": None,
            "max_tokens": 131072,
            "context_length": 131072,
            "capabilities": {"completion": True, "chat_completion": True}
        }]
    }


if __name__ == "__main__":
    port = int(os.getenv("RAG_API_PORT"))
    uvicorn.run(app, host="0.0.0.0", port=port)