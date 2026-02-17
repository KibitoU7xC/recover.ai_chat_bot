# main.py
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from services import analyze_medical_data
from schemas import AnalysisResult
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("doctor_brain")

app = FastAPI(title="Doctor Brain API", version="2.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- SECURITY DEPENDENCY ---
async def verify_token(x_api_key: str = Header(...)):
    if x_api_key != settings.API_SECRET_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid Secret Token")

# --- ENDPOINTS ---
@app.post("/analyze", response_model=AnalysisResult)
async def analyze_endpoint(
        query: str = Form(...),
        file: UploadFile = File(None),  # Changed from 'image' to 'file'
        token: str = Depends(verify_token)
):
    logger.info("Received analysis request")

    file_data = None
    content_type = None

    if file:
        file_data = await file.read()
        content_type = file.content_type
        logger.info(f"Processing file type: {content_type}")

    try:
        # Pass file data AND content_type to service
        result = await analyze_medical_data(query, file_data, content_type)
        return result
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ... rest of main.py (uvicorn logic) stays the same
import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
