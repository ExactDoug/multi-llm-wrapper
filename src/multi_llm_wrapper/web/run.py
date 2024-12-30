import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from multi_llm_wrapper.web.app import app

def main():
    """
    Run the Multi-LLM Web Interface
    
    This script starts the FastAPI server with the following configuration:
    - Host: 0.0.0.0 (accessible from all network interfaces)
    - Port: From environment variable PORT or default 8000
    - Reload: True in development (when DEBUG=True in env)
    """
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    print(f"Starting Multi-LLM Web Interface on port {port}")
    print("Debug mode:", "enabled" if debug else "disabled")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        reload=debug,
        workers=1,  # For SSE support, we use 1 worker
        log_level="info"
    )

if __name__ == "__main__":
    main()