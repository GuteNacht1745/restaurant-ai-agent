from fastapi import APIRouter, HTTPException
from Logic.conversation_logic import find_missing_field
from Models.reservations import ReservationOutput, ReservationValidated, ReservationExtraction, \
    CallLogsValidated
from Logic.ai_logic import extract_info
from Logic.db_logic import get_reservation, list_reservation, insert_reservation

router = APIRouter()

@router.get("/reservations/{reservation_id}", response_model=ReservationOutput)
def get_call(reservation_id: int) -> ReservationOutput:
    try:
        call = get_reservation("reservations", "reservation_id", reservation_id)

        if not call.data:
            raise HTTPException(status_code=404, detail="Reservation not found")

        return call.data[0]

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(status_code = 500, detail = "Database error")

@router.get("/reservations", response_model=list[ReservationOutput])
def get_calls():
    list_data = list_reservation()
    return list_data.data

@router.post("/webhook")
def webhook(event: dict):

    event_type = event.get("message", {}).get("type", None)

    if event_type == "end-of-call-report":
        call_id = event["message"]["call"]["id"]
        phone_number = event["message"]["customer"]["number"]
        started_at = event["message"]["startedAt"]
        ended_at = event["message"]["endedAt"]
        ended_reason = event["message"]["endedReason"]
        duration_seconds = event["message"]["durationSeconds"]
        recording_url = event["message"]["recordingUrl"]
        summary = event["message"]["summary"]
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
            ended_reason = ended_reason
        )
        insert_reservation("call_logs", call_validated.model_dump(mode = "json"))


        # Reservation creation process
        extracted_info = extract_info(transcript, ReservationExtraction) # Return ReservationExtraction object
        missing_fields = find_missing_field(extracted_info.model_dump()) # Return a list

        is_complete = not missing_fields

        reservation_validated = ReservationValidated(
            **extracted_info.model_dump(),
            call_id = call_id,
            phone_number = phone_number,
            missing_fields = missing_fields,
            is_complete = is_complete
        )
        insert_reservation("reservations", reservation_validated.model_dump(mode = "json"))


        return {
            "message": "Data added successfully."
        }
    return {
        "status": "ok"
    }