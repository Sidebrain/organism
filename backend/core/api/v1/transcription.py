from fastapi import APIRouter

app = APIRouter(prefix="/transcription", tags=["transcription"])


@app.post("/")
async def transcribe():
    return {"message": "Hello World"}