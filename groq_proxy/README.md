# Groq Proxy Server (Deprecated)

A simple OpenAI API-compatible proxy specifically for Groq LLM services. Note: This component is being phased out in favor of the more versatile LiteLLM Proxy.

## Status

⚠️ **DEPRECATED**: We recommend using the LiteLLM Proxy (`/litellm_proxy`) instead, which provides:
- Support for multiple providers including Groq
- More robust implementation
- Better maintenance
- Additional features

## Current Functionality

- OpenAI API compatibility for Groq models
- Basic async support
- Simple configuration
- Error handling
- Health checks

## Configuration

1. Environment Setup:
   ```bash
   export GROQ_API_KEY=your_key_here
   ```

2. Model Configuration (config.yaml):
   ```yaml
   model_list:
     - model_name: groq-llama3-8b-8192
       litellm_params:
         model: groq/llama3-8b-8192
         api_key: ${GROQ_API_KEY}
   ```

## Usage

1. Start server:
   ```bash
   python groq_proxy.py
   ```
   Server runs on http://localhost:8002

2. Use like OpenAI API:
   ```python
   import openai
   openai.api_base = "http://localhost:8002/v1"
   openai.api_key = "not-needed"
   
   response = openai.ChatCompletion.create(
       model="groq/llama3-8b-8192",
       messages=[{"role": "user", "content": "Hello!"}]
   )
   ```

## Testing

Run the test suite:
```bash
python run_groq_proxy_test.py
```

## Migration Guide

To migrate to the LiteLLM Proxy:

1. Use the LiteLLM Proxy server instead:
   ```bash
   cd ../litellm_proxy
   python proxy.py
   ```

2. Update your API base URL:
   ```python
   # Old
   openai.api_base = "http://localhost:8002/v1"
   
   # New
   openai.api_base = "http://localhost:8010/v1"
   ```

3. Configure Groq models in `litellm_proxy/config.yaml`

## Support

For any issues:
1. Consider migrating to the LiteLLM Proxy
2. Open an issue in the repository if needed
3. Contact the development team