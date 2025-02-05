import asyncio
import subprocess
import sys
import time
import os
from pathlib import Path

async def main():
    # Start the web server
    server_process = subprocess.Popen(
        [sys.executable, "-m", "multi_llm_wrapper.web.run"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    try:
        # Wait for server to start
        print("Starting web server...")
        time.sleep(2)  # Give the server time to start
        
        # Run the test
        print("Running test...")
        test_process = subprocess.run(
            [sys.executable, "test_groq_proxy.py"],
            capture_output=True,
            text=True
        )
        
        # Print test output
        print("\nTest output:")
        print(test_process.stdout)
        if test_process.stderr:
            print("\nTest errors:")
            print(test_process.stderr)
            
    finally:
        # Clean up
        print("\nStopping web server...")
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    asyncio.run(main())