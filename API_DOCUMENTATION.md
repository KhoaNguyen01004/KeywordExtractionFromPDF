# API Documentation - Logistics Data Extraction

## Tổng Quan

API này cung cấp các endpoint để trích xuất và xác thực dữ liệu Logistics từ các chứng từ (Invoice, Packing List, Bill of Lading, Customs Declaration).

---

## Endpoint: /api/extract-all

### Mô Tả
Trích xuất dữ liệu từ nhiều file chứng từ đồng thời và thực hiện đối chiếu dữ liệu.

### HTTP Method
**POST**

### URL
```
POST /api/extract-all
```

### Request

#### Header
```
Content-Type: multipart/form-data
```

#### Parameters
- **Files**: Danh sách các file (PDF, JPG, PNG, GIF, WEBP)
  - Hỗ trợ tối thiểu 2 file, tối đa không giới hạn
  - Tên file: `file`, `file0`, `file1`, ... hoặc `file[0]`, `file[1]`, ...

#### Ví dụ cURL
```bash
curl -X POST http://localhost:5000/api/extract-all \
  -F "file=@invoice.pdf" \
  -F "file=@packing_list.pdf" \
  -F "file=@bill_of_lading.pdf"
```

#### Ví dụ Python
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

print(response.json())
```

#### Ví dụ JavaScript (Fetch API)
```javascript
const formData = new FormData();
formData.append('file', document.getElementById('invoice').files[0]);
formData.append('file', document.getElementById('packing_list').files[0]);
formData.append('file', document.getElementById('bill_of_lading').files[0]);

fetch('/api/extract-all', {
    method: 'POST',
    body: formData
})
.then(res => res.json())
.then(data => console.log(data));
```

### Response

#### Success (200 OK)
```json
{
  "success": true,
  "extracted_documents": [
    {
      "doc_type": "Invoice",
      "bl_no": "BL123456789",
      "invoice_no": "INV-2024-001",
      "shipper": "Công ty ABC",
      "consignee": "Công ty XYZ",
      "vessel": "EVER GIVEN",
      "containers": [
        {
          "container_no": "CONTAINER001",
          "seal_no": "SEAL001"
        },
        {
          "container_no": "CONTAINER002",
          "seal_no": "SEAL002"
        }
      ],
      "total_weight": 5000.5,
      "total_packages": 100,
      "hs_code_suggestions": ["6204.62", "6204.63"]
    },
    {
      "doc_type": "Packing List",
      "bl_no": "BL123456789",
      "invoice_no": null,
      "shipper": "Công ty ABC",
      "consignee": "Công ty XYZ",
      "vessel": "EVER GIVEN",
      "containers": [
        {
          "container_no": "CONTAINER001",
          "seal_no": "SEAL001"
        },
        {
          "container_no": "CONTAINER002",
          "seal_no": "SEAL002"
        }
      ],
      "total_weight": 5000.5,
      "total_packages": 100,
      "hs_code_suggestions": ["6204.62", "6204.63"]
    }
  ],
  "validation": {
    "flags": [
      {
        "field": "total_weight",
        "status": "warning",
        "message": "Trọng lượng lệch nhau 2.50KG (> 5.00KG)",
        "details": {
          "weights": {
            "invoice": 5000.5,
            "packing_list": 4998.0
          },
          "difference": 2.5,
          "tolerance": 5.0
        }
      }
    ],
    "summary": {
      "total_issues": 1,
      "errors": 0,
      "warnings": 1,
      "error_details": [],
      "warning_details": [
        {
          "field": "total_weight",
          "status": "warning",
          "message": "Trọng lượng lệch nhau 2.50KG (> 5.00KG)",
          "details": {...}
        }
      ],
      "status": "WARNING"
    }
  }
}
```

#### Error (400/500)
```json
{
  "error": "No files provided"
}
```

---

## Schema LogisticsData

### Định Nghĩa
```python
class LogisticsData(BaseModel):
    doc_type: str                          # Loại chứng từ: Invoice/PL/BL/Customs
    bl_no: Optional[str]                   # Số vận đơn
    invoice_no: Optional[str]              # Số hóa đơn
    shipper: Optional[str]                 # Tên người xuất khẩu
    consignee: Optional[str]               # Tên người nhập khẩu
    vessel: Optional[str]                  # Tên tàu
    containers: List[Container]            # Danh sách container
    total_weight: float                    # Trọng lượng tổng cộng (KG)
    total_packages: int                    # Số kiện
    hs_code_suggestions: List[str]         # Mã HS gợi ý
```

### Container
```python
class Container(BaseModel):
    container_no: str                      # Số container
    seal_no: Optional[str]                 # Số seal
```

---

## Validation Rules

### Error (Cảnh báo Đỏ)
- **bl_no không khớp**: BL number khác nhau giữa các file
- **containers không khớp**: Container numbers thiếu hoặc khác nhau

### Warning (Cảnh báo Vàng)
- **total_weight lệch**: Trọng lượng lệch nhau > 5kg
- **total_packages không khớp**: Số kiện khác nhau
- **shipper không khớp**: Tên người xuất khác nhau
- **consignee không khớp**: Tên người nhập khác nhau
- **invoice_no thiếu**: Không tìm thấy số hóa đơn

---

## Unit Conversion

AI Extractor tự động chuyển đổi các đơn vị trọng lượng:
- **LBS → KG**: 1 LBS = 0.453592 KG
- **Tấn (Ton) → KG**: 1 Tấn = 1000 KG
- **KG**: Giữ nguyên

---

## Error Handling

| HTTP Code | Description |
|-----------|-------------|
| 200 | Thành công |
| 400 | Bad Request - File không hợp lệ hoặc thiếu |
| 500 | Internal Server Error - Lỗi xử lý server |

---

## Status Response

Trường `status` trong `validation.summary` có các giá trị:
- **PASSED**: Không có lỗi hoặc cảnh báo
- **WARNING**: Có cảnh báo nhưng không có lỗi
- **FAILED**: Có lỗi

---

## Lưu Ý

1. **Yêu cầu Environment**: Cần có `GEMINI_API_KEY` trong file `.env`
2. **File Size**: Không có giới hạn size cụ thể (phụ thuộc Google Generative AI)
3. **Processing Time**: Tùy thuộc vào độ phức tạp của tài liệu (5-30 giây)
4. **Ngôn Ngữ**: Hỗ trợ tài liệu tiếng Anh và tiếng Việt
