from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from litellm import Router
import os
from typing import Optional, Dict, Any
import yaml
from pydantic import BaseModel
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Load config from yaml
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    return {"model_list": []}

# Initialize router with config
router = Router(model_list=load_config().get("model_list", []))

class CompletionRequest(BaseModel):
    model: str
    messages: list
    stream: Optional[bool] = False
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None

@app.post("/v1/chat/completions")
async def chat_completion(request: CompletionRequest):
    """Generic chat completion endpoint that supports any provider configured in the router."""
    try:
        # Extract parameters from request
        kwargs = {
            "model": request.model,
            "messages": request.messages,
            "stream": request.stream
        }
        
        # Add optional parameters if provided
        if request.temperature is not None:
            kwargs["temperature"] = request.temperature
        if request.max_tokens is not None:
            kwargs["max_tokens"] = request.max_tokens
            
        # Handle streaming
        if request.stream:
            return StreamingResponse(
                router.acompletion(**kwargs),
                media_type="text/event-stream"
            )
            
        # Handle non-streaming
        response = await router.acompletion(**kwargs)
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"Error in chat completion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models")
async def list_models():
    """List all available models from the configuration."""
    try:
        config = load_config()
        return {
            "models": [
                {
                    "id": model["model_name"],
                    "provider": model.get("litellm_params", {}).get("provider", "unknown")
                }
                for model in config["model_list"]
            ]
        }
    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("LITELLM_PROXY_PORT", "8010"))
    uvicorn.run(app, host="0.0.0.0", port=port)