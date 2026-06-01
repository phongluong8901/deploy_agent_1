from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from typing import Optional, List, Dict
import json
import uuid
from pathlib import Path
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

# Initialize Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
# Sử dụng gemini-1.5-flash để phản hồi nhanh
model = genai.GenerativeModel("gemini-2.5-flash")

# Memory directory
MEMORY_DIR = Path("../memory")
MEMORY_DIR.mkdir(exist_ok=True)

def load_personality():
    with open("me.txt", "r", encoding="utf-8") as f:
        return f.read().strip()

PERSONALITY = load_personality()

# Chuyển đổi định dạng role từ OpenAI (system/user/assistant) sang Gemini (user/model)
def convert_history_to_gemini(conversation: List[Dict]):
    gemini_history = []
    # Thêm personality làm lời dẫn đầu tiên
    gemini_history.append({"role": "user", "parts": [f"System Instructions: {PERSONALITY}"]})
    gemini_history.append({"role": "model", "parts": ["Understood. I am your Digital Twin."]})
    
    for msg in conversation:
        role = "user" if msg["role"] == "user" else "model"
        gemini_history.append({"role": role, "parts": [msg["content"]]})
    return gemini_history

# Memory functions (giữ nguyên)
def load_conversation(session_id: str) -> List[Dict]:
    file_path = MEMORY_DIR / f"{session_id}.json"
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_conversation(session_id: str, messages: List[Dict]):
    file_path = MEMORY_DIR / f"{session_id}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(messages, f, indent=2, ensure_ascii=False)

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
        conversation = load_conversation(session_id)
        
        # Tạo session chat với lịch sử cũ
        history = convert_history_to_gemini(conversation)
        chat_session = model.start_chat(history=history)
        
        # Gửi tin nhắn mới
        response = chat_session.send_message(request.message)
        assistant_response = response.text
        
        # Cập nhật lịch sử
        conversation.append({"role": "user", "content": request.message})
        conversation.append({"role": "assistant", "content": assistant_response})
        save_conversation(session_id, conversation)
        
        return ChatResponse(response=assistant_response, session_id=session_id)
    except Exception as e:
        print(f"Lỗi hệ thống: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)