from fastapi import HTTPException
from datetime import datetime
from openai import OpenAI
from settings import OPENAI_API_KEY

client = OpenAI(api_key = OPENAI_API_KEY)

def normalize_datetime_ai(raw_time):
    try:
        response = client.responses.create(
                model=
                "gpt-5.4-mini",

                input=
                f"""
                Current datetime:
                {datetime.now().isoformat()}
                
                Timezone:
                Europe/Berlin
                
                Convert to ISO-8601.

                Return only datetime.
                
                Output Examples (assume current datetime is 2026-06-02T15:00:00+02:00):

                Input:
                tomorrow at 7 PM
                
                Output:
                2026-06-03T19:00:00+02:00
                
                Input:
                in about 15 minutes
                
                Output:
                2026-06-02T15:15:00+02:00
                
                Input:
                next week friday at 12 pm
                
                Output:
                2026-06-12T12:00:00+02:00
                                
                Input:
                {raw_time}
                """
            )

        return response.output_text

    except Exception:
        raise HTTPException(
            status_code=502,
            detail="AI service unavailable"
        )