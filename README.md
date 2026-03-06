# Logistics Data Extraction & Validation System

A comprehensive web application for intelligent extraction and validation of logistics data from Vietnamese customs documents. Features advanced AI-powered OCR, cross-document validation, database storage, and professional reporting capabilities.

## Features

- **AI-Powered Data Extraction**: Uses Google GenAI for intelligent document analysis
- **Dual OCR System**: Google Cloud Vision API with EasyOCR fallback for Vietnamese/English text
- **Advanced Validation**: Cross-document consistency checking with severity-based flagging
- **Database Storage**: Supabase PostgreSQL for session history and validation records
- **Professional Reporting**: HTML/JSON reports with comparison tables and quality metrics
- **Modular Architecture**: Extensible design for multiple document types and validation rules

## Quick Start

### 1. Environment Setup

1. **Create Supabase Project**:
   - Go to [supabase.com](https://supabase.com) and create a new project
   - Note your Project URL and anon/public key

2. **Set Environment Variables**:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your credentials:
   ```
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-anon-key-here
   GOOGLE_API_KEY=your-google-ai-api-key
   ```

3. **Create Database Tables**:
   - Open Supabase Dashboard → SQL Editor
   - Run the SQL from `backend/database/schema.sql`

### 2. Installation

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 3. Run Application

```bash
python run.py
```

Open browser to: http://127.0.0.1:5000

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Frontend  │    │   Flask Backend  │    │   Supabase DB   │
│   (HTML/JS)     │◄──►│   API Routes      │◄──►│   PostgreSQL    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   AI Services   │
                       │ • Google GenAI  │
                       │ • OCR Processing│
                       │ • Validation    │
                       └─────────────────┘
```

## Core Components

### Data Extraction Pipeline

1. **Document Upload**: Multi-format support (PDF, images)
2. **OCR Processing**: Dual-engine OCR with Vietnamese language support
3. **AI Analysis**: Google GenAI extracts structured logistics data
4. **Validation Layer**: Cross-document consistency checks
5. **Database Storage**: Session history and validation records
6. **Report Generation**: Quality control reports and metrics

### Validation Features

- **Severity Levels**: CRITICAL, ERROR, WARNING, INFO
- **Cross-Document Checks**: BL vs Invoice, weight consistency, container validation
- **Smart Flagging**: Automatic issue detection with recommendations
- **Audit Trail**: Complete session history with timestamps

### Supported Document Types

- Customs Declarations (Tờ khai hải quan)
- Bills of Lading (Vận đơn)
- Commercial Invoices (Hóa đơn thương mại)
- Packing Lists (Danh sách đóng gói)

## API Endpoints

- `POST /api/upload` - Upload and process documents
- `GET /api/session/{session_id}` - Get session history
- `GET /api/sessions` - List recent sessions
- `GET /api/reports/{session_id}` - Generate validation report
- `GET /api/statistics` - System statistics

## Development

### Project Structure

```
backend/
├── app.py                 # Flask application
├── config.py             # Configuration settings
├── database/
│   ├── manager.py        # Supabase database operations
│   └── schema.sql        # Database schema
├── extractor/
│   ├── ai_extractor.py   # Google GenAI integration
│   ├── ocr_processor.py  # OCR processing pipeline
│   └── pdf_processor.py  # PDF text extraction
├── services/
│   ├── advanced_validator.py  # Cross-document validation
│   └── report_generator.py    # Report generation
└── routes/
    ├── api.py           # API endpoints
    └── web.py           # Web routes
```

### Adding New Document Types

1. Update `config.py` with new document configuration
2. Add extraction patterns in `ai_extractor.py`
3. Implement validation rules in `advanced_validator.py`
4. Update database schema if needed

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | Supabase project URL | Yes |
| `SUPABASE_KEY` | Supabase anon key | Yes |
| `GOOGLE_API_KEY` | Google AI API key | Yes |
| `FLASK_ENV` | Flask environment | No |

### Document Types Configuration

Add new document types in `backend/config.py`:

```python
DOCUMENT_TYPES = {
    "new_type": {
        "name": "New Document Type",
        "keys": ["field1", "field2", ...]
    }
}
```

## Troubleshooting

### Common Issues

1. **Supabase Connection Error**:
   - Verify `SUPABASE_URL` and `SUPABASE_KEY` in `.env`
   - Check Supabase project is active

2. **OCR Processing Fails**:
   - Ensure Google Cloud Vision API is enabled
   - Check API quotas and billing

3. **AI Extraction Issues**:
   - Verify `GOOGLE_API_KEY` is valid
   - Check API rate limits

### Logs

Application logs are available in the terminal when running. Set `FLASK_DEBUG=true` for detailed logging.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with proper validation
4. Test with sample documents
5. Submit pull request

## License

This project is licensed under the MIT License.

The extraction process:

| Key | Search Result | Extracted Value |
|-----|---------------|------------------|
| Số vận đơn | Found on line 1 | ABC123456 |
| Người xuất khẩu | Found on line 2, empty value | Công Ty TNHH ABC |

### Step 3: Result Aggregation

```
Extracted Values
        │
        ▼
┌─────────────────────────┐
│  Combine into JSON      │
│  {                      │
│    "key1": "value1",    │
│    "key2": "value2",    │
│    ...                  │
│  }                      │
└─────────────────────────┘
```

## API Endpoints

### POST /api/extract
Extract data from uploaded PDF.

**Request:**
- Content-Type: multipart/form-data
- Body: `file` (PDF file)

**Response:**
```json
{
  "success": true,
  "data": {
    "Số vận đơn": "ABC123456",
    "Mã số hàng hóa đại diện tờ khai": "...",
    ...
  }
}
```

### GET /api/fields
Get list of extraction fields.

**Response:**
```json
{
  "fields": ["Số vận đơn", "Mã số hàng hóa...", ...]
}
```

### GET /api/document-types
Get available document types.

**Response:**
```json
{
  [{"id": "customs_declaration "document_types":", "name": "Tờ khai hải quan", "field_count": 9}],
  "default": "customs_declaration"
}
```

### GET /health
Health check endpoint.

## Project Structure

```
KeywordExtractionFromPDF/
├── README.md                  # This file
├── requirements.txt           # Python dependencies
├── TODO.md                    # Project tasks
├── backend/
│   ├── __init__.py           # Package init
│   ├── app.py                # Flask application entry point
│   ├── config.py             # Configuration settings
│   ├── extractor/           # Extraction modules
│   │   ├── __init__.py
│   │   ├── base.py          # BaseExtractor class
│   │   ├── customs_extractor.py
│   │   ├── pdf_processor.py
│   │   └── text_extractor.py
│   ├── routes/              # Route handlers
│   │   ├── __init__.py
│   │   ├── api.py          # API endpoints
│   │   └── web.py          # Web routes
│   └── utils/              # Utility functions
│       ├── __init__.py
│       └── helpers.py
└── frontend/
    └── index.html          # User interface
```

## Extending the Application

### Adding New Extraction Keys

Edit `backend/config.py`:

```python
DEFAULT_EXTRACTION_KEYS = [
    "Số vận đơn",
    "Mã số hàng hóa đại diện tờ khai",
    "Mã bộ phận xử lý tờ khai",
    "Người xuất khẩu",
    "Người nhập khẩu",
    "Địa điểm lưu kho",
    "Địa điểm dỡ hàng",
    "Ngày hàng đi",
    "Ngày hàng đến",
    "New Key Here"  # Add your new key
]
```

### Adding New Document Types

```python
from backend.config import app_config

# Add new document type
app_config.add_document_type(
    type_name="bill_of_lading",
    name="Vận đơn",
    keys=["Số vận đơn", "Ngày phát hành", "Người gửi hàng"]
)
```

### Creating Custom Extractors

```python
from backend.extractor import BaseExtractor

class MyCustomExtractor(BaseExtractor):
    def __init__(self, extraction_keys=None):
        super().__init__(extraction_keys)
        # Initialize your dependencies
    
    def extract(self, document_content):
        # Your custom extraction logic
        extracted_data = {}
        # ... process document
        return extracted_data
    
    def validate(self, document_content):
        # Validate document
        return True
```

## Technology Stack

- **Backend**: Flask 3.0.0 (Python)
- **PDF Processing**: PyMuPDF 1.23.8
- **Frontend**: HTML, Tailwind CSS, Vanilla JavaScript
- **CORS**: Flask-CORS

## License

MIT License

