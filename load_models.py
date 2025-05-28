from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from dotenv import load_dotenv
import os

load_dotenv('.env')

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_MODEL = GeminiModel('gemini-2.0-flash', provider=GoogleGLAProvider(api_key=GEMINI_API_KEY))
