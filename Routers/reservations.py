from fastapi import APIRouter, HTTPException
from Logic.agent_tools import run_tools
from Logic.data_processing import find_missing_field, parse_structured_output
from Models.reservations import ReservationOutput, CallOutputValidated, ReservationExtraction, \
    CallLogsValidated, ItemValidated
from Logic.db_logic import get_record, list_reservation, insert_record
import jwt
import time
from settings import VAPI_PRIVATE_KEY, VAPI_ORG_ID

router = APIRouter()

@router.get("/reservations/{reservation_id}")
def get_call(reservation_id: int) -> dict:
    try:
        call = get_record("reservations", {"reservation_id": reservation_id})

        if not call:
            raise HTTPException(status_code=404, detail="Reservation not found")

        return call

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(status_code = 500, detail = "Database error")

@router.get("/reservations", response_model=list[ReservationOutput])
def get_calls() -> list[ReservationOutput]:
    list_data = list_reservation()
    return list_data.data

@router.post("/webhook")
def webhook(event: dict) -> dict:

    event_type = event.get("message", {}).get("type", None)

    if event_type == "tool-calls":
        return run_tools(event)

    if event_type == "end-of-call-report":

        call_type, extracted_data, raw_structured_output = parse_structured_output(event)

        call_id = event["message"]["call"]["id"]
        phone_number = event.get("message", {}).get("customer", {}).get("number")
        started_at = event["message"]["startedAt"]
        ended_at = event["message"]["endedAt"]
        ended_reason = event["message"]["endedReason"]
        duration_seconds = event["message"]["durationSeconds"]
        recording_url = event["message"]["recordingUrl"]
        summary = (event.get("message", {}).get("artifact", {}).get("structuredOutputs", {})
                   .get("f36ee908-fbeb-4545-858c-32b0a36eacda", {}).get("result", {}).get("summary")) or "Summary unavailable"
        transcript = event["message"]["transcript"]

        # Call log process
        call_validated = CallLogsValidated(
            call_id = call_id,
            summary = summary,
            transcript = transcript,
            recording_url = recording_url,
            phone_number = phone_number,
            started_at = started_at,
            ended_at = ended_at,
            duration_seconds = duration_seconds,
            ended_reason = ended_reason,
            structured_output = raw_structured_output,
            call_type = call_type
        )
        insert_record("call_logs", call_validated.model_dump(mode = "json", exclude_none = True))

        if not raw_structured_output:
            return {
                "message": "Call logged. No structured output."
            }

        # Reservation creation process
        missing_fields = find_missing_field(extracted_data, call_type) # Return a list

        is_complete = not missing_fields

        if call_type == "reservation_created":
            reservation_validated = CallOutputValidated(
                customer_name = extracted_data.customer_name,
                party_size = extracted_data.party_size,
                reservation_time = extracted_data.reservation_time,
                special_request = extracted_data.special_request,
                call_id = call_id,
                phone_number = phone_number,
                missing_fields = missing_fields,
                is_complete = is_complete
            )
            insert_record("reservations", reservation_validated.model_dump(mode = "json", exclude_none = True))

        elif call_type == "pickup_order_created":
            order_validated = CallOutputValidated(
                customer_name = extracted_data.customer_name,
                pickup_time = extracted_data.pickup_time,
                special_request = extracted_data.special_request,
                call_id = call_id,
                phone_number = phone_number,
                missing_fields = missing_fields,
                is_complete = is_complete
            )
            order_inserted = insert_record("pickup_orders", order_validated.model_dump(mode = "json", exclude_none = True))
            order_id = order_inserted[0]["order_id"]

            for item in (extracted_data.items or []):
                item_validated = ItemValidated(
                    order_id = order_id,
                    item_number = item.get("itemNumber"),
                    item_name = item.get("itemName"),
                    extras = item.get("selectedExtra"),
                    special_request = item.get("specialRequest"),
                    variant = item.get("variant")
                )

                insert_record("pickup_order_items", item_validated.model_dump(mode = "json", exclude_none = True))

        return {
            "message": "Data added successfully."
        }
    return {
        "status": "okeee"
    }

@router.get("/health")
def health():
    return {
        "message": "oke"
    }

@router.post("/vapi-web-token")
def vapi_web_token():
    """
    Returns a short-lived JWT that the browser can use to initialize the Vapi Web SDK.
    This avoids calling Vapi endpoints directly from the browser (CORS issues).
    """
    vapi_private_key = VAPI_PRIVATE_KEY
    if not vapi_private_key:
        raise HTTPException(status_code=500, detail="VAPI_PRIVATE_KEY is not set")

    now = int(time.time())

    # If you know your orgId, set VAPI_ORG_ID in env and we'll include it.
    vapi_org_id = VAPI_ORG_ID
    payload = {
        "iat": now,
        "exp": now + 300,  # 5 minutes
    }
    if vapi_org_id:
        payload["orgId"] = vapi_org_id

    token = jwt.encode(payload, vapi_private_key, algorithm="HS256")

    return {"token": token}