# main.py
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from services import analyze_medical_data
from schemas import AnalysisResult
from fastapi.middleware.cors import CORSMiddleware
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("doctor_brain")

app = FastAPI(title="Doctor Brain API", version="2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all websites to connect (good for testing)
    allow_credentials=True,
    allow_methods=["*"],  # Allows POST, GET, OPTIONS, etc.
    allow_headers=["*"],  # Crucial: This tells the browser your 'x-api-key' is safe!
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- SECURITY DEPENDENCY ---
async def verify_token(x_api_key: str = Header(...)):
    """Enforces that your frontend sends the correct password in the headers."""
    if x_api_key != settings.API_SECRET_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid Secret Token")


# --- ENDPOINTS ---
@app.post("/analyze", response_model=AnalysisResult)
async def analyze_endpoint(
        query: str = Form(...),
        file: UploadFile = File(None),  # <-- CHANGED FROM 'image' TO 'file'
        token: str = Depends(verify_token)
):
    logger.info("Received analysis request")

    file_data = None
    mime_type = None
    if file:
        file_data = await file.read()
        mime_type = file.content_type  # <-- NEW: Get the file type (image/png or application/pdf)

    try:
        # Pass the mime_type to our service
        result = await analyze_medical_data(query, file_data, mime_type)
        return result
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))