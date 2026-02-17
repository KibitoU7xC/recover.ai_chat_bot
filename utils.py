# utils.py
import re
import io
import fitz  # PyMuPDF
from PIL import Image, ImageEnhance
import docx

# --- PII SCRUBBER (Text) ---
def sanitize_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', "[REDACTED_EMAIL]", text)
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', "[REDACTED_PHONE]", text)
    return text

# --- PDF TO IMAGES (For Scanned Docs) ---
def convert_pdf_to_images(file_bytes: bytes) -> list[Image.Image]:
    """Converts a PDF into a list of PIL Images (one per page)."""
    images = []
    try:
        # Open PDF from memory
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        
        # Limit to first 5 pages to prevent crashing on huge files
        for i, page in enumerate(doc):
            if i >= 5: break 
            
            # Render page to image (pixmap)
            pix = page.get_pixmap()
            
            # Convert to PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(img)
    except Exception as e:
        print(f"Error converting PDF to images: {e}")
    return images

# --- TEXT EXTRACTOR (For Digital Docs) ---
def extract_text_from_file(file_bytes: bytes, content_type: str) -> str:
    text = ""
    try:
        if "word" in content_type or "docx" in content_type:
            doc = docx.Document(io.BytesIO(file_bytes))
            for para in doc.paragraphs:
                text += para.text + "\n"
        elif "text" in content_type:
            text = file_bytes.decode("utf-8")
    except Exception as e:
        return f"Error reading document: {str(e)}"
    return sanitize_text(text)

# --- IMAGE PROCESSOR ---
def process_image(image_bytes: bytes) -> Image.Image:
    try:
        img = Image.open(io.BytesIO(image_bytes))
        # Strip EXIF & Enhance
        data = list(img.getdata())
        img_without_exif = Image.new(img.mode, img.size)
        img_without_exif.putdata(data)
        
        # Convert to Grayscale & Contrast (Helps OCR)
        img_gray = img_without_exif.convert("L")
        enhancer = ImageEnhance.Contrast(img_gray)
        return enhancer.enhance(1.5)
    except Exception as e:
        raise ValueError(f"Image processing failed: {e}")