# services.py
import json
import google.generativeai as genai
from config import settings
from utils import sanitize_text, process_image

# 1. Init Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel(settings.GEMINI_MODEL)

# 2. LOAD YOUR NEW JSON DATABASE
# This attempts to load 'medical_knowledge.json' when the server starts.
try:
    with open("medical_knowledge.json", "r", encoding="utf-8") as f:
        MEDICAL_DB = json.load(f)
        print(f"✅ Medical Knowledge Base Loaded: {len(MEDICAL_DB)} topics.")
except FileNotFoundError:
    MEDICAL_DB = []
    print("⚠️ WARNING: medical_knowledge.json not found. The app will run without RAG context.")


def retrieve_context(query: str) -> str:
    """
    RAG Search: Finds relevant medical info from your JSON file.
    """
    if not MEDICAL_DB:
        return "No specific medical database available."

    query_lower = query.lower()

    # Priority 1: Exact Title Match (e.g., User asks "A1C", finds "A1C" topic)
    for entry in MEDICAL_DB:
        if entry.get('title', '').lower() in query_lower:
            return entry.get('content', '')

    # Priority 2: Keyword Search inside Content
    # If the user asks "diabetes test", it might not match title "A1C" but matches the text inside.
    for entry in MEDICAL_DB:
        if query_lower in entry.get('content', '').lower():
            # Return first 2000 chars to keep prompt size manageable
            return entry.get('content', '')[:2000]

    return "No specific medical topic found in database."


# 3. UPDATED PROMPT (Now mentions the Retrieved Context)
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


async def analyze_medical_data(query: str, image_bytes: bytes = None) -> dict:
    # 1. Sanitize Inputs
    safe_query = sanitize_text(query)

    # 2. RETRIEVE (Get data from your JSON)
    context_data = retrieve_context(safe_query)

    # 3. AUGMENT (Inject that data into the prompt)
    rag_prompt = f"""
    [RETRIEVED CONTEXT FROM DATABASE]
    {context_data}

    [PATIENT QUERY]
    {safe_query}
    """

    content = [SYSTEM_PROMPT, rag_prompt]

    # 4. Process Image if exists
    if image_bytes:
        processed_img = process_image(image_bytes)
        content.append(processed_img)

    # 5. Call AI
    try:
        response = model.generate_content(content)

        # Clean Response
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
        # Pass the actual error up so you can see it in logs
        raise e