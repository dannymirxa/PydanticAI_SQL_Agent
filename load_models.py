from openai import AsyncAzureOpenAI

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

client = AsyncAzureOpenAI(
    azure_endpoint = "https://llmcoechangemateopenai2.openai.azure.com/",
    api_key=AZURE_OPENAI_KEY,
    api_version="2024-10-01-preview",
)

OPENAI_MODEL = OpenAIModel(
    'gpt-4o-dev',
    provider=OpenAIProvider(openai_client=client),
)

# from pydantic_ai import Agent
# agent = Agent(model)
# result = agent.run_sync('Where is KL, Malaysia?')

# print(result)
