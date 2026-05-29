from fastapi import FastAPI
from Routers.reservations import router

app = FastAPI()
app.include_router(router)

@app.get("/")
def root():
    return {
        "message": "Welcome to my restaurant, how may I help you?"
    }








