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

app = FastAPI(title="Doctor Brain API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- SECURITY DEPENDENCY ---
async def verify_token(x_api_key: str = Header(...)):
    """Enforces that your friend sends the correct password in the headers."""
    if x_api_key != settings.API_SECRET_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid Secret Token")


# --- ENDPOINTS ---
@app.post("/analyze", response_model=AnalysisResult)
async def analyze_endpoint(
        query: str = Form(...),
        image: UploadFile = File(None),
        token: str = Depends(verify_token)  # 🔒 Locks the endpoint
):
    logger.info("Received analysis request")

    image_data = None
    if image:
        image_data = await image.read()

    try:
        result = await analyze_medical_data(query, image_data)
        return result
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)