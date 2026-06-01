from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi_clerk_auth import ClerkConfig, ClerkHTTPBearer, HTTPAuthorizationCredentials
from google import genai

import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

clerk_config = ClerkConfig(jwks_url=os.getenv("CLERK_JWKS_URL"))
clerk_guard = ClerkHTTPBearer(clerk_config)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api-be")
def idea():
    # Khởi tạo client
    client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
    
    def event_stream():
        try:
            # Tạo stream trực tiếp trong generator
            # Đảm bảo lệnh này nằm bên trong generator để mỗi khi có request mới 
            # nó tạo ra một kết nối mới hoàn toàn
            response = client.models.generate_content_stream(
                model="gemini-2.5-flash",
                contents="Come up with a new business idea for AI Agents",
            )
            
            for chunk in response:
                if chunk.text:
                    yield f"data: {chunk.text}\n\n"
                    
        except Exception as e:
            yield f"data: \n\n**Lỗi hệ thống:** {str(e)}"
            
    return StreamingResponse(event_stream(), media_type="text/event-stream")