import os
from fastapi import FastAPI, Request, HTTPException
from typing import Dict
from litellm import Router
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Assuming GROQ_API_KEY is set in environment variables
groq_api_key = os.environ.get("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("GROQ_API_KEY environment variable not set")

# Define a router with Groq
router = Router(model_list=[
    {
        "model_name": "groq/llama2-70b-4096",  # Example Groq model
        "provider": "groq",
        "litellm_params": {
            "model": "groq/llama2-70b-4096",
            "api_key": groq_api_key,
            "api_base": "https://api.groq.com/openai/v1"
        }
    }
])

@app.post("/v1/chat/completions")
async def create_chat_completion(request: Request) -> Dict:
    """
    Endpoint to create chat completions, mimicking the OpenAI API and using LiteLLM to route to Groq.
    """
    try:
        json_data = await request.json()
        response = await router.acompletion(
            model="groq/llama2-70b-4096",  # Specify the Groq model with provider
            messages=json_data.get("messages", [])
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002, reload=True)