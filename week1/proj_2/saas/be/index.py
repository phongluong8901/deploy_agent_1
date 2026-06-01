from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api-be")
def idea():
    try:
        # Lưu ý: Đảm bảo GOOGLE_API_KEY đã được thêm vào Vercel Settings -> Environment Variables
        client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Come up with a new business idea for AI Agents",
        )
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"