from Logic.db_logic import get_record, get_record_contains, update_record
from Logic.data_processing import normalize_name, search_similarity, normalize_datetime
from Database.database import sb
from datetime import datetime
from zoneinfo import ZoneInfo
from Models.reservations import ReservationUpdate, OrderUpdate


def verify_scoring(score, raw_text, method, candidate_text) -> None:
    inserted_data = {
        "score": score,
        "method": method,
        "raw_text": raw_text,
        "candidate_text": candidate_text
    }
    sb.table("order_item_resolution_log").insert(inserted_data).execute()

def search_menu(tool_call_id, item_number: str | None = None, item_name: str | None = None) -> dict:

    menu_item = None
    needs_confirmation = False
    score = None
    method = None

    if item_number:
        item_number = item_number.strip().upper()
        menu_item = get_record("menu", {"item_number": item_number})

    elif item_name:
        item_name = normalize_name(item_name)
        menu_item = get_record_contains("menu", "searchable_names", [item_name])
        if not menu_item:
            method = "similarity"
            similarity_result = search_similarity(item_name)
            score = similarity_result["score"]
            if score > 0.8:
                menu_item = similarity_result["item"]
            elif score > 0:
                menu_item = similarity_result["item"]
                needs_confirmation = True
            if score is not None:
                verify_scoring(score, raw_text = item_name, method = method, candidate_text = similarity_result["candidate_text"])

    if not menu_item:
        return {
                "toolCallId":tool_call_id,
                "result":{
                    "found": False,
                    "item_number": item_number,
                    "item_name": item_name
            }
            }


    category = get_record("menu_categories", {"category_id": menu_item["category_id"]})
    allowed_extra_ids = menu_item.get("allowed_extra_ids") or []
    available_extras = []

    for extra_id in allowed_extra_ids:
        extra_option = get_record("extra_options", {"extra_id": extra_id})
        if extra_option:
            available_extras.append({
                "extra_name": extra_option["extra_item_name"],
                "extra_price": extra_option["extra_item_price"]
            })

    return {
        "toolCallId": tool_call_id,
        "result": {
        "found": True,
        "needs_confirmation": needs_confirmation,
        "item_number": menu_item["item_number"],
        "item_name_vi": menu_item["item_name_vi"],
        "item_name_de": menu_item["item_name_de"],
        "item_price": menu_item["item_price"],
        "item_description": menu_item["item_description"],
        "category": {
            "category_vi": category["category_vi"] if category else None,
            "category_de": category["category_de"] if category else None,
            "serving_note": category["serving_note"] if category else None
        },
        "variant_options": menu_item.get("variant_options", []) or [],
        "available_extras": available_extras
    }
        }

def get_current_time(tool_call_id) -> dict:
    tz = ZoneInfo("Europe/Berlin")
    now = datetime.now(tz = tz)

    return  {
                "toolCallId": tool_call_id,
                "result": {
                    "timezone": "Europe/Berlin",
                    "nowIso": now.isoformat(),
                    "unixMs": int(now.timestamp() * 1000),
                    "date": now.strftime("%Y-%m-%d"),
                    "time": now.strftime("%H:%M"),
                    "weekday": now.strftime("%A"),
                    "nowHuman": now.strftime("%A, %d %B %Y, %H:%M")
                }
            }

def lookup_reservation(tool_call_id,
                       phone_number: str | None = None,
                       customer_name: str | None = None,
                       party_size: int | None = None,
                       reservation_time: str | None = None) -> dict:
    parsed = normalize_datetime(reservation_time)
    reservation_time_iso = parsed.isoformat() if isinstance(parsed, datetime) else None
    response = get_record("reservations", {
        "phone_number": phone_number,
        "customer_name": customer_name,
        "party_size": party_size,
        "reservation_time": reservation_time_iso
    })
    return {
        "toolCallId": tool_call_id,
        "result": {
            "found": bool(response),
            "reservation": response
        }
    }

def lookup_order(tool_call_id,
                 phone_number: str | None = None,
                 pickup_time: str | None = None,
                 customer_name: str | None = None) -> dict:
    parsed = normalize_datetime(pickup_time)
    pickup_time_iso = parsed.isoformat() if isinstance(parsed, datetime) else None
    response = get_record("pickup_orders", {
        "phone_number": phone_number,
        "pickup_time": pickup_time_iso,
        "customer_name": customer_name
    })
    return {
        "toolCallId": tool_call_id,
        "result": {
            "found": bool(response),
            "order": response
        }
    }

def update_reservation(tool_call_id: str,
                       reservation_id: str,
                       customer_name: str | None = None,
                       reservation_time: str | None = None,
                       special_request: str | None = None,
                       party_size: int | None = None) -> dict:
    parsed = normalize_datetime(reservation_time)
    reservation_time_iso = parsed.isoformat() if isinstance(parsed, datetime) else None
    updated_data_validated = ReservationUpdate(
        customer_name = customer_name,
        reservation_time = reservation_time_iso,
        special_request = special_request,
        party_size = party_size
    )
    response = update_record("reservations", updated_data_validated.model_dump(mode = "json", exclude_none = True), "reservation_id", reservation_id)
    return {
        "toolCallId": tool_call_id,
        "result": {
            "success": response,
            "status": "Reservation updated successfully." if response else "Reservation update failed."
        }
    }

def update_order(tool_call_id: str,
                 order_id: int,
                 customer_name: str | None = None,
                 pickup_time: str | None = None,
                 special_request: str | None = None) -> dict:
    parsed = normalize_datetime(pickup_time)
    pickup_time_iso = parsed.isoformat() if isinstance(parsed, datetime) else None
    updated_data_validated = OrderUpdate(
        customer_name = customer_name,
        pickup_time = pickup_time_iso,
        special_request = special_request
    )
    response = update_record("pickup_orders", updated_data_validated.model_dump(mode = "json", exclude_none = True), "order_id", order_id)
    return {
        "toolCallId": tool_call_id,
        "result": {
            "success": response,
            "status": "Order updated successfully." if response else "Order update failed."
        }
    }

def cancel_reservation(tool_call_id: str, reservation_id: int) -> dict:
    response = update_record("reservations", {"status": "cancelled"}, "reservation_id", reservation_id)
    return {
        "toolCallId": tool_call_id,
        "result": {
            "success": response,
            "status": "Reservation cancelled successfully" if response else "Reservation cancellation failed."
        }
    }

def cancel_order(tool_call_id: str, order_id: int) -> dict:
    response = update_record("pickup_orders", {"status": "cancelled"}, "order_id", order_id)
    return {
        "toolCallId": tool_call_id,
        "result":{
            "success": response,
            "status": "Order cancelled successfully" if response else "Order cancellation failed."
        }
    }

TOOL_REGISTRY = {
    "search_menu": search_menu,
    "get_current_time": get_current_time,
    "lookup_reservation": lookup_reservation,
    "lookup_order": lookup_order,
    "update_reservation": update_reservation,
    "update_order": update_order,
    "cancel_reservation": cancel_reservation,
    "cancel_order": cancel_order
}

def run_tools(event: dict) -> dict[str, list[dict]]:
    tool_results: list[dict] = []
    tool_call_list = event.get("message", {}).get("toolCallList", [{}])
    for tool in tool_call_list:
        tool_id = tool.get("id")
        tool_name = tool.get("function", {}).get("name")
        arguments = tool.get("function", {}).get("arguments", {})
        tool_func = TOOL_REGISTRY.get(tool_name)

        if not tool_func:
            tool_results.append({
                "toolCallId": tool_id,
                "result": {"success": False, "error": f"Tool '{tool_name}' not implemented on server"}
            })
            continue

        result = tool_func(tool_call_id = tool_id, **arguments)

        tool_results.append(result)

    return {
        "results": tool_results
    }
