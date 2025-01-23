# Brave Search Knowledge Aggregator - Configuration Guide

## Environment Configuration

### Required Environment Variables

```plaintext
# Brave Search API Configuration
BRAVE_API_KEY=your_api_key_here
MAX_RESULTS_PER_QUERY=20
TIMEOUT_SECONDS=30
RATE_LIMIT=20

# Azure Configuration
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret
AZURE_TENANT_ID=005789aa-d109-48c1-b690-c157b9b7d953
AZURE_SUBSCRIPTION_ID=20cdb97a-3107-4857-88a5-81488217f327

# LLM Configuration
LLM_MODEL=gpt-4-turbo
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000
```

### Development Environment Setup

1. Create .env file:
```bash
cp .env.example .env
```

2. Configure Python Environment:
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## Azure Configuration

### Resource Group Setup
```bash
# Verify resource group
az group show --name apps-rg

# Create if doesn't exist
az group create --name apps-rg --location westus3
```

### App Service Configuration
```bash
# Create App Service Plan
az appservice plan create \
    --name brave-search-plan \
    --resource-group apps-rg \
    --sku B1 \
    --is-linux

# Create Web App
az webapp create \
    --name brave-search-aggregator \
    --resource-group apps-rg \
    --plan brave-search-plan \
    --runtime "PYTHON:3.11"
```

### Environment Variables in Azure
```bash
az webapp config appsettings set \
    --name brave-search-aggregator \
    --resource-group apps-rg \
    --settings \
        BRAVE_API_KEY="<key>" \
        MAX_RESULTS_PER_QUERY="20" \
        TIMEOUT_SECONDS="30" \
        RATE_LIMIT="20" \
        AZURE_CLIENT_ID="<id>" \
        AZURE_CLIENT_SECRET="<secret>" \
        AZURE_TENANT_ID="005789aa-d109-48c1-b690-c157b9b7d953" \
        LLM_MODEL="gpt-4-turbo" \
        LLM_TEMPERATURE="0.7" \
        LLM_MAX_TOKENS="2000"
```

## Authentication Configuration

### Azure AD Setup
1. App Registration
```bash
az ad app create \
    --display-name "Brave Search Aggregator" \
    --sign-in-audience "AzureADMyOrg" \
    --web-redirect-uris "https://brave-search-aggregator.azurewebsites.net/.auth/login/aad/callback"
```

2. Configure Authentication
```bash
az webapp auth update \
    --name brave-search-aggregator \
    --resource-group apps-rg \
    --enabled true \
    --action LoginWithAzureActiveDirectory \
    --aad-client-id "<client-id>" \
    --aad-client-secret "<client-secret>" \
    --aad-token-issuer-url "https://sts.windows.net/005789aa-d109-48c1-b690-c157b9b7d953/"
```

## Monitoring Configuration

### Application Insights
```bash
# Create Application Insights
az monitor app-insights component create \
    --app brave-search-insights \
    --location westus3 \
    --resource-group apps-rg

# Get Instrumentation Key
az monitor app-insights component show \
    --app brave-search-insights \
    --resource-group apps-rg \
    --query instrumentationKey
```

### Logging Configuration
```python
# logging_config.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'azure': {
            'class': 'opencensus.ext.azure.log_exporter.AzureLogHandler',
            'connection_string': 'InstrumentationKey={your-key}'
        },
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO'
        }
    },
    'root': {
        'handlers': ['azure', 'console'],
        'level': 'INFO'
    }
}
```

## Rate Limiting Configuration

### Brave Search API
```python
# config.py
BRAVE_SEARCH_CONFIG = {
    'max_rate': 20,  # requests per second
    'timeout': 30,   # seconds
    'max_retries': 3,
    'retry_delay': 1 # seconds
}
```

### Application Rate Limiting
```python
# rate_limiting.py
RATE_LIMIT_CONFIG = {
    'default': '100/minute',
    'authenticated': '200/minute',
    'search': '50/minute',
    'content_fetch': '30/minute'
}
```

## Content Processing Configuration

### Fetch Configuration
```python
# fetch_config.py
FETCH_CONFIG = {
    'timeout': 30,
    'max_size': 1024 * 1024,  # 1MB
    'allowed_content_types': [
        'text/html',
        'text/plain',
        'application/json'
    ],
    'max_redirects': 3
}
```

### Synthesis Configuration
```python
# synthesis_config.py
SYNTHESIS_CONFIG = {
    'max_sources': 5,
    'min_content_length': 100,
    'max_content_length': 8000,
    'reference_format': '[{index}] {title}',
    'confidence_threshold': 0.7
}
```

## Development Tools Configuration

### VSCode Settings
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

### Git Configuration
```bash
# .gitignore additions
.env
.venv
venv/
__pycache__/
*.pyc
.azure/
```

## Testing Configuration

### Pytest Configuration
```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --cov=brave_search_aggregator --cov-report=html
```

### Test Environment Variables
```plaintext
# .env.test
BRAVE_API_KEY=test_key
MAX_RESULTS_PER_QUERY=5
TIMEOUT_SECONDS=5
RATE_LIMIT=10
```

## Deployment Configuration

### GitHub Actions
```yaml
# .github/workflows/deploy.yml
name: Deploy to Azure
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Azure
        uses: azure/webapps-deploy@v2
        with:
          app-name: 'brave-search-aggregator'
          publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
```

## Maintenance Procedures

### Backup Configuration
```bash
# Enable backup
az webapp backup create \
    --resource-group apps-rg \
    --webapp-name brave-search-aggregator \
    --container-url "<storage-account-url>" \
    --backup-name initial-backup

# Configure scheduled backups
az webapp backup schedule \
    --resource-group apps-rg \
    --webapp-name brave-search-aggregator \
    --frequency 1d \
    --retain-one true \
    --container-url "<storage-account-url>"
```

### Monitoring Alerts
```bash
# Create alert rule
az monitor metrics alert create \
    --name "high-error-rate" \
    --resource-group apps-rg \
    --scopes "/subscriptions/20cdb97a-3107-4857-88a5-81488217f327/resourceGroups/apps-rg/providers/Microsoft.Web/sites/brave-search-aggregator" \
    --condition "count requests/failed > 10" \
    --window-size 5m \
    --evaluation-frequency 1m