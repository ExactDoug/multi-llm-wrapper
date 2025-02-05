from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from uuid import uuid4
from .service import LLMService

# Initialize FastAPI app
app = FastAPI()

# Setup static files and templates
current_dir = Path(__file__).parent
static_dir = current_dir / "static"
templates_dir = current_dir / "templates"

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
templates = Jinja2Templates(directory=str(templates_dir))

# Initialize LLM service
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)