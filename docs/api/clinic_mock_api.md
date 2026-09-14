# Clinic Mock API contract

Base URL được cấu hình bằng `CLINIC_API_BASE_URL`. API sử dụng Bearer authentication qua header `Authorization`; token được đọc từ `CLINIC_API_KEY` và không được ghi vào source hoặc log.

## Endpoint dùng cho identity flow

### Tìm bệnh nhân theo số điện thoại

```http
GET /v1/patients?phone=<10-digit-vietnamese-number>&cursor=<optional>&limit=25
```

`phone` là tham số bắt buộc theo pattern `^(02|03|05|07|08|09)\d{8}$`. Kết quả chỉ được dùng để tìm candidate; số điện thoại không phải bằng chứng xác minh. `ClinicClient` chỉ giữ lại:

```json
{
  "patient_id": "string",
  "full_name": "string",
  "dob": "YYYY-MM-DD",
  "phone": "string or null"
}
```

Client chấp nhận collection dạng JSON array hoặc envelope có khóa `items`, `patients` hoặc `data`, do OpenAPI hiện không khai báo response schema cụ thể.

### Lấy identity context từ lịch hẹn

```http
GET /v1/appointments/{appt_id}
```

Trước khi xác minh, client chỉ chiếu response thành:

```json
{
  "appointment_id": "string",
  "patient_id": "string",
  "patient": "optional patient identity object"
}
```

Ngày, giờ, cơ sở, trạng thái và các chi tiết lịch hẹn khác bị loại bỏ khỏi identity projection. Việc tiết lộ hoặc thực hiện action lịch hẹn vẫn phải đi qua core guard.

## Endpoint không được sử dụng

Callbot không được gọi bất kỳ endpoint `/_harness/*` nào. Đây là API quản trị dành riêng cho hệ thống chấm điểm.

## Kiểm tra kết nối

```powershell
$env:CLINIC_API_BASE_URL = "https://clinic-mock-api.vercel.app"
$env:CLINIC_API_KEY = "<your-key>"
.\.venv\Scripts\python.exe scripts\check_clinic_connection.py --phone 0900000000
```

Script chỉ in trạng thái kết nối và số candidate, không in token hoặc dữ liệu bệnh nhân.
