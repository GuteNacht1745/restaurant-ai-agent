from Logic.db_logic import get_record

def search_menu(item_number: str, tool_call_id):
    menu_item = get_record("menu", "item_number", item_number)

    if menu_item is None:
        return {
            "results":[
            {
                "toolCallId":tool_call_id,
                "result":{
                    "found": False,
                    "item_number": item_number
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