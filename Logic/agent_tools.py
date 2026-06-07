from Logic.db_logic import get_record, get_record_contains
from Logic.data_processing import normalize_name, search_similarity
from Database.database import sb

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
            "results":[
            {
                "toolCallId":tool_call_id,
                "result":{
                    "found": False,
                    "item_number": item_number,
                    "item_name": item_name
            }
            }
        ]
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
        "results":[
        {
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
    ]
    }