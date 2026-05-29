FOLLOWUP_QUESTIONS = {
    "name": "your name",
    "phone_number": "your phone number",
    "number_of_people": "how many people for your reservation",
    "reservation_time": "the time for your reservation"
}

def follow_up_question(list_missing, conversation_id):
    message = [FOLLOWUP_QUESTIONS[missing] for missing in list_missing]
    final_message = " and ".join(message)
    return {
        "conversation_id": conversation_id,
        "message": f"Could you provide me {final_message}?"
    }

REQUIRE_FIELDS = [
    "customer_name",
    "party_size",
    "reservation_time"
]

def find_missing_field(extracted_info: dict):
    return [field for field in REQUIRE_FIELDS if extracted_info.get(field) is None]