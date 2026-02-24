# services.py
import json
import google.generativeai as genai
from config import settings
from utils import sanitize_text, process_image

# 1. Init Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel(settings.GEMINI_MODEL)

# 2. LOAD YOUR NEW JSON DATABASE
try:
    with open("medical_knowledge.json", "r", encoding="utf-8") as f:
        MEDICAL_DB = json.load(f)
        print(f"✅ Medical Knowledge Base Loaded: {len(MEDICAL_DB)} topics.")
except FileNotFoundError:
    MEDICAL_DB = []
    print("⚠️ WARNING: medical_knowledge.json not found. The app will run without RAG context.")


def retrieve_context(query: str) -> str:
    if not MEDICAL_DB:
        return "No specific medical database available."

    query_lower = query.lower()

    # Priority 1: Exact Title Match
    for entry in MEDICAL_DB:
        if entry.get('title', '').lower() in query_lower:
            return entry.get('content', '')

    # Priority 2: Keyword Search inside Content
    for entry in MEDICAL_DB:
        if query_lower in entry.get('content', '').lower():
            return entry.get('content', '')[:2000]

    return "No specific medical topic found in database."


# 3. SYSTEM PROMPT
SYSTEM_PROMPT = """
You are a conservative medical AI assistant. 
Use the [RETRIEVED CONTEXT] below to inform your analysis, but prioritize patient safety.
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


# <-- ADDED mime_type PARAMETER HERE
async def analyze_medical_data(query: str, file_bytes: bytes = None, mime_type: str = None) -> dict:
    safe_query = sanitize_text(query)
    context_data = retrieve_context(safe_query)

    rag_prompt = f"""
    [RETRIEVED CONTEXT FROM DATABASE]
    {context_data}

    [PATIENT QUERY]
    {safe_query}
    """

    content = [SYSTEM_PROMPT, rag_prompt]

    # --- THE MAGIC FIX: Separate Images from PDFs ---
    if file_bytes and mime_type:
        if mime_type.startswith("image/"):
            # It's an image: send it to your secure PIL processor in utils.py
            processed_img = process_image(file_bytes)
            content.append(processed_img)
        elif mime_type == "application/pdf":
            # It's a PDF: PIL can't read PDFs, but Gemini can natively!
            content.append({
                "mime_type": "application/pdf",
                "data": file_bytes
            })

    # 5. Call AI
    try:
        response = model.generate_content(content)
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)

    except json.JSONDecodeError:
        return {
            "findings": "AI Error: Could not parse response",
            "potential_diagnosis": "Unknown",
            "remedies": [],
            "diet_plan": [],
            "is_emergency": False
        }
    except Exception as e:
        raise e