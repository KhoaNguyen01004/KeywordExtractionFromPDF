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
            # Prepare prompt for extraction - Bilingual Vietnamese/English
            prompt = """Extract logistics information from this document.

**CRITICAL: This document contains BOTH Vietnamese AND English text. You MUST extract from BOTH languages!**

**LANGUAGE REQUIREMENTS:**
- Look for field labels in Vietnamese: "Số vận đơn", "Người xuất khẩu", "Người nhập khẩu", "Mã số hàng hóa", "Địa điểm lưu kho", "Địa điểm dỡ hàng", "Ngày hàng đến", "Ngày hàng đi", "Số container", "Số seal", "Số lượng", "Trọng lượng", "Số hóa đơn", "Tên tàu", "Mã bộ phận xử lý tờ khai"
- Look for field labels in English: "B/L No", "Shipper", "Consignee", "HS Code", "Warehouse Location", "Discharge Place", "Arrival Date", "Departure Date", "Container No", "Seal No", "Quantity", "Weight", "Invoice No", "Vessel", "Declaration Office Code"
- The SAME information may appear in BOTH languages - extract whichever you find

**CRITICAL EXTRACTION RULES:**
1. EXTRACT THE COMPLETE VALUE - don't truncate or skip any part!
2. For "Địa điểm lưu kho" / "Warehouse Location": Extract EVERYTHING (e.g., "02CIS01 TONG CTY TAN CANG SG")
3. For "Địa điểm dỡ hàng" / "Discharge Place": Extract COMPLETE place (e.g., "VNCLI CANG CAT LAI (HCM)")
4. For company names: Extract the FULL company name, don't abbreviate
5. For addresses: Extract the complete address including all text
6. For numbers/codes: Extract every digit/character exactly as shown

**YOU MUST INCLUDE ALL THESE FIELDS IN YOUR JSON (extract from either Vietnamese OR English labels):**

| Field | Vietnamese Label | English Label |
|-------|-----------------|---------------|
| doc_type | Loại tài liệu | Document Type |
| bl_no | Số vận đơn | B/L No, Bill of Lading No |
| invoice_no | Số hóa đơn | Invoice No |
| shipper | Người xuất khẩu | Shipper, Exporter |
| consignee | Người nhập khẩu | Consignee, Importer |
| vessel | Tên tàu | Vessel |
| hs_code | Mã số hàng hóa | HS Code, Commodity Code |
| declaration_office_code | Mã bộ phận xử lý tờ khai | Declaration Office Code |
| warehouse_location | Địa điểm lưu kho | Warehouse Location |
| discharge_place | Địa điểm dỡ hàng | Discharge Place, Place of Discharge |
| departure_date | Ngày hàng đi | Departure Date, ETD |
| arrival_date | Ngày hàng đến | Arrival Date, ETA |
| total_packages | Số lượng | Quantity, Packages, No. of Packages |
| total_weight | Trọng lượng | Weight, Gross Weight |
| container_no | Số container | Container No |
| seal_no | Số seal | Seal No |

**JSON OUTPUT FORMAT:**
{
  "doc_type": "Invoice" | "Packing List" | "Bill of Lading" | "Customs Declaration",
  "bl_no": "Complete B/L number",
  "invoice_no": "Invoice number", 
  "shipper": "Full company name",
  "consignee": "Full company name",
  "vessel": "Vessel name",
  "hs_code": "Complete HS code (e.g., 8471.30.00)",
  "declaration_office_code": "Code",
  "warehouse_location": "Complete warehouse location with code and name",
  "discharge_place": "Complete discharge place",
  "departure_date": "DD/MM/YYYY or date format found",
  "arrival_date": "DD/MM/YYYY or date format found",
  "total_packages": number,
  "total_weight": number,
  "containers": [{"container_no": "...", "seal_no": "..."}],
  "hs_code_suggestions": ["HS code"]
}

**IMPORTANT:** 
- If a field appears in BOTH Vietnamese and English, extract the value only once
- If one language is incomplete, check the other language
- NEVER return null if the value exists somewhere in the document
- Check EVERY PAGE thoroughly - information may be spread across multiple pages
- Extract ALL container numbers if multiple containers exist"""


            
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
