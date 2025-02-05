# LiteLLM Proxy Server

A standardized OpenAI-compatible proxy server providing quick access to multiple LLM providers. Designed for rapid testing, tool integration, and API compatibility across providers.

## Key Use Cases

1. **Rapid Testing**
   - Compare outputs across providers
   - Verify API compatibility
   - Test new models quickly

2. **Tool Integration**
   - Compatible with OpenAI clients
   - Supports CLI tools like Roo-Code
   - Enables provider-agnostic workflows

3. **Development Support**
   - Local development environment
   - Provider switching without code changes
   - Centralized API key management

## Quick Start

1. **Environment Setup**
```bash
cp config.yaml.example config.yaml
```

2. **Configure API Keys**
```env
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
GROQ_API_KEY=your_key
GEMINI_API_KEY=your_key
PERPLEXITY_API_KEY=your_key
```

3. **Start Server**
```bash
python proxy.py
```
Server runs on `http://localhost:8010`

## API Endpoints

### Chat Completions
```http
POST /v1/chat/completions
Content-Type: application/json

{
  "model": "gpt-4",
  "messages": [{"role": "user", "content": "Hello!"}],
  "stream": false,
  "temperature": 0.7
}
```

### List Models
```http
GET /v1/models
```

### Health Check
```http
GET /health
```

## Configuration

### Model Setup (config.yaml)
```yaml
model_list:
  - model_name: gpt-4
    litellm_params:
      model: gpt-4
      api_key: ${OPENAI_API_KEY}
  - model_name: claude-3-sonnet-20240229
    litellm_params:
      model: claude-3-sonnet-20240229
      api_key: ${ANTHROPIC_API_KEY}
  - model_name: mixtral-8x7b-32768
    litellm_params:
      model: groq/mixtral-8x7b-32768
      api_key: ${GROQ_API_KEY}
  - model_name: sonar-small
    litellm_params:
      model: perplexity/llama-3.1-sonar-small-128k-online
      api_key: ${PERPLEXITY_API_KEY}
  - model_name: gemini-1.5-flash
    litellm_params:
      model: gemini/gemini-1.5-flash
      api_key: ${GEMINI_API_KEY}
```

### Environment Settings
```env
LITELLM_PROXY_PORT=8010  # Defaults to 8010
```

## Error Handling

Standard HTTP status codes:
- 400: Invalid parameters
- 401: Authentication failure
- 404: Model not found
- 500: Server error

## Security Notes

- Environment variables handle API keys
- No default authentication
- Use HTTPS in production
- Monitor network access

## Monitoring

- Request timing
- Error tracking
- Model usage analytics
- Response status logging

## Support

- [LiteLLM Documentation](https://docs.litellm.ai/)
- Open an issue
- Contact: dmortensen@exactpartners.com