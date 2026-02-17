# services.py
import json
import google.generativeai as genai
from config import settings
from utils import sanitize_text, process_image, extract_text_from_file, convert_pdf_to_images

# 1. Init Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel(settings.GEMINI_MODEL)

# 2. LOAD DB (Same as before)
try:
    with open("medical_knowledge.json", "r", encoding="utf-8") as f:
        MEDICAL_DB = json.load(f)
except FileNotFoundError:
    MEDICAL_DB = []

def retrieve_context(query: str) -> str:
    if not MEDICAL_DB: return "No database."
    query_lower = query.lower()
    for entry in MEDICAL_DB:
        if entry.get('title', '').lower() in query_lower:
            return entry.get('content', '')
    return "No specific topic found."

SYSTEM_PROMPT = """
You are a conservative medical AI assistant. 
Analyze the [PATIENT QUERY] and any [UPLOADED IMAGES/DOCS].
If the images are medical reports, extract the text and interpret the values.
Return ONLY valid JSON matching this schema:
{
    "findings": "str",
    "potential_diagnosis": "str",
    "remedies": ["str"],
    "diet_plan": ["str"],
    "is_emergency": bool
}
"""

async def analyze_medical_data(query: str, file_bytes: bytes = None, content_type: str = None) -> dict:
    safe_query = sanitize_text(query)
    context_data = retrieve_context(safe_query)
    
    # Prepare the prompt parts
    prompt_content = [
        SYSTEM_PROMPT, 
        f"[RETRIEVED CONTEXT]: {context_data}",
        f"[PATIENT QUERY]: {safe_query}"
    ]

    # --- HANDLE FILES ---
    if file_bytes and content_type:
        if "pdf" in content_type:
            # 1. Convert PDF pages to Images (Vision approach for scanned docs)
            pdf_images = convert_pdf_to_images(file_bytes)
            if pdf_images:
                prompt_content.append(f"[Start of PDF Images ({len(pdf_images)} pages)]")
                prompt_content.extend(pdf_images) # Add all images to prompt
            else:
                prompt_content.append("Error: Could not convert PDF to images.")

        elif "image" in content_type:
            # 2. Process Single Image
            img = process_image(file_bytes)
            prompt_content.append(img)
            
        else:
            # 3. Process Text Doc (Word/Txt)
            text_content = extract_text_from_file(file_bytes, content_type)
            prompt_content.append(f"[DOCUMENT CONTENT]: {text_content}")

    # --- CALL AI ---
    try:
        response = model.generate_content(prompt_content)
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    except Exception as e:
        # Fallback error
        return {
            "findings": f"Error processing request: {str(e)}",
            "potential_diagnosis": "Unknown",
            "remedies": [],
            "diet_plan": [],
            "is_emergency": False
        }