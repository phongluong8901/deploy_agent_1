from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from typing import Optional, List, Dict
import json
import uuid
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
import google.generativeai as genai
from context import prompt

# Load environment variables
load_dotenv()

app = FastAPI()

# Configure CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Initialize Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

# Memory storage configuration
USE_S3 = os.getenv("USE_S3", "false").lower() == "true"
S3_BUCKET = os.getenv("S3_BUCKET", "")
MEMORY_DIR = os.getenv("MEMORY_DIR", "../memory")

if USE_S3:
    s3_client = boto3.client("s3")

# Models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str

# Memory Helpers
def get_memory_path(session_id: str) -> str:
    return f"{session_id}.json"

def load_conversation(session_id: str) -> List[Dict]:
    if USE_S3:
        try:
            response = s3_client.get_object(Bucket=S3_BUCKET, Key=get_memory_path(session_id))
            return json.loads(response["Body"].read().decode("utf-8"))
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey": return []
            raise
    else:
        file_path = os.path.join(MEMORY_DIR, get_memory_path(session_id))
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f: return json.load(f)
        return []

def save_conversation(session_id: str, messages: List[Dict]):
    if USE_S3:
        s3_client.put_object(
            Bucket=S3_BUCKET, Key=get_memory_path(session_id),
            Body=json.dumps(messages, indent=2), ContentType="application/json"
        )
    else:
        os.makedirs(MEMORY_DIR, exist_ok=True)
        file_path = os.path.join(MEMORY_DIR, get_memory_path(session_id))
        with open(file_path, "w", encoding="utf-8") as f: json.dump(messages, f, indent=2)

def convert_to_gemini_history(conversation: List[Dict]):
    history = []
    for msg in conversation:
        role = "user" if msg["role"] == "user" else "model"
        history.append({"role": role, "parts": [msg["content"]]})
    return history

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        session_id = request.session_id or str(uuid.uuid4())
        conversation = load_conversation(session_id)

        # Gemini session management
        chat_session = model.start_chat(history=convert_to_gemini_history(conversation))
        
        # Inject system prompt + user message
        full_input = f"System Context: {prompt()}\n\nUser: {request.message}"
        
        response = chat_session.send_message(full_input)
        assistant_response = response.text

        # Update and Save
        conversation.append({"role": "user", "content": request.message, "timestamp": datetime.now().isoformat()})
        conversation.append({"role": "assistant", "content": assistant_response, "timestamp": datetime.now().isoformat()})
        save_conversation(session_id, conversation)

        return ChatResponse(response=assistant_response, session_id=session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)