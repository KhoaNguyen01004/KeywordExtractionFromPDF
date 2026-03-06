"""
AI-powered logistics document extractor using Google Genai SDK (NEW).
Uses response_schema for automatic JSON parsing.
"""

import os
import time
import base64
import json
import re
from typing import List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from google import genai
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY not found in environment variables")

# Configure Gemini API
# Client will be created per-instance to force API v1 and avoid v1beta model lookup issues


class Container(BaseModel):
    """Model for container information."""
    container_no: str = Field(description="Container number")
    seal_no: Optional[str] = Field(None, description="Seal number")


class LogisticsData(BaseModel):
    """Pydantic schema for extracted logistics data."""
    doc_type: str = Field(description="Document type: Invoice/PL/BL/Customs")
    bl_no: Optional[str] = Field(None, description="Bill of lading number")
    invoice_no: Optional[str] = Field(None, description="Invoice number")
    shipper: Optional[str] = Field(None, description="Exporter/Shipper name")
    consignee: Optional[str] = Field(None, description="Importer/Consignee name")
    vessel: Optional[str] = Field(None, description="Vessel name")
    containers: Optional[List[Container]] = Field(default_factory=list, description="List of containers")
    total_weight: Optional[float] = Field(None, description="Total weight in KG")
    total_packages: Optional[int] = Field(None, description="Total number of packages")
    hs_code_suggestions: Optional[List[str]] = Field(default_factory=list, description="Suggested HS codes")
    # Additional fields for Vietnamese customs
    hs_code: Optional[str] = Field(None, description="HS Code / Mã số hàng hóa")
    declaration_office_code: Optional[str] = Field(None, description="Declaration office code / Mã bộ phận xử lý tờ khai")
    warehouse_location: Optional[str] = Field(None, description="Warehouse location / Địa điểm lưu kho")
    discharge_place: Optional[str] = Field(None, description="Place of discharge / Địa điểm dỡ hàng")
    departure_date: Optional[str] = Field(None, description="Departure date / Ngày hàng đi")
    arrival_date: Optional[str] = Field(None, description="Arrival date / Ngày hàng đến")


class AIExtractor:
    """Logistics document extractor using Gemini 1.5 Flash."""
    
    def __init__(self):
        """Initialize with Gemini API client."""
        # Force SDK to use API v1 to avoid v1beta model lookup errors
        self.client = genai.Client(api_key=GEMINI_API_KEY, http_options={"api_version": "v1"})
        # Use a model that exists in your account (choose from the listed models)
        # Models returned earlier: models/gemini-2.5-flash, models/gemini-2.5-pro, models/gemini-2.0-flash, ...
        # Use the short name (no 'models/' prefix)
        self.model_name = "gemini-2.5-flash"
    
    def _get_mime_type(self, file_path: str) -> str:
        """Detect MIME type from file extension."""
        if file_path.lower().endswith('.pdf'):
            return "application/pdf"
        elif file_path.lower().endswith(('.jpg', '.jpeg')):
            return "image/jpeg"
        elif file_path.lower().endswith('.png'):
            return "image/png"
        elif file_path.lower().endswith('.gif'):
            return "image/gif"
        elif file_path.lower().endswith('.webp'):
            return "image/webp"
        else:
            return "application/octet-stream"
    
    @retry(
        # Only retry on rate-limit / RESOURCE_EXHAUSTED errors; don't retry on 4xx client errors
        wait=wait_exponential(multiplier=2, min=10, max=60),
        stop=stop_after_attempt(3),
        retry=retry_if_exception(lambda exc: isinstance(exc, Exception) and ("429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc))),
        reraise=True
    )
    def extract_data(self, file_path: str) -> LogisticsData:
        """
        Extract logistics data using Gemini 1.5 Flash with structured output.
        
        Args:
            file_path: Path to document file
            
        Returns:
            LogisticsData object with extracted information
            
        Raises:
            ValueError: If file not found
            Exception: If API call fails
        """
        if not os.path.exists(file_path):
            raise ValueError(f"File not found: {file_path}")
        
        filename = os.path.basename(file_path)
        print(f"📄 Processing: {filename}")
        
        # Read and encode file to base64
        with open(file_path, "rb") as f:
            file_bytes = f.read()
            base64_data = base64.standard_b64encode(file_bytes).decode("utf-8")
        
        mime_type = self._get_mime_type(file_path)
        
        print(f"🔄 Calling Gemini API ({self.model_name})...")
        start_time = time.time()
        
        try:
            # Prepare prompt for extraction
            prompt = """Extract logistics information from this Vietnamese customs/logistics document.

IMPORTANT: This is a Vietnamese customs document. You MUST extract ALL fields below. Read the entire document carefully.

CRITICAL: EXTRACT THE COMPLETE VALUE AFTER EACH LABEL, NOT PARTIAL!
- For "Địa điểm lưu kho": Extract EVERYTHING on the same line (e.g., "02CIS01 TONG CTY TAN CANG SG")
- For "Địa điểm dỡ hàng": Extract COMPLETE place name (e.g., "VNCLI CANG CAT LAI (HCM)")
- DO NOT truncate values - extract EVERY word!

YOU MUST INCLUDE ALL THESE FIELDS IN YOUR JSON RESPONSE:
1. "doc_type": Must be one of: Invoice, Packing List, Bill of Lading, Customs Declaration
2. "Địa điểm lưu kho" - COMPLETE value including code AND name
3. "Địa điểm dỡ hàng" - COMPLETE value
4. "Ngày hàng đến" - Format: DD/MM/YYYY
5. "Ngày hàng đi" - Format: DD/MM/YYYY
6. "Số vận đơn" - Complete number
7. "Mã số hàng hóa" - Complete code
8. "Người xuất khẩu" - Full company name
9. "Người nhập khẩu" - Full company name
10. "Mã bộ phận xử lý tờ khai"
11. "Số container"
12. "Số seal"
13. "Số lượng"
14. "Trọng lượng"
15. "Số hóa đơn"
16. "Tên tàu"

IMPORTANT: Your JSON response MUST include ALL fields including doc_type. Don't skip any fields!

JSON format:
{
  "doc_type": "Invoice" or "Packing List" or "Bill of Lading" or "Customs Declaration",
  "warehouse_location": "COMPLETE warehouse location with code and name",
  "discharge_place": "COMPLETE discharge place with all text",
  "arrival_date": "DD/MM/YYYY or null",
  "departure_date": "DD/MM/YYYY or null",
  "bl_no": "Complete B/L number or null",
  "hs_code": "Complete HS code or null",
  "shipper": "Complete exporter name or null",
  "consignee": "Complete importer name or null",
  "declaration_office_code": "Complete code or null",
  "invoice_no": "Invoice number or null",
  "vessel": "Vessel name or null",
  "total_weight": number or null,
  "total_packages": number or null,
  "containers": [{"container_no": "...", "seal_no": "..."}] or [],
  "hs_code_suggestions": ["HS code"] or []
}

Extract EVERY WORD - don't skip or truncate anything! Include ALL fields in the JSON!"""
            
            # Call Gemini API without unsupported `config` keys to avoid 400 INVALID_ARGUMENT
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[
                    {
                        "role": "user",
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": base64_data
                                }
                            }
                        ]
                    }
                ]
            )

            api_time = time.time() - start_time
            print(f"✓ API response received ({api_time:.1f}s)")

            # If the SDK produced a parsed object, use it directly
            if hasattr(response, "parsed") and response.parsed:
                parsed = response.parsed
                # If parsed is already a Pydantic model instance, return it
                if isinstance(parsed, LogisticsData):
                    print("✅ Extraction successful (parsed object)!")
                    return parsed
                # If parsed is a dict, validate and return
                if isinstance(parsed, dict):
                    logistics_data = LogisticsData(**parsed)
                    print("✅ Extraction successful (parsed dict)!")
                    return logistics_data

            # Fallback to parsing raw text if parsed not available
            response_text = response.text.strip()
            try:
                extracted_json = json.loads(response_text)
            except json.JSONDecodeError:
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    extracted_json = json.loads(json_match.group())
                else:
                    raise ValueError(f"Could not parse JSON from response: {response_text}")

            logistics_data = LogisticsData(**extracted_json)
            print("✅ Extraction successful (parsed fallback)!")
            return logistics_data
        
        except Exception as e:
            error_str = str(e)
            
            if "404" in error_str or "not found" in error_str.lower():
                print("❌ Error 404: Model not found. Try gemini-1.5-pro or gemini-2.0-flash")
            elif "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                print("⚠️ Rate limit (429). Waiting before retry...")
                time.sleep(10)
            elif "PERMISSION_DENIED" in error_str or "permission" in error_str.lower():
                print("❌ Permission denied. Check API key in .env")
            
            raise
    
    def extract_data_batch(self, file_paths: List[str]) -> List[LogisticsData]:
        """
        Extract data from multiple files with rate limit handling.
        
        Args:
            file_paths: List of file paths
            
        Returns:
            List of LogisticsData objects
        """
        results = []
        for i, file_path in enumerate(file_paths):
            # Add delay between requests to avoid rate limits
            if i > 0:
                print(f"⏳ Waiting 3 seconds before next file...")
                time.sleep(3)
            
            try:
                data = self.extract_data(file_path)
                results.append(data)
            except Exception as e:
                print(f"❌ Failed to extract {file_path}: {str(e)}")
                raise
        
        return results
