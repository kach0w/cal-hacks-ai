from google import genai
from dotenv import load_dotenv
import os

load_dotenv()
key = os.environ["GOOGLE_AI_API_KEY"]
client = genai.Client(api_key=key)

for m in client.models.list():
    print(m.name, "|", m.supported_actions)
