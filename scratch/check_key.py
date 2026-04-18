from src.utils.api_keys import get_google_api_key
import os
print(f"DEBUG: GOOGLE_API_KEY in os.environ: {os.environ.get('GOOGLE_API_KEY')}")
print(f"DEBUG: get_google_api_key() result: {get_google_api_key()}")
