from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from typing import Optional
from uuid import uuid4
import json
import logging
from .service import LLMService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# Setup static files and templates
current_dir = Path(__file__).parent
static_dir = current_dir / "static"
templates_dir = current_dir / "templates"

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
templates = Jinja2Templates(directory=str(templates_dir))

# Initialize LLM service
# Service initialization always succeeds now - individual providers handle their own errors
llm_service = LLMService()

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the main web interface."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get('/favicon.ico')
async def favicon():
    """Serve favicon.ico from static directory."""
    return FileResponse(static_dir / 'favicon.ico')

@app.get('/apple-touch-icon{suffix:path}.png')
async def apple_touch_icon(suffix: str = ""):
    """Serve apple-touch-icon.png files with fallback."""
    # Try specific file first, then fall back to default
    specific_file = static_dir / f'apple-touch-icon{suffix}.png'
    default_file = static_dir / 'apple-touch-icon.png'
    return FileResponse(specific_file if specific_file.exists() else default_file)

@app.get("/api/status")
async def get_status():
    """Report service availability status"""
    return {
        "llm_service_available": True,
        "error": None,
        "message": "Service ready - individual providers available based on API key configuration"
    }

# Helper function for error streaming
async def error_generator(message: str):
    """Generate error message in streaming format"""
    yield f"data: {json.dumps({'type': 'error', 'message': message, 'code': 'SERVICE_UNAVAILABLE'})}\n\n"
    yield f"data: {json.dumps({'type': 'done'})}\n\n"

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
        llm_service.stream_llm_response(llm_index, query, session_id),
        media_type="text/event-stream"
    )

@app.get("/synthesize/{session_id}")
async def synthesize_endpoint(session_id: str):
    """Endpoint for synthesizing responses."""
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID is required")
        
    return StreamingResponse(
        llm_service.stream_synthesis(session_id),
        media_type="text/event-stream"
    )

from litellm import acompletion

@app.post("/groq/v1/completions")
async def groq_completions(request: Request):
    """Direct Groq API endpoint"""
    return await handle_groq_request(request)

@app.post("/groq-proxy/v1/completions")
async def groq_proxy_completions(request: Request):
    """Groq proxy endpoint"""
    return await handle_groq_request(request, base_url="http://localhost:8001")

async def handle_groq_request(request: Request, base_url: Optional[str] = None):
    """Handle Groq API requests with optional proxy support"""
    try:
        data = await request.json()
        
        # Extract and validate model name
        model = data.get("model")
        if not model:
            # Only use default if no model specified
            model = "llama2-70b-8192"
            logger.info(f"No model specified, using default model: {model}")
        elif model.startswith("groq/"):
            # Remove 'groq/' prefix if present
            model = model[5:]
            logger.debug(f"Removed 'groq/' prefix from model name: {model}")
            
        # Validate required fields
        if "messages" not in data:
            raise HTTPException(
                status_code=400,
                detail="Field 'messages' is required"
            )
            
        completion_args = {
            "model": model,
            "messages": data["messages"],
            # Only include optional params if they exist
            **({k: v for k, v in {
                "temperature": data.get("temperature"),
                "max_tokens": data.get("max_tokens")
            }.items() if v is not None})
        }
        
        # Add base_url if provided
        if base_url:
            completion_args["base_url"] = base_url
            logger.debug(f"Using base URL: {base_url}")
            
        # Send completion request
        logger.info(f"Sending completion request for model: {model}")
        try:
            response = await acompletion(**completion_args)
        except Exception as e:
            logger.error(f"Completion request failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Completion request failed: {str(e)}")

        logger.debug("Completion request successful")
        
        # Format the response
        try:
            formatted_response = {
                "id": "cmpl-" + str(uuid4()),
                "object": "text_completion",
                "created": int(response['created']),
                "choices": [
                    {
                        "text": response['choices'][0]['message']['content'],
                        "index": 0,
                        "logprobs": None,
                        "finish_reason": response['choices'][0]['finish_reason']
                    }
                ],
                "usage": {
                    "prompt_tokens": response['usage']['prompt_tokens'],
                    "completion_tokens": response['usage']['completion_tokens'],
                    "total_tokens": response['usage']['total_tokens']
                }
            }
        except (KeyError, TypeError, IndexError) as e:
            logger.error(f"Failed to format response: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Invalid response format from completion API: {str(e)}"
            )

        logger.info(f"Request completed successfully. Total tokens: {formatted_response['usage']['total_tokens']}")
        return formatted_response
            
    except ValueError as e:
        logger.error(f"Invalid request data: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in handle_groq_request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)