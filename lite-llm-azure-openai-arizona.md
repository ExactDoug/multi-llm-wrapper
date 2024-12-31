# Using LiteLLM with Azure OpenAI in Arizona 3

This document outlines how to use the `lite-llm` Python library to interface with Microsoft Azure OpenAI, specifically targeting the Arizona 3 region.

## Prerequisites

*   Python installed
*   `pip` package installer
*   Azure account with access to Azure OpenAI service
*   Azure OpenAI deployment in the Arizona 3 region (West US 3)

## Installation

Install the `liteLLM` library with the proxy extras:

```bash
pip install 'litellm[proxy]' 'litellm[extra_proxy]'
```

## Azure Credentials

You need to configure your Azure credentials as environment variables. Obtain the following from your Azure portal:

*   `AZURE_CLIENT_ID`: Your Azure application client ID.
*   `AZURE_CLIENT_SECRET`: Your Azure application client secret.
*   `AZURE_TENANT_ID`: Your Azure tenant ID.
*   `AZURE_API_KEY`: Your Azure OpenAI API key for the Arizona 3 deployment.
*   `AZURE_API_BASE`: The base URL for your Azure OpenAI deployment in Arizona 3. This will follow the format: `https://<your-resource-name>.openai.azure.com/`.
*   `AZURE_API_VERSION`: The API version to use (e.g., `2023-05-15preview`).

Set these as environment variables:

```bash
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"
export AZURE_TENANT_ID="your-tenant-id"
export AZURE_API_KEY="your-api-key"
export AZURE_API_BASE="https://<your-resource-name>.openai.azure.com/"
export AZURE_API_VERSION="2023-05-15preview"
```

**Note on Arizona 3 Region:** Ensure your `AZURE_API_BASE` is pointed to your Azure OpenAI resource deployed in the **West US 3** region.

## LiteLLM Configuration

Create a `config.yaml` file to configure LiteLLM. Here's an example for using the `gpt-3.5-turbo` model deployed in Azure:

```yaml
model_list:
  - model_name: azure-gpt-35-turbo # A name you choose
    litellm_params:
      model: azure/gpt-35-turbo # Specify the Azure model
      api_base: os.environ/AZURE_API_BASE
      api_key: os.environ/AZURE_API_KEY
      api_version: os.environ/AZURE_API_VERSION
```

## Running the LiteLLM Proxy

Start the LiteLLM proxy server using your configuration file:

```bash
litellm --config /path/to/your/config.yaml
```

## Making Requests

You can now use the OpenAI Python SDK to make requests through the LiteLLM proxy. Make sure your `base_url` points to the proxy:

```python
import openai

client = openai.OpenAI(
    api_key="anything",  # Not used when using a proxy
    base_url="http://0.0.0.0:4000"  # Default proxy address
)

response = client.chat.completions.create(
    model="azure-gpt-35-turbo", # Use the model_name from your config.yaml
    messages=[
        {"role": "user", "content": "Write a short poem about Arizona."}
    ]
)

print(response.choices[0].message.content)
```

By following these steps, you can successfully use the `lite-llm` library to interact with your Azure OpenAI deployment in the Arizona 3 region. Remember to replace placeholder values with your actual Azure credentials and deployment details.