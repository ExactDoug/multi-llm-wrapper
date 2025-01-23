# Brave Search Knowledge Aggregator - Configuration Guide

## Environment Configuration

### Required Environment Variables

```plaintext
# Brave Search API Configuration (MVP)
BRAVE_API_KEY=your_api_key_here
MAX_RESULTS_PER_QUERY=20
TIMEOUT_SECONDS=30
RATE_LIMIT=20

# Azure Configuration
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret
AZURE_TENANT_ID=005789aa-d109-48c1-b690-c157b9b7d953
AZURE_SUBSCRIPTION_ID=20cdb97a-3107-4857-88a5-81488217f327

# LLM Configuration (Advanced Features)
LLM_MODEL=gpt-4-turbo
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000
```

### Feature Flag Configuration
```plaintext
# Feature Flags (in .env)
FEATURE_ADVANCED_SYNTHESIS=false    # Enable advanced synthesis features
FEATURE_PARALLEL_PROCESSING=true    # Enable parallel processing (MVP)
FEATURE_MOE_ROUTING=false          # Enable MoE routing (advanced)
FEATURE_TASK_VECTORS=false         # Enable task vectors (advanced)
FEATURE_SLERP_MERGING=false        # Enable SLERP merging (advanced)
```

### Configuration Models

#### Feature Flags Model
```python
from pydantic import BaseModel, Field

class TestFeatureFlags(BaseModel):
    """Test-specific feature flag configuration."""
    advanced_synthesis: bool = Field(
        default=False,
        description="Enable advanced synthesis features"
    )
    parallel_processing: bool = Field(
        default=True,
        description="Enable parallel processing of search results"
    )
    moe_routing: bool = Field(
        default=False,
        description="Enable mixture of experts routing"
    )
    task_vectors: bool = Field(
        default=False,
        description="Enable task vector support"
    )
    slerp_merging: bool = Field(
        default=False,
        description="Enable SLERP-based vector merging"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "advanced_synthesis": False,
                    "parallel_processing": True,
                    "moe_routing": False,
                    "task_vectors": False,
                    "slerp_merging": False
                }
            ]
        }
    }
```

#### Server Configuration Model
```python
class TestServerConfig(BaseModel):
    """Test server configuration settings."""
    # Server settings
    host: str = Field(default="0.0.0.0", description="Server host address")
    port: int = Field(default=8001, description="Server port number")
    reload: bool = Field(default=True, description="Enable auto-reload")
    workers: int = Field(default=1, description="Number of worker processes")
    log_level: str = Field(default="debug", description="Logging level")
    
    # Brave Search API settings
    brave_api_key: str = Field(default="", description="Brave Search API key")
    max_results_per_query: int = Field(
        default=20,
        description="Maximum results per query"
    )
    timeout_seconds: int = Field(
        default=30,
        description="API timeout in seconds"
    )
    rate_limit: int = Field(default=20, description="API rate limit")

    # Feature flags
    features: TestFeatureFlags = Field(
        default_factory=TestFeatureFlags,
        description="Feature flag configuration"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "host": "0.0.0.0",
                    "port": 8001,
                    "reload": True,
                    "workers": 1,
                    "log_level": "debug",
                    "brave_api_key": "your-api-key-here",
                    "max_results_per_query": 20,
                    "timeout_seconds": 30,
                    "rate_limit": 20,
                    "features": {
                        "advanced_synthesis": False,
                        "parallel_processing": True,
                        "moe_routing": False,
                        "task_vectors": False,
                        "slerp_merging": False
                    }
                }
            ]
        }
    }
```

### Development Environment Setup

1. Create .env file:
```bash
cp .env.example .env
```

2. Configure Python Environment:
```powershell
# Activate virtual environment
& C:\dev\venvs\multi-llm-wrapper\Scripts\Activate.ps1

# Install dependencies
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
        FEATURE_ADVANCED_SYNTHESIS="false" \
        FEATURE_PARALLEL_PROCESSING="true" \
        FEATURE_MOE_ROUTING="false" \
        FEATURE_TASK_VECTORS="false" \
        FEATURE_SLERP_MERGING="false"
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

### Brave Search API (MVP)
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

### Fetch Configuration (MVP)
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

# MVP Configuration
BASIC_SYNTHESIS_CONFIG = {
    'max_sources': 5,
    'min_content_length': 100,
    'max_content_length': 8000,
    'reference_format': '[{index}] {title}'
}

# Advanced Features Configuration (When Enabled)
ADVANCED_SYNTHESIS_CONFIG = {
    **BASIC_SYNTHESIS_CONFIG,
    'confidence_threshold': 0.7,
    'moe_routing_threshold': 0.8,
    'task_vector_dimensions': 768,
    'slerp_interpolation_steps': 10
}
```

## Development Tools Configuration

### VSCode Settings
```json
{
    "python.defaultInterpreterPath": "C:\\dev\\venvs\\multi-llm-wrapper\\Scripts\\python.exe",
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
FEATURE_ADVANCED_SYNTHESIS=false
FEATURE_PARALLEL_PROCESSING=true
FEATURE_MOE_ROUTING=false
FEATURE_TASK_VECTORS=false
FEATURE_SLERP_MERGING=false
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
```

### Feature Flag Management
```python
# feature_flags.py
class FeatureFlags:
    @staticmethod
    def is_enabled(feature_name: str) -> bool:
        """Check if a feature is enabled."""
        return os.getenv(f"FEATURE_{feature_name.upper()}", "false").lower() == "true"

    @staticmethod
    def get_enabled_features() -> List[str]:
        """Get list of all enabled features."""
        return [
            key.replace("FEATURE_", "").lower()
            for key, value in os.environ.items()
            if key.startswith("FEATURE_") and value.lower() == "true"
        ]