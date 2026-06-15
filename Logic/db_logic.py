import datetime
import json
from Database.database import sb
from Logic.data_processing import normalize_datetime


def get_record(table, filters: dict, ranges: dict[str, tuple[str, str]] | None = None) -> list[dict]:

    query = sb.table(table).select("*")

    for column, value in filters.items():
        if value is not None:
            query = query.eq(column, value)
    if ranges:
        for column, (start, end) in ranges.items():

            if start is not None:
                query = query.gte(column, start)
            if end is not None:
                query = query.lte(column, end)

    return query.execute().data

def get_record_contains(table: str, parameter: str, values: list[str]) -> dict | None:
    response = sb.table(table).select("*").filter(parameter, "cs", json.dumps(values)).execute()
    if not response.data:
        return None
    return response.data[0]

def list_reservation():
    return sb.table("reservations").select("*").execute()

def insert_record(table, new_data):
    return sb.table(table).insert(new_data).execute().data

def update_record(table: str, new_data: dict, parameter: str, value) -> bool:
    response = sb.table(table).update(new_data).eq(parameter, value).execute()
    return response.data

def remove_record(table, parameter: str, value):
    response = sb.table(table).delete().eq(parameter, value).execute()
    return response.data




