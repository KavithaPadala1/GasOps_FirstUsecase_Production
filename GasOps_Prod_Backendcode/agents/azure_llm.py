

## azure multi client setup

from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv
import os
import threading
# from keyvaultsecret import (
#     AZURE_OPENAI_ENDPOINT,
#     AZURE_OPENAI_API_VERSION,
#     AZURE_OPENAI_DEPLOYMENT,
#     AZURE_OPENAI_API_KEY,
#     AZURE_OPENAI_ENDPOINT2,
#     AZURE_OPENAI_DEPLOYMENT2,
#     AZURE_OPENAI_API_KEY2,
#     AZURE_OPENAI_ENDPOINT3,
#     AZURE_OPENAI_DEPLOYMENT3,
#     AZURE_OPENAI_API_KEY3
# )

# Load environment variables from .env file
load_dotenv()

 

# Initialize both AzureChatOpenAI clients
llm_clients = [
    AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        temperature=1
    ),
    AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT2"),
        openai_api_version= os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT2"),
        openai_api_key=os.getenv("AZURE_OPENAI_API_KEY2"),
        temperature=1
    ),
    AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT3"),
        openai_api_version= os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT3"),
        openai_api_key=os.getenv("AZURE_OPENAI_API_KEY3"),
        temperature=1
    )
]

# Global index and lock for round-robin client access
_client_index = 0
_client_lock = threading.Lock()

# use get_next_llm_client() to get a client for each request

def load_azureopenai_llm_client():
    """
    Returns the next AzureChatOpenAI client in round-robin fashion for load balancing.
    Thread-safe for concurrent requests.
    Logs the user question being processed.
    """
    global _client_index
    with _client_lock:
        client = llm_clients[_client_index]
        print(f"[Azure LLM] Using client {_client_index}: endpoint={client.azure_endpoint}, deployment={getattr(client, 'deployment_name', 'N/A')}")
        _client_index = (_client_index + 1) % len(llm_clients)
    return client



# from langchain_openai import AzureChatOpenAI
# import threading
# from keyvaultsecret import (
#     AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_VERSION,
#     AZURE_OPENAI_DEPLOYMENT, AZURE_OPENAI_API_KEY,
#     AZURE_OPENAI_ENDPOINT2, AZURE_OPENAI_DEPLOYMENT2, AZURE_OPENAI_API_KEY2,
#     AZURE_OPENAI_ENDPOINT3, AZURE_OPENAI_DEPLOYMENT3, AZURE_OPENAI_API_KEY3,
# )

# configs = [
#     (AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT, AZURE_OPENAI_API_KEY),
#     (AZURE_OPENAI_ENDPOINT2, AZURE_OPENAI_DEPLOYMENT2, AZURE_OPENAI_API_KEY2),
#     (AZURE_OPENAI_ENDPOINT3, AZURE_OPENAI_DEPLOYMENT3, AZURE_OPENAI_API_KEY3),
# ]

# llm_clients = [
#     AzureChatOpenAI(
#         azure_endpoint=endpoint,
#         openai_api_version=AZURE_OPENAI_API_VERSION,
#         azure_deployment=deployment,
#         openai_api_key=api_key,
#         temperature=1,
#     )
#     for endpoint, deployment, api_key in configs
# ]

# _index = 0
# _lock = threading.Lock()

# def load_azureopenai_llm_client():
#     global _index
#     with _lock:
#         client = llm_clients[_index]
#         print(f"[Azure LLM] Using client {_index}: endpoint={client.azure_endpoint}")
#         _index = (_index + 1) % len(llm_clients)
#     return client
