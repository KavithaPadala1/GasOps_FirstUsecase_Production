# from azure.identity import DefaultAzureCredential
# from azure.keyvault.secrets import SecretClient

# # Define your Key Vault URL
# key_vault_url = "https://gasops-prod-ai-keyvault.vault.azure.net"

# # Authenticate using Managed Identity
# credential = DefaultAzureCredential()

# # Create a SecretClient
# secret_client = SecretClient(vault_url=key_vault_url, credential=credential)

# # Retrieve secrets (match names from your Key Vault configuration)

# # Azure OpenAI 1
# AZURE_OPENAI_ENDPOINT = secret_client.get_secret("AZUREOPENAIENDPOINT").value
# AZURE_OPENAI_API_KEY = secret_client.get_secret("AZUREOPENAIAPIKEY").value
# AZURE_OPENAI_DEPLOYMENT = secret_client.get_secret("AZUREOPENAIDEPLOYMENT").value
# AZURE_OPENAI_MODEL_NAME = secret_client.get_secret("AZUREOPENAIMODELNAME").value
# AZURE_OPENAI_API_VERSION = secret_client.get_secret("AZUREOPENAIAPIVERSION").value

# # Azure OpenAI 2
# AZURE_OPENAI_ENDPOINT2 = secret_client.get_secret("AZUREOPENAIENDPOINT2").value
# AZURE_OPENAI_API_KEY2 = secret_client.get_secret("AZUREOPENAIAPIKEY2").value
# AZURE_OPENAI_DEPLOYMENT2 = secret_client.get_secret("AZUREOPENAIDEPLOYMENT2").value

# # Azure OpenAI 3
# AZURE_OPENAI_ENDPOINT3 = secret_client.get_secret("AZUREOPENAIENDPOINT3").value
# AZURE_OPENAI_API_KEY3 = secret_client.get_secret("AZUREOPENAIAPIKEY3").value
# AZURE_OPENAI_DEPLOYMENT3 = secret_client.get_secret("AZUREOPENAIDEPLOYMENT3").value

# # Azure AI Search
# AZURE_SEARCH_API_VERSION = secret_client.get_secret("AZURESEARCHAPIVERSION").value
# AZURE_SEARCH_DEPLOYMENT = secret_client.get_secret("AZURESEARCHDEPLOYMENT").value
# AZURE_SEARCH_ENDPOINT = secret_client.get_secret("AZURESEARCHENDPOINT").value
# AZURE_SEARCH_KEY = secret_client.get_secret("AZURESEARCHKEY").value

# # Database credentials
# SERVER = secret_client.get_secret("SERVER").value
# DATABASE_OAMSCM = secret_client.get_secret("DATABASEOAMSCM").value
# USERNAME = secret_client.get_secret("USERNAME").value
# PASSWORD = secret_client.get_secret("PASSWORD").value

# # Example usage
# print(f"OpenAI Endpoint 1: {AZURE_OPENAI_ENDPOINT}")
# print(f"OpenAI Key 1: {AZURE_OPENAI_API_KEY}")
# print(f"Database Connection: Server={SERVER}, DB={DATABASE_OAMSCM}, User={USERNAME}")