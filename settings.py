from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
VAPI_PRIVATE_KEY=os.getenv("VAPI_PRIVATE_KEY")
VAPI_ORG_ID=os.getenv("VAPI_ORG_ID")
WEBHOOK_BEARER_TOKEN=os.getenv("WEBHOOK_BEARER_TOKEN")