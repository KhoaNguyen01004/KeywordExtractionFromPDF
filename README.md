# Logistics Data Extraction & Validation System

A comprehensive web application for intelligent extraction and validation of logistics data from Vietnamese customs documents. Features advanced AI-powered OCR, cross-document validation, database storage, and professional reporting capabilities.

## Features

- **AI-Powered Data Extraction**: Uses Google Gemini AI for intelligent document analysis
- **Multi-Format Support**: PDF, JPG, PNG, GIF, WEBP
- **Advanced Validation**: Cross-document consistency checking with severity-based flagging (CRITICAL, ERROR, WARNING, INFO)
- **Database Storage**: Supabase PostgreSQL for session history and validation records
- **Professional Reporting**: Session tracking with comparison tables and quality metrics
- **Docker Support**: Ready for deployment with Docker and Docker Compose

## Quick Start

### 1. Environment Setup

1. **Create Supabase Project**:
   - Go to [supabase.com](https://supabase.com) and create a new project
   - Note your Project URL and anon/public key

2. **Set Environment Variables**:
   Create a `.env` file with your credentials:
   ```
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-anon-key-here
   GEMINI_API_KEY=your-google-gemini-api-key
   ```

3. **Create Database Tables**:
   - Open Supabase Dashboard → SQL Editor
   - Run the SQL from `backend/database/schema.sql`

### 2. Installation

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
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
                       │ • Google Gemini │
                       │ • OCR Processing│
                       │ • Validation    │
                       └─────────────────┘
```

## Core Components

### Data Extraction Pipeline

1. **Document Upload**: Multi-format support (PDF, images)
2. **OCR Processing**: EasyOCR for Vietnamese/English text extraction
3. **AI Analysis**: Google Gemini extracts structured logistics data
4. **Validation Layer**: Cross-document consistency checks
5. **Database Storage**: Session history and validation records

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

### Extracted Fields

| Field | Description |
|-------|-------------|
| `doc_type` | Document type (Invoice/PL/BL/Customs) |
| `bl_no` | Bill of Lading number |
| `invoice_no` | Invoice number |
| `shipper` | Exporter name |
| `consignee` | Importer name |
| `vessel` | Vessel name |
| `containers` | List of containers |
| `total_weight` | Total weight (KG) |
| `total_packages` | Total packages |
| `hs_code` | HS code |
| `hs_code_suggestions` | Suggested HS codes |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/extract` | Extract data from single document |
| POST | `/api/extract-all` | Extract and validate multiple documents |
| GET | `/api/session/{session_id}` | Get session history |
| GET | `/api/sessions` | List recent sessions (paginated) |
| GET | `/api/statistics` | System statistics |
| GET | `/api/fields` | List extraction fields |
| GET | `/api/document-types` | Available document types |
| GET | `/api/config` | Current configuration |
| GET | `/api/save-comparison` | Save user comparison data |
| GET | `/api/qc-report/{session_id}` | Generate QC report |

### POST /api/extract

Extract data from a single document.

```bash
curl -X POST http://localhost:5000/api/extract \
  -F "file=@document.pdf"
```

### POST /api/extract-all

Extract and validate multiple documents simultaneously.

```bash
curl -X POST http://localhost:5000/api/extract-all \
  -F "file=@invoice.pdf" \
  -F "file=@packing_list.pdf" \
  -F "file=@bill_of_lading.pdf"
```

Response:
```json
{
  "success": true,
  "session_id": "...",
  "extracted_documents": [...],
  "validation": {
    "issues": [...],
    "summary": {
      "total_issues": 0,
      "critical": 0,
      "errors": 0,
      "warnings": 0,
      "info": 0
    }
  }
}
```

## Project Structure

```
KeywordExtractionFromPDF/
├── README.md                      # This file
├── API_DOCUMENTATION.md           # Detailed API reference
├── CHANGELOG.md                   # Version history
├── requirements.txt               # Python dependencies
├── run.py                         # Application entry point
├── Procfile                       # Heroku deployment
├── Dockerfile                     # Docker configuration
├── runtime.txt                    # Python version
├── backend/
│   ├── __init__.py
│   ├── app.py                     # Flask application
│   ├── config.py                  # Configuration settings
│   ├── database/
│   │   ├── manager.py             # Supabase database operations
│   │   └── schema.sql             # Database schema
│   ├── extractor/
│   │   ├── __init__.py
│   │   ├── ai_extractor.py        # Google Gemini integration
│   │   ├── base.py                # BaseExtractor class
│   │   ├── customs_extractor.py   # Legacy customs extractor
│   │   ├── ocr_processor.py       # OCR processing
│   │   ├── pdf_processor.py       # PDF text extraction
│   │   └── text_extractor.py      # Text extraction
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── api.py                 # API endpoints
│   │   └── web.py                 # Web routes
│   ├── services/
│   │   ├── __init__.py
│   │   ├── advanced_validator.py   # Cross-document validation
│   │   ├── report_generator.py    # Report generation
│   │   └── validator.py           # Legacy validator
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
├── frontend/
│   ├── index.html                 # Main HTML
│   ├── css/
│   │   └── styles.css            # Styles
│   └── js/
│       ├── config.js              # Configuration
│       ├── api.js                 # API functions
│       ├── ui.js                  # UI rendering
│       └── app.js                 # Main entry
├── pdf_examples/                   # Sample documents
└── venv/                           # Virtual environment
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | Supabase project URL | Yes |
| `SUPABASE_KEY` | Supabase anon key | Yes |
| `GEMINI_API_KEY` | Google Gemini API key | Yes |
| `FLASK_ENV` | Flask environment | No |
| `FLASK_DEBUG` | Enable debug mode | No |

## Troubleshooting

### Common Issues

1. **Supabase Connection Error**:
   - Verify `SUPABASE_URL` and `SUPABASE_KEY` in `.env`
   - Check Supabase project is active

2. **AI Extraction Fails**:
   - Verify `GEMINI_API_KEY` is valid
   - Check API rate limits

3. **PDF Processing Issues**:
   - Ensure PDF is not password protected
   - Check file is not corrupted

### Logs

Application logs are available in the terminal when running. Set `FLASK_DEBUG=true` for detailed logging.

## Docker Deployment

```bash
# Build Docker image
docker build -t logistics-extraction .

# Run container
docker run -p 5000:5000 --env-file .env logistics-extraction
```

## Technology Stack

- **Backend**: Flask 3.0.0 (Python)
- **AI**: Google Gemini API
- **OCR**: EasyOCR
- **PDF Processing**: PyMuPDF
- **Database**: Supabase PostgreSQL
- **Frontend**: HTML, CSS, Vanilla JavaScript

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with proper validation
4. Test with sample documents
5. Submit pull request

## License

MIT License

