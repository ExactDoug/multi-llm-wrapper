# LiteLLM Proxy Server

A standardized OpenAI-compatible proxy server providing quick access to any LiteLLM-supported provider. Designed for rapid testing, tool integration, and providing OpenAI API compatibility for various LLM providers.

## Key Use Cases

1. **Rapid Testing**
   - Quick testing of different LLM providers
   - Model output comparison
   - API functionality verification

2. **Tool Integration**
   - Backend for CLINE/Roo-Code
   - Support for tools expecting OpenAI API format
   - Access to providers not natively supported

3. **Development Support**
   - Local development environment
   - Integration testing
   - Provider switching without code changes

## Quick Start

1. **Environment Setup**
```bash
# Copy example config
cp config.yaml.example config.yaml

# Configure your API keys in .env
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
GROQ_API_KEY=your_key
GEMINI_API_KEY=your_key
PERPLEXITY_API_KEY=your_key
```

2. **Start Server**
```bash
python proxy.py
```
Server runs on `http://localhost:8010`

3. **Usage Example**
```python
import openai
openai.api_base = "http://localhost:8010/v1"
openai.api_key = "not-needed"  # Proxy handles authentication

response = openai.ChatCompletion.create(
    model="claude-3-sonnet-20240229",  # Any configured model
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## Configuration

### Model Setup (config.yaml)
```yaml
model_list:
  # OpenAI Models
  - model_name: gpt-4
    litellm_params:
      model: gpt-4
      api_key: ${OPENAI_API_KEY}

  # Anthropic Models
  - model_name: claude-3-sonnet-20240229
    litellm_params:
      model: claude-3-sonnet-20240229
      api_key: ${ANTHROPIC_API_KEY}

  # Add other models as needed
```

### Environment Settings
```env
LITELLM_PROXY_PORT=8010  # Optional, defaults to 8010
```

## API Endpoints

### Chat Completions
```http
POST /v1/chat/completions
Content-Type: application/json

{
    "model": "claude-3-sonnet-20240229",
    "messages": [
        {"role": "user", "content": "Hello!"}
    ],
    "stream": false,
    "temperature": 0.7
}
```

### List Models
```http
GET /models
```

### Health Check
```http
GET /health
```

## Testing

### Basic Health Check
```bash
curl http://localhost:8010/health
```

### Test Completion
```bash
curl http://localhost:8010/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-sonnet-20240229",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## Error Handling

Standard HTTP status codes:
- 400: Bad Request (invalid parameters)
- 401: Unauthorized (invalid API key)
- 404: Not Found (invalid model)
- 500: Server Error (provider issues)

## Security Notes

- Designed for internal use/development
- No authentication required by default
- API keys managed by proxy
- Use appropriate network security in production

## Monitoring

Basic logging enabled:
- Request timing
- Error tracking
- Model usage
- Response status

## Support

- Check [LiteLLM documentation](https://docs.litellm.ai/)
- Open an issue in the repository
- Contact development team (dmortensen@exactpartners.com)