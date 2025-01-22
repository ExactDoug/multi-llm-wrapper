from typing import AsyncGenerator, Dict
from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timedelta
import json

# Initialize FastAPI app
app = FastAPI()

# Setup static files and templates
current_dir = Path(__file__).parent
static_dir = current_dir / "static"
templates_dir = current_dir / "templates"

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
templates = Jinja2Templates(directory=str(templates_dir))

# Initialize LLMWrapper and response storage
from .wrapper import LLMWrapper
wrapper = LLMWrapper()

class ResponseStore:
    def __init__(self):
        self.responses = {}  # session_id -> {llm_index -> response}
        self.last_cleanup = datetime.now()
        
    def add_response(self, session_id: str, llm_index: int, response: str):
        """Add a response for a specific LLM in a session."""
        if session_id not in self.responses:
            self.responses[session_id] = {
                'timestamp': datetime.now(),
                'responses': {}
            }
        self.responses[session_id]['responses'][llm_index] = response
        self._cleanup()
    
    def get_responses(self, session_id: str) -> Dict[int, str]:
        """Get all responses for a session."""
        if session_id in self.responses:
            return self.responses[session_id]['responses']
        return {}
    
    def _cleanup(self):
        """Remove old sessions (older than 1 hour)."""
        current_time = datetime.now()
        if (current_time - self.last_cleanup).seconds < 3600:  # Only cleanup every hour
            return
            
        self.responses = {
            sid: data for sid, data in self.responses.items()
            if current_time - data['timestamp'] < timedelta(hours=1)
        }
        self.last_cleanup = current_time

# Initialize response store at module level
response_store = ResponseStore()

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the main web interface."""
    return templates.TemplateResponse("index.html", {"request": request})

async def stream_llm_response(llm_index: int, query: str, session_id: str) -> AsyncGenerator[str, None]:
    """Stream responses from a specific LLM."""
    complete_response = []  # Accumulate complete response
    try:
        # Map indices to specific models
        models = [
            "claude-3-opus-20240229",    # 0: Claude 3 Opus
            "claude-3-sonnet-20240229",  # 1: Claude 3 Sonnet
            "gpt-4",                     # 2: GPT-4
            "gpt-3.5-turbo"             # 3: GPT-3.5 Turbo
        ]
        
        # Validate index and get model
        if not (0 <= llm_index < len(models)):
            raise ValueError(f"Invalid LLM index: {llm_index}. Must be between 0 and {len(models)-1}")
            
        model = models[llm_index]
        
        # Stream responses
        async for chunk in wrapper.query(query, model=model, stream=True):
            if isinstance(chunk, dict):
                if chunk['status'] == 'error':
                    yield f"data: {json.dumps({'type': 'error', 'message': chunk['error']})}\n\n"
                    break
                elif chunk['status'] == 'success' and chunk.get('content'):
                    content = chunk['content']
                    complete_response.append(content)
                    yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
        
        # Store complete response and send completion messages
        if complete_response:
            response_store.add_response(session_id, llm_index, ''.join(complete_response))
            yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

@app.get("/stream/{llm_index}")
async def stream_endpoint(
    llm_index: int,
    query: str,
    session_id: str = Query(None)
):
    """Endpoint for streaming LLM responses."""
    # Generate session ID if not provided
    if not session_id:
        session_id = str(uuid4())
    
    return StreamingResponse(
        stream_llm_response(llm_index, query, session_id),
        media_type="text/event-stream"
    )

@app.get("/synthesize/{session_id}")
async def synthesize_endpoint(session_id: str):
    """Endpoint for synthesizing responses."""
    return StreamingResponse(
        stream_synthesis(session_id),
        media_type="text/event-stream"
    )

async def stream_synthesis(session_id: str) -> AsyncGenerator[str, None]:
    """Stream the synthesis of all LLM responses using Claude."""
    try:
        # Get stored responses for the session
        stored_responses = response_store.get_responses(session_id)
        if not stored_responses:
            raise ValueError("No responses found for synthesis")
            
        # Create synthesis prompt
        synthesis_prompt = "Analyze and synthesize the following AI responses:\n\n"
        for idx, response in sorted(stored_responses.items()):
            model_name = ["Claude 3 Opus", "Claude 3 Sonnet", "GPT-4", "GPT-3.5 Turbo"][idx]
            synthesis_prompt += f"=== {model_name} Response ===\n{response}\n\n"
        
        synthesis_prompt += "\nProvide a comprehensive synthesis that:\n"
        synthesis_prompt += "1. Compares and contrasts the different responses\n"
        synthesis_prompt += "2. Identifies key agreements and disagreements\n"
        synthesis_prompt += "3. Evaluates the strengths of each response\n"
        
        # Stream synthesis using Claude
        async for chunk in wrapper.query(
            synthesis_prompt,
            model="claude-3-opus-20240229",
            stream=True
        ):
            if isinstance(chunk, dict):
                if chunk['status'] == 'error':
                    yield f"data: {json.dumps({'type': 'error', 'message': chunk['error']})}\n\n"
                    break
                elif chunk['status'] == 'success' and chunk.get('content'):
                    yield f"data: {json.dumps({'type': 'content', 'content': chunk['content']})}\n\n"
        
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"