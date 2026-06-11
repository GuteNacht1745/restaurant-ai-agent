from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from Routers.reservations import router

app = FastAPI()
app.include_router(router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "message": "Welcome to my restaurant, how may I help you?"
    }








