import json

from Database.database import sb

def get_record(table, filters: dict) -> dict | None:

    query = sb.table(table).select("*")

    for column, value in filters.items():
        if value is not None:
            query = query.eq(column, value)

    response = query.execute()

    if not response.data:
        return None
    return response.data

def get_record_contains(table: str, parameter: str, values: list[str]) -> dict | None:
    response = sb.table(table).select("*").filter(parameter, "cs", json.dumps(values)).execute()
    if not response.data:
        return None
    return response.data[0]

def list_reservation():
    return sb.table("reservations").select("*").execute()

def insert_record(table, new_data):
    return sb.table(table).insert(new_data).execute()

def update_record(table: str, new_data: dict, parameter: str, value) -> bool:
    response = sb.table(table).update(new_data).eq(parameter, value).execute()
    return bool(response.data)
