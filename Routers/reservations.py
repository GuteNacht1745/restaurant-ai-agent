from fastapi import APIRouter, HTTPException
from Logic.data_processing import find_missing_field, parse_structured_output
from Models.reservations import ReservationOutput, CallOutputValidated, ReservationExtraction, \
    CallLogsValidated, ItemValidated
from Logic.db_logic import get_reservation, list_reservation, insert_record

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
      # Return ReservationExtraction object

    if event_type == "end-of-call-report":
        call_type, extracted_data, raw_structured_output = parse_structured_output(event)

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
            ended_reason = ended_reason,
            structured_output = raw_structured_output,
            call_type = call_type
        )
        insert_record("call_logs", call_validated.model_dump(mode = "json"))


        # Reservation creation process
        missing_fields = find_missing_field(extracted_data, call_type) # Return a list

        is_complete = not missing_fields

        if call_type == "reservation":
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

        elif call_type == "pickup_order":
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
            order_id = order_inserted.data[0]["order_id"]

            for item in (extracted_data.items or []):
                item_validated = ItemValidated(
                    order_id = order_id,
                    item_number = item.get("itemNumber"),
                    item_name = item.get("itemName"),
                    quantity = item.get("quantity")
                )

                insert_record("pickup_order_items", item_validated.model_dump(mode = "json"))

        return {
            "message": "Data added successfully."
        }
    return {
        "status": "ok"
    }