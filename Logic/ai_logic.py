from fastapi import HTTPException
from openai import OpenAI
from settings import OPENAI_API_KEY
from datetime import datetime

client = OpenAI(api_key = OPENAI_API_KEY)

def extract_info(transcript: str, text_format):
    try:
        current_time = datetime.now().isoformat()
        response = client.responses.parse(
            model = "gpt-4.1-nano",
            input = [
                {
                    "role": "system",
                    "content": "You are receptionist at a restaurant, your job is receiving the reservation phone call from the customer"
                },
                {
                    "role": "developer",
                    "content": f"""
                    Extract:
                    - customer_name
                    - party_size
                    - reservation_time
                    - special_request
                    
                    Current datetime: {current_time}
                    
                    IMPORTANT:
                    Convert relative dates like:
                    - today
                    - tomorrow
                    - tonight
                    into a Full ISO-8601 datetime.
                    
                    Example:
                    2026-05-21T21:00:00
                    
                    DO NOT invent years.
                    Do not correct invalid values.
                    Extract values exactly as provided by the user.
                    """
                },
                {
                    "role": "user",
                    "content": transcript
                }
            ],
            text_format = text_format,
        )
        return response.output_parsed  # Return ReservationExtraction object
    except Exception:
        raise HTTPException(status_code = 502, detail = "AI service unavailable")