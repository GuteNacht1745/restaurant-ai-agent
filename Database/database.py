from supabase import create_client
from settings import SUPABASE_URL, SUPABASE_API_KEY


sb = create_client(
    supabase_url = SUPABASE_URL,
    supabase_key = SUPABASE_API_KEY
)