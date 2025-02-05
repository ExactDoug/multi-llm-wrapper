from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from litellm import Router
from litellm.exceptions import AuthenticationError  # To handle errors from providers
import os
from typing import Optional, Dict, Any
import yaml
from pydantic import BaseModel
import logging
from dotenv import load_dotenv
import json  # For JSON serialization
from pathlib import Path # To obtain the API keys since the .env is in the parent directory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Find and load the .env file from the parent directory
env_path = Path(__file__).resolve().parent.parent / '.env'
if env_path.exists():
    logger.info(f"Loading .env from: {env_path}")
    load_dotenv(env_path)
else:
    logger.warning(f".env file not found at: {env_path}")

# After loading .env file, environment variable debug (remove for production)
for key in ["PERPLEXITY_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GROQ_API_KEY", "GEMINI_API_KEY"]:
    value = os.getenv(key)
    if value:
        logger.info(f"{key} is set with length: {len(value)}")
    else:
        logger.warning(f"{key} is not set!")

app = FastAPI()

# Load config from yaml (with debug logging)
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    if os.path.exists(config_path):
        logger.info(f"Loading config from: {config_path}")
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
            # Expand environment variables in API keys
            for model in config.get("model_list", []):
                if "api_key" in model.get("litellm_params", {}):
                    model["litellm_params"]["api_key"] = os.path.expandvars(model["litellm_params"]["api_key"])
            return config
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
    try:
        kwargs = {
            "model": request.model,
            "messages": request.messages,
            "stream": request.stream
        }
        
        if request.temperature is not None:
            kwargs["temperature"] = request.temperature
        if request.max_tokens is not None:
            kwargs["max_tokens"] = request.max_tokens
            
        if request.stream:
            # Existing streaming code
            async def generate():
                try:
                    async for chunk in await router.acompletion(**kwargs):
                        if chunk and hasattr(chunk, "model_dump"):
                            yield f"data: {json.dumps(chunk.model_dump())}\n\n"
                        else:
                            yield f"data: {json.dumps(chunk)}\n\n"
                except AuthenticationError as auth_err:
                    error_response = {
                        "error": {
                            "message": f"Authentication failed: {str(auth_err)}",
                            "type": "auth_error"
                        }
                    }
                    yield f"data: {json.dumps(error_response)}\n\n"
                except Exception as e:
                    error_response = {
                        "error": {
                            "message": str(e),
                            "type": "stream_error"
                        }
                    }
                    yield f"data: {json.dumps(error_response)}\n\n"
                finally:
                    yield "data: [DONE]\n\n"

            return StreamingResponse(generate(), media_type="text/event-stream")
            
        # Non-streaming response
        response = await router.acompletion(**kwargs)
        if hasattr(response, "model_dump"):
            return JSONResponse(content=response.model_dump())
        return JSONResponse(content=response)
        
    except AuthenticationError as auth_err:
        logger.error(f"Authentication error: {str(auth_err)}")
        raise HTTPException(status_code=401, detail={
            "error": {
                "message": f"Authentication failed: {str(auth_err)}",
                "type": "auth_error"
            }
        })
    except Exception as e:
        logger.error(f"Error in chat completion: {str(e)}")
        raise HTTPException(status_code=500, detail={
            "error": {
                "message": str(e),
                "type": "server_error"
            }
        })

@app.get("/v1/models")
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