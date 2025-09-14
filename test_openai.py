from dotenv import load_dotenv
import os
import openai

# Ladda .env
load_dotenv()

# Hämta nyckeln
api_key = os.getenv("OPENAI_API_KEY")
print("Key starts with:", api_key[:7] if api_key else "None")

# Initiera OpenAI-klienten
client = openai.OpenAI(api_key=api_key)

# Lista de första 3 modellerna
models = client.models.list().data[:3]
print("Available models:", [m.id for m in models])

