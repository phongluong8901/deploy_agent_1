from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from google import genai
from dotenv import load_dotenv
import os


load_dotenv()

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def instant():
    # Khởi tạo client với API key từ biến môi trường
    client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
    
    prompt = """
    You are on a website that has just been deployed to production for the first time!
    Please reply with an enthusiastic announcement to welcome visitors to the site, 
    explaining that it is live on production for the first time!
    """
    
    # Sử dụng mô hình gemini-2.5-flash (hoặc phiên bản bạn muốn)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    
    reply = response.text.replace("\n", "<br/>")
    html = f"<html><head><title>Live in an Instant!</title></head><body><p>{reply}</p></body></html>"
    return html