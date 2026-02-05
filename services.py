# services.py
import json
import google.generativeai as genai
from config import settings
from utils import sanitize_text, process_image

# Init Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel(settings.GEMINI_MODEL)

SYSTEM_PROMPT = """
You are a conservative medical AI assistant. 
Analyze the input and return ONLY valid JSON matching this schema:
{
    "findings": "str",
    "potential_diagnosis": "str",
    "remedies": ["str"],
    "diet_plan": ["str"],
    "is_emergency": bool
}
Do not use markdown formatting. Just raw JSON.
"""


async def analyze_medical_data(query: str, image_bytes: bytes = None) -> dict:
    # 1. Sanitize Inputs
    safe_query = sanitize_text(query)

    content = [SYSTEM_PROMPT, f"Patient Query: {safe_query}"]

    # 2. Process Image if exists
    if image_bytes:
        processed_img = process_image(image_bytes)
        content.append(processed_img)

    # 3. Call AI
    try:
        response = model.generate_content(content)

        # 4. Clean Response (Strip markdown if Gemini adds it)
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)

    except json.JSONDecodeError:
        # Fallback if AI returns bad JSON
        return {
            "findings": "AI Error: Could not parse response",
            "potential_diagnosis": "Unknown",
            "remedies": [],
            "diet_plan": [],
            "is_emergency": False
        }
    except Exception as e:
        raise e