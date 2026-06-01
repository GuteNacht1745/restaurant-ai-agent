from Models.reservations import ReservationExtraction

def parse_structured_output(data: dict) -> tuple[str | None, ReservationExtraction, dict | None]:
    structured_output = (
        data
        .get("message", {})
        .get("analysis", {})
        .get("structuredData", {})
    )

    call_type = structured_output.get("callType")

    reservation = structured_output.get("reservation") or {}
    pickup_order = structured_output.get("pickupOrder") or {}
    other = structured_output.get("other") or {}

    if call_type == "reservation":
        output =  ReservationExtraction(customer_name = reservation.get("name"),
                                     party_size = reservation.get("partySize"),
                                     reservation_time = reservation.get("dateTime"),
                                     special_request = reservation.get("specialRequest")
                                     )

    elif call_type == "pickup_order":
        output = ReservationExtraction(customer_name = pickup_order.get("name"),
                                     items = pickup_order.get("items"),
                                     pickup_time = pickup_order.get("pickupTime"),
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
        "reservation":[
            "customer_name",
            "party_size",
            "reservation_time"
        ],
        "pickup_order":[
            "customer_name",
            "items",
            "pickup_time"
        ]
    }

    return [field for field in require_field.get(call_type, []) if getattr(structured_output, field) is None]

