from Database.database import sb

def get_reservation(table, parameter, value):
    return sb.table(table).select("*").eq(parameter, value).execute()

def list_reservation():
    return sb.table("reservations").select("*").execute()

def insert_reservation(table, new_data):
    sb.table(table).insert(new_data).execute()

def update_reservation(table, new_data, parameter, value):
    sb.table(table).update(new_data).eq(parameter, value).execute()

def delete_reservation(table, parameter, value):
    sb.table(table).delete().eq(parameter, value).execute()

