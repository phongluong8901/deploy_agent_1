from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from typing import Optional
import uuid
import google.generativeai as genai

# Load environment variables
load_dotenv(override=True)

app = FastAPI()

# Configure CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cấu hình Google Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

# Load personality details
def load_personality():
    with open("me.txt", "r", encoding="utf-8") as f:
        return f.read().strip()

PERSONALITY = load_personality()

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        session_id = request.session_id or str(uuid.uuid4())

        # Gemini sử dụng hệ thống "chat session" (history)
        # Ở đây ta khởi tạo history với system prompt (personality)
        chat_session = model.start_chat(history=[
            {"role": "user", "parts": [f"System instructions: {PERSONALITY}"]},
            {"role": "model", "parts": ["Understood. I will act according to these instructions."]}
        ])

        # Gửi tin nhắn
        response = chat_session.send_message(request.message)

        return ChatResponse(
            response=response.text, 
            session_id=session_id
        )

    except Exception as e:
        # print(f"LỖI CHI TIẾT: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)