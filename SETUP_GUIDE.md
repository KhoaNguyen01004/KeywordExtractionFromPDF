# Logistics Data Extraction - Hướng Dẫn Thiết Lập

## Tính Năng Chính

✅ **Trích xuất dữ liệu Logistics** từ PDF, hình ảnh sử dụng AI (Google Generative AI)
✅ **Hỗ trợ Multiple Document Types**: Invoice, Packing List, Bill of Lading, Customs Declaration
✅ **Tự động chuyển đổi đơn vị**: LBS → KG, Tấn → KG
✅ **Đối chiếu dữ liệu** giữa các chứng từ (Cross-validation)
✅ **Cảnh báo Lỗi & Cảnh báo** (Error/Warning flags)
✅ **Trích xuất mã HS** tự động

---

## Yêu Cầu Hệ Thống

- Python 3.9+
- pip (Python Package Manager)

---

## Cài Đặt

### 1. Clone hoặc Tải Project
```bash
cd d:\Code\PhuongNghiHelp\KeywordExtractionFromPDF
```

### 2. Tạo Virtual Environment
```bash
python -m venv venv
```

### 3. Kích Hoạt Virtual Environment

**Windows:**
```bash
venv\Scripts\Activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### 4. Cài Đặt Dependencies
```bash
pip install -r requirements.txt
```

### 5. Cấu Hình Biến Môi Trường

Tạo file `.env` trong thư mục gốc:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

**Cách lấy GEMINI_API_KEY:**
1. Truy cập [Google AI Studio](https://aistudio.google.com/)
2. Đăng nhập với tài khoản Google
3. Tạo API key mới
4. Sao chép key vào file `.env`

---

## Chạy Ứng Dụng

### Khởi Động Server
```bash
python -m backend.app
```

Server sẽ chạy tại: `http://localhost:5000`

### Frontend
Mở trình duyệt và truy cập: `http://localhost:5000`

---

## Cấu Trúc Dự Án

```
KeywordExtractionFromPDF/
├── backend/
│   ├── __init__.py
│   ├── app.py                          # Flask app chính
│   ├── config.py                       # Cấu hình
│   ├── extractor/
│   │   ├── __init__.py
│   │   ├── base.py                     # Base class cho extractor
│   │   ├── pdf_processor.py            # Xử lý PDF
│   │   ├── text_extractor.py           # Trích xuất text
│   │   ├── customs_extractor.py        # Legacy extractor
│   │   └── ai_extractor.py             # 🆕 AI-powered extractor
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── api.py                      # API routes
│   │   └── web.py                      # Web routes
│   ├── services/
│   │   ├── __init__.py
│   │   └── validator.py                # 🆕 Cross-validation logic
│   └── utils/
│       ├── __init__.py
│       └── helpers.py                  # Utility functions
├── frontend/
│   └── index.html                      # Frontend
├── .env                                # Environment variables
├── requirements.txt                    # Python dependencies
├── API_DOCUMENTATION.md                # 🆕 API Documentation
└── README.md
```

---

## Cách Sử Dụng API

### Upload và Trích Xuất Dữ Liệu

#### cURL
```bash
curl -X POST http://localhost:5000/api/extract-all \
  -F "file=@invoice.pdf" \
  -F "file=@packing_list.pdf" \
  -F "file=@bill_of_lading.pdf"
```

#### Python
```python
import requests

files = [
    ('file', open('invoice.pdf', 'rb')),
    ('file', open('packing_list.pdf', 'rb')),
    ('file', open('bill_of_lading.pdf', 'rb'))
]

response = requests.post(
    'http://localhost:5000/api/extract-all',
    files=files
)

result = response.json()
print(f"Status: {result['validation']['summary']['status']}")
for doc in result['extracted_documents']:
    print(f"Document: {doc['doc_type']}")
    print(f"BL No: {doc['bl_no']}")
```

#### JavaScript
```javascript
const formData = new FormData();
formData.append('file', document.getElementById('invoiceInput').files[0]);
formData.append('file', document.getElementById('plInput').files[0]);
formData.append('file', document.getElementById('blInput').files[0]);

fetch('/api/extract-all', {
    method: 'POST',
    body: formData
})
.then(res => res.json())
.then(data => {
    console.log('Extracted Data:', data.extracted_documents);
    console.log('Validation Status:', data.validation.summary.status);
});
```

---

## Module Chi Tiết

### 1. AIExtractor (`backend/extractor/ai_extractor.py`)

**Chính:** Trích xuất dữ liệu từ tài liệu sử dụng Google Generative AI

**Classes:**
- `LogisticsData` - Schema Pydantic để định nghĩa cấu trúc dữ liệu
- `Container` - Model cho thông tin container
- `AIExtractor` - Lớp chính để trích xuất dữ liệu

**Methods:**
```python
extractor = AIExtractor()
data = extractor.extract_data('path/to/file.pdf')
# Returns: LogisticsData object
```

### 2. Validator (`backend/services/validator.py`)

**Chức Năng:** So sánh dữ liệu từ nhiều tài liệu

**Classes:**
- `FlagStatus` - Enum (ERROR, WARNING)
- `ValidationFlag` - Model cho flag validation
- `CrossCheckValidator` - Validator chính

**Methods:**
```python
validator = CrossCheckValidator()
flags = validator.cross_check([doc1, doc2, doc3])
summary = validator.generate_summary(flags)
```

**Validation Rules:**
- ✓ BL number consistency
- ✓ Container numbers consistency
- ✓ Weight tolerance (> 5kg = warning)
- ✓ Package count matching
- ✓ Shipper/Consignee consistency

### 3. Routes (`backend/routes/api.py`)

**Endpoints:**
- `POST /api/extract` - Trích xuất từ 1 file (legacy)
- `POST /api/extract-all` - 🆕 Trích xuất từ nhiều file + validation
- `GET /api/fields` - Danh sách trường trích xuất
- `GET /api/config` - Cấu hình hiện tại

---

## Các Trường Dữ Liệu Trích Xuất

| Trường | Kiểu | Mô Tả |
|--------|------|--------|
| `doc_type` | string | Loại tài liệu (Invoice/PL/BL/Customs) |
| `bl_no` | string | Số vận đơn |
| `invoice_no` | string | Số hóa đơn |
| `shipper` | string | Tên người xuất khẩu |
| `consignee` | string | Tên người nhập khẩu |
| `vessel` | string | Tên tàu |
| `containers` | array | Danh sách container |
| `total_weight` | number | Trọng lượng tổng (KG) |
| `total_packages` | integer | Số kiện |
| `hs_code_suggestions` | array | Mã HS gợi ý |

---

## Troubleshooting

### Lỗi: `GEMINI_API_KEY not found`
**Giải pháp:**
- Kiểm tra file `.env` có tồn tại
- Kiểm tra biến `GEMINI_API_KEY` đã được cấu hình đúng

### Lỗi: `ModuleNotFoundError`
**Giải pháp:**
```bash
pip install -r requirements.txt
```

### Lỗi: Port 5000 đã được sử dụng
**Giải pháp:** Thay đổi port trong `backend/config.py`:
```python
FLASK_PORT = 5001  # hoặc port khác
```

### Timeout khi xử lý file lớn
**Giải pháp:**
- Giảm size file hoặc chia thành nhiều phần
- Chờ Google Generative AI xử lý (có thể mất 20-30 giây)

---

## Performance Tips

1. **Batch Processing**: Gửi từ 2-3 files cùng lúc để tối ưu hóa
2. **File Quality**: Tài liệu rõ ràng sẽ cho kết quả tốt hơn
3. **API Rate Limiting**: Google Generative AI có giới hạn request/phút
4. **Caching**: Có thể cache kết quả để tránh re-processing

---

## Contributing

Để đóng góp, vui lòng:
1. Fork repository
2. Tạo branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -am 'Add feature'`
4. Push: `git push origin feature/your-feature`
5. Mở Pull Request

---

## License

MIT License - Xem file LICENSE để chi tiết

---

## Support

Nếu có vấn đề, vui lòng tạo issue hoặc liên hệ dev team.
