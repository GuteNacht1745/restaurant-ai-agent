from fastapi.encoders import isoformat
from datetime import datetime
from Models.reservations import ReservationExtraction
import dateparser
from Logic.ai_logic import normalize_datetime_ai
from difflib import SequenceMatcher
import unicodedata
from Database.database import sb

def normalize_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    datetime_parsed = dateparser.parse(
        value,
        settings = {
            "TIMEZONE": "Europe/Berlin",
            "RETURN_AS_TIMEZONE_AWARE": True,
            "PREFER_DATES_FROM": "future"
        }
    )
    if datetime_parsed:
        print(
            "Parsed using dateparser"
        )
        return datetime_parsed
    print("Fallback to OpenAI")
    return datetime.fromisoformat(normalize_datetime_ai(value))

def normalize_name(text: str) -> str:
    text = str(text).lower().strip()

    replacements = {
        "ß": "ss",
        "ü": "ue",
        "ä": "ae",
        "ö": "oe"
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()

    return text

def parse_structured_output(data: dict) -> tuple[str | None, ReservationExtraction, dict | None]:
    structured_output = (
        data
        .get("message", {})
        .get("artifact", {})
        .get("structuredOutputs", {})
        .get("f36ee908-fbeb-4545-858c-32b0a36eacda", {})
        .get("result", {})
    )
    if not structured_output:
        return None, ReservationExtraction(), None
    call_type = structured_output.get("callType")

    reservation = structured_output.get("reservation_created") or {}
    pickup_order = structured_output.get("pickup_order_created") or {}
    other = structured_output.get("other") or {}

    if call_type == "reservation_created":
        output =  ReservationExtraction(customer_name = reservation.get("customer_name"),
                                     party_size = reservation.get("partySize"),
                                     reservation_time = normalize_datetime(reservation.get("dateTimeRaw")),
                                     special_request = reservation.get("specialRequest")
                                     )

    elif call_type == "pickup_order_created":
        output = ReservationExtraction(customer_name = pickup_order.get("customer_name"),
                                     items = pickup_order.get("items", []),
                                     pickup_time = normalize_datetime(pickup_order.get("pickupTimeRaw")),
                                     special_request = pickup_order.get("specialRequest")
                                     )

    elif call_type == "other":
        output =  ReservationExtraction(
            reason = other.get("reason")
        )

    else:
        output = ReservationExtraction()

    return call_type, output, structured_output

def find_missing_field(structured_output: ReservationExtraction, call_type: str) -> list[str]:

    require_field = {
        "reservation_created":[
            "customer_name",
            "party_size",
            "reservation_time"
        ],
        "pickup_order_created":[
            "customer_name",
            "items",
            "pickup_time"
        ]
    }

    return [field for field in require_field.get(call_type, []) if not getattr(structured_output, field)]

def search_similarity(text: str) -> dict:
    rows = sb.table("menu").select("*").execute().data

    best_item = None
    best_score = 0
    best_candidate_text = None

    for row in rows:
        names = row.get("searchable_names") or []
        for name in names:
            score = SequenceMatcher(None, text, name).ratio()
            if score > best_score:
                best_score = score
                best_item = row
                best_candidate_text = name

    return {
        "item": best_item,
        "score": round(best_score, 2),
        "candidate_text": best_candidate_text
    }