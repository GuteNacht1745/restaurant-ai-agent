from Logic.db_logic import get_record, get_record_contains
from Logic.data_processing import normalize_name, search_similarity
from Database.database import sb
from datetime import datetime
from zoneinfo import ZoneInfo

def verify_scoring(score, raw_text, method, candidate_text):
    inserted_data = {
        "score": score,
        "method": method,
        "raw_text": raw_text,
        "candidate_text": candidate_text
    }
    sb.table("order_item_resolution_log").insert(inserted_data).execute()

def search_menu(tool_call_id, item_number: str | None = None, item_name: str | None = None):

    menu_item = None
    needs_confirmation = False
    score = None
    method = None

    if item_number:
        item_number = item_number.strip().upper()
        menu_item = get_record("menu", "item_number", item_number)

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


    category = get_record("menu_categories", "category_id", menu_item["category_id"])
    allowed_extra_ids = menu_item.get("allowed_extra_ids") or []
    available_extras = []

    for extra_id in allowed_extra_ids:
        extra_option = get_record("extra_options", "extra_id", extra_id)
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

def get_current_time(tool_call_id):
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

TOOL_REGISTRY = {
    "search_menu": search_menu,
    "get_current_time": get_current_time
}

def run_tools(event: dict):
    tool_results = []
    tool_call_list = event.get("message", {}).get("toolCallList", [{}])
    for tool in tool_call_list:
        tool_id = tool.get("id")
        tool_name = tool.get("function", {}).get("name")
        arguments = tool.get("function", {}).get("arguments", {})

        tool_func = TOOL_REGISTRY.get(tool_name)

        if not tool_func:
            continue

        result = tool_func(tool_call_id = tool_id, **arguments)

        tool_results.append(result)

    return {
        "results": tool_results
    }
