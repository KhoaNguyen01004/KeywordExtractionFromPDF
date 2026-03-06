"""
OCR Processor Module - Converts PDF/Image to text using Google Vision API or EasyOCR.
Provides intelligent text extraction with support for Vietnamese documents.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

# Try to import Google Vision API, fall back to EasyOCR
VISION_API_AVAILABLE = False
EASYOCR_AVAILABLE = False

try:
    from google.cloud import vision
    VISION_API_AVAILABLE = True
except ImportError:
    pass

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    pass

import PyPDF2
from PIL import Image
import io


@dataclass
class OCRResult:
    """Result from OCR processing."""
    full_text: str
    text_blocks: List[Dict]  # List of {text, confidence, location}
    language_detected: str
    processing_method: str  # 'google_vision', 'easyocr', 'pdf_text'


class OCRProcessor:
    """
    Optical Character Recognition processor for logistics documents.
    Supports PDF and image files (JPG, PNG, etc.)
    """

    def __init__(self, use_google_vision: bool = True):
        """
        Initialize OCR processor.
        
        Args:
            use_google_vision: Try to use Google Vision API if available
        """
        self.use_google_vision = use_google_vision and VISION_API_AVAILABLE
        self.use_easyocr = EASYOCR_AVAILABLE
        
        if self.use_google_vision:
            self.vision_client = vision.ImageAnnotatorClient()
            print("✓ Google Vision API initialized")
        
        if self.use_easyocr:
            # Initialize EasyOCR reader for Vietnamese & English
            self.ocr_reader = easyocr.Reader(['en', 'vi'], gpu=False)
            print("✓ EasyOCR initialized (EN, VI)")

    def extract_from_pdf(self, pdf_path: str) -> OCRResult:
        """
        Extract text from PDF file.
        First tries to extract native text, then falls back to OCR if needed.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            OCRResult object with extracted text
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Try to extract native text from PDF first
        native_text = self._extract_native_pdf_text(pdf_path)
        
        if native_text and len(native_text.strip()) > 100:
            # PDF has extractable text
            return OCRResult(
                full_text=native_text,
                text_blocks=[],
                language_detected="mixed",
                processing_method="pdf_native"
            )
        
        # PDF is image-based or low quality text, use OCR
        # Convert PDF to images
        images = self._pdf_to_images(pdf_path)
        
        all_text = []
        all_blocks = []
        
        for img_array in images:
            result = self._ocr_image(img_array)
            all_text.append(result.full_text)
            all_blocks.extend(result.text_blocks)
        
        combined_text = "\n---PAGE BREAK---\n".join(all_text)
        
        return OCRResult(
            full_text=combined_text,
            text_blocks=all_blocks,
            language_detected="mixed",
            processing_method="ocr_image"
        )

    def extract_from_image(self, image_path: str) -> OCRResult:
        """
        Extract text from image file (JPG, PNG, etc.)
        
        Args:
            image_path: Path to image file
            
        Returns:
            OCRResult object with extracted text
        """
        image_path = Path(image_path)
        
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        # Load image
        image = Image.open(image_path)
        image_array = self._image_to_array(image)
        
        # Process with OCR
        result = self._ocr_image(image_array)
        
        return result

    def _extract_native_pdf_text(self, pdf_path: Path) -> str:
        """Extract native text from PDF without OCR."""
        try:
            text = []
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page_num, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text.append(page_text)
            
            return "\n".join(text)
        except Exception as e:
            print(f"Warning: Failed to extract native PDF text: {e}")
            return ""

    def _pdf_to_images(self, pdf_path: Path, dpi: int = 150) -> List:
        """
        Convert PDF pages to images.
        Requires pdf2image or PyMuPDF.
        """
        try:
            from pdf2image import convert_from_path
            images = convert_from_path(pdf_path, dpi=dpi)
            return images
        except ImportError:
            # Fallback to PyMuPDF
            import fitz
            pdf_doc = fitz.open(pdf_path)
            images = []
            for page_num in range(len(pdf_doc)):
                page = pdf_doc[page_num]
                pix = page.get_pixmap(matrix=fitz.Matrix(dpi/72, dpi/72))
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                images.append(img)
            return images

    def _ocr_image(self, image) -> OCRResult:
        """
        Process image with OCR (Google Vision or EasyOCR).
        """
        if self.use_google_vision:
            return self._google_vision_ocr(image)
        elif self.use_easyocr:
            return self._easyocr_ocr(image)
        else:
            raise RuntimeError("No OCR engine available. Install google-cloud-vision or easyocr")

    def _google_vision_ocr(self, image) -> OCRResult:
        """
        Use Google Vision API for OCR.
        Requires GOOGLE_APPLICATION_CREDENTIALS environment variable.
        """
        # Convert PIL image to bytes
        image_bytes = io.BytesIO()
        image.save(image_bytes, format='JPEG')
        image_bytes = image_bytes.getvalue()
        
        # Call Google Vision API
        from google.cloud.vision_v1 import types
        
        image_content = types.Image(content=image_bytes)
        response = self.vision_client.document_text_detection(image=image_content)
        
        # Extract full text
        full_text = response.full_text_annotation.text
        
        # Extract text blocks with confidence
        text_blocks = []
        for page in response.full_text_annotation.pages:
            for block in page.blocks:
                for paragraph in block.paragraphs:
                    block_text = ''.join([
                        symbol.text for line in paragraph.lines
                        for word in line.words
                        for symbol in word.symbols
                    ])
                    
                    # Get confidence
                    confidence = paragraph.confidence
                    
                    text_blocks.append({
                        'text': block_text,
                        'confidence': confidence,
                        'location': None
                    })
        
        return OCRResult(
            full_text=full_text,
            text_blocks=text_blocks,
            language_detected="mixed",
            processing_method="google_vision"
        )

    def _easyocr_ocr(self, image) -> OCRResult:
        """
        Use EasyOCR for text recognition.
        """
        # Convert PIL image to numpy array if needed
        if isinstance(image, Image.Image):
            import numpy as np
            image_array = np.array(image)
        else:
            image_array = image
        
        # Run OCR
        results = self.ocr_reader.readtext(image_array)
        
        # Extract text and build blocks
        full_text = []
        text_blocks = []
        
        for (bbox, text, confidence) in results:
            full_text.append(text)
            text_blocks.append({
                'text': text,
                'confidence': confidence,
                'location': {'bbox': bbox}
            })
        
        return OCRResult(
            full_text="\n".join(full_text),
            text_blocks=text_blocks,
            language_detected="mixed",
            processing_method="easyocr"
        )

    def _image_to_array(self, image):
        """Convert PIL Image to array."""
        return image

    def preprocess_for_ocr(self, image_path: str, output_path: Optional[str] = None):
        """
        Preprocess image for better OCR results.
        - Increase contrast
        - Denoise
        - Deskew
        """
        try:
            import cv2
            import numpy as np
            
            # Read image
            img = cv2.imread(str(image_path))
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Increase contrast
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            contrast = clahe.apply(gray)
            
            # Denoise
            denoised = cv2.fastNlMeansDenoising(contrast)
            
            # Threshold
            _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            if output_path:
                cv2.imwrite(output_path, thresh)
            
            return thresh
        except ImportError:
            print("Warning: OpenCV not available. Skipping image preprocessing.")
            return None


# Singleton instance
_ocr_processor = None

def get_ocr_processor() -> OCRProcessor:
    """Get or create OCR processor instance."""
    global _ocr_processor
    if _ocr_processor is None:
        _ocr_processor = OCRProcessor()
    return _ocr_processor
