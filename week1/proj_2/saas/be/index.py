import os
from fastapi import FastAPI, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from fastapi_clerk_auth import ClerkConfig, ClerkHTTPBearer, HTTPAuthorizationCredentials
from google import genai # Import thư viện chính của Google

app = FastAPI()
clerk_config = ClerkConfig(jwks_url=os.getenv("CLERK_JWKS_URL"))
clerk_guard = ClerkHTTPBearer(clerk_config)

class Visit(BaseModel):
    patient_name: str
    date_of_visit: str
    notes: str

system_prompt = """
You are provided with notes written by a doctor from a patient's visit.
Your job is to summarize the visit for the doctor and provide an email.
Reply with exactly three sections with the headings:
### Summary of visit for the doctor's records
### Next steps for the doctor
### Draft of email to patient in patient-friendly language
"""

def user_prompt_for(visit: Visit) -> str:
    return f"""Create the summary, next steps and draft email for:
Patient Name: {visit.patient_name}
Date of Visit: {visit.date_of_visit}
Notes:
{visit.notes}"""

@app.post("/api-be")
def consultation_summary(
    visit: Visit,
    creds: HTTPAuthorizationCredentials = Depends(clerk_guard),
):
    user_id = creds.decoded["sub"]
    
    # Khởi tạo client Gemini
    client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

    full_prompt = f"{system_prompt}\n\n{user_prompt_for(visit)}"

    # Gọi Gemini với streaming
    response = client.models.generate_content_stream(
        model="gemini-2.5-flash",
        contents=full_prompt,
    )

    def event_stream():
        for chunk in response:
            if chunk.text:
                # Format SSE chuẩn
                yield f"data: {chunk.text.replace(chr(10), ' ')}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")