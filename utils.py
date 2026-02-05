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
def process_image(image_bytes: bytes) -> Image.Image:
    try:
        img = Image.open(io.BytesIO(image_bytes))

        # 1. SECURITY: Strip EXIF Data (GPS, Camera info, Dates)
        # This prevents leaking location data to the AI model.
        data = list(img.getdata())
        img_without_exif = Image.new(img.mode, img.size)
        img_without_exif.putdata(data)

        # 2. ENHANCE: Convert to Grayscale & Boost Contrast
        img_gray = img_without_exif.convert("L")
        enhancer = ImageEnhance.Contrast(img_gray)
        final_img = enhancer.enhance(1.5)

        return final_img
    except Exception as e:
        raise ValueError(f"Image processing failed: {e}")