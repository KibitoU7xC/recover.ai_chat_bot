# utils.py
import re
from PIL import Image, ImageEnhance
import io

# --- PII SCRUBBER (Text) ---
def sanitize_text(text: str) -> str:
    # Remove Emails
    text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', "[REDACTED_EMAIL]", text)
    # Remove Phone Numbers (Generic patterns)
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', "[REDACTED_PHONE]", text)
    return text

# --- IMAGE ENHANCER & METADATA STRIPPER ---
def process_image(image_bytes: bytes):
    try:
        img = Image.open(io.BytesIO(image_bytes))

        # 1. SECURITY: Safe EXIF Stripping (NO memory crash)
        img_without_exif = Image.new(img.mode, img.size)
        img_without_exif.paste(img)

        # 2. ENHANCE: Convert to Grayscale & Boost Contrast
        img_gray = img_without_exif.convert("L")
        enhancer = ImageEnhance.Contrast(img_gray)
        final_img = enhancer.enhance(1.5)



        return final_img
    except Exception as e:
        print(f"❌ UTILS.PY CRASHED: {e}")
        return None