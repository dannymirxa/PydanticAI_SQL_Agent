from openai import AsyncAzureOpenAI, AzureOpenAI
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from pydantic_ai.providers.openai import OpenAIProvider

from dotenv import load_dotenv
import os

load_dotenv('.env')

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")

# GEMINI_MODEL = GeminiModel('gemini-2.0-flash', provider=GoogleGLAProvider(api_key=GEMINI_API_KEY))

async_client = AsyncAzureOpenAI(
    azure_endpoint = "https://llmcoechangemateopenai2.openai.azure.com/",
    api_key=AZURE_OPENAI_KEY,
    api_version="2024-10-21",
    azure_deployment='gpt-4o'
)

OPENAI_MODEL = OpenAIModel(
    'gpt-4o-dev',
    provider=OpenAIProvider(openai_client=async_client),
)

client = AzureOpenAI(
    azure_endpoint = "https://llmcoechangemateopenai2.openai.azure.com/",
    api_key=AZURE_OPENAI_KEY,
    api_version="2024-10-21",
)

def get_embedding(text, model="text-embedding-ada-002"): # model = "deployment_name"
    return client.embeddings.create(input = [text], model=model).data[0].embedding

# print(generate_embeddings("What is the meaning of life?"))


