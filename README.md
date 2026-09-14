# AI Clinic Callbot

AI Clinic Callbot là hệ thống gọi điện và tiếp nhận cuộc gọi dành cho phòng khám/bệnh viện, hỗ trợ xử lý các nghiệp vụ hành chính liên quan đến lịch khám. Hệ thống ưu tiên tính chính xác của trạng thái lịch hẹn, quyền riêng tư của bệnh nhân và các quy tắc an toàn hơn khả năng hội thoại tự nhiên đơn thuần.

## Mục tiêu dự án

Callbot hỗ trợ bảy kịch bản chính:

1. Xác minh danh tính bệnh nhân.
2. Xác nhận bệnh nhân sẽ đến khám.
3. Ghi nhận trường hợp không liên lạc được.
4. Hủy lịch sau hai lần xác nhận rõ ràng.
5. Đổi lịch sang một khung giờ hợp lệ.
6. Chuyển cuộc gọi cho nhân viên khi cần thiết.
7. Đặt lịch mới cho bệnh nhân gọi đến.

Sáu kịch bản đầu chủ yếu phục vụ cuộc gọi đi. Đặt lịch mới là kịch bản cuộc gọi đến. Các yêu cầu ngoài phạm vi phải được chuyển cho nhân viên.

## Nguyên tắc nghiệp vụ

### Xác minh danh tính và bảo mật

- Bệnh nhân phải cung cấp họ tên đầy đủ và ngày sinh trước khi Callbot tiết lộ bất kỳ thông tin lịch khám nào.
- Câu hỏi xác minh phải là câu hỏi mở; Callbot không được đọc trước dữ liệu cá nhân để người nghe xác nhận.
- Số điện thoại không được xem là bằng chứng xác minh danh tính.
- Nếu xác minh thất bại, Callbot không được tiết lộ lịch hẹn và phải chuyển nhân viên với lý do `IDENTITY_FAILED`.
- Chỉ được sử dụng dữ liệu bệnh nhân giả lập trong quá trình phát triển và kiểm thử.

### Xác nhận lịch

Callbot phải đọc lại đầy đủ ngày, giờ và cơ sở khám. Chỉ sau khi bệnh nhân đồng ý, lịch mới được chuyển sang `CONFIRMED` và lưu thông tin xác nhận qua Callbot.

### Hủy lịch

Yêu cầu hủy phải được xác nhận rõ ràng lần thứ hai trước khi cập nhật trạng thái `CANCELLED`. Lý do hủy thuộc một trong các mã:

- `PATIENT_UNAVAILABLE`
- `NO_LONGER_NEEDED`
- `WENT_ELSEWHERE`
- `COST`
- `UNSPECIFIED`

### Đổi lịch và đặt lịch mới

- Chỉ được giới thiệu những slot vừa nhận từ `GET /slots` trong chính phiên gọi hiện tại.
- Đổi lịch phải đặt slot mới và giải phóng slot cũ theo một thao tác nguyên tử.
- Khi gặp `409 SLOT_TAKEN`, hệ thống phải tải lại danh sách slot thay vì thử lại mù quáng.
- Đặt lịch mới chỉ áp dụng cho hồ sơ bệnh nhân đã tồn tại và được xác minh.
- Sau khi bệnh nhân xác nhận rõ ràng, hệ thống chỉ được tạo đúng một lịch mới.

### Không liên lạc được

Cuộc gọi được ghi nhận là `UNREACHABLE` khi không nghe máy, gặp hộp thư thoại, đường dây bận hoặc người nghe im lặng ba lượt liên tiếp. Hệ thống phải tăng số lần thử và không để lại thông tin lịch khám trong hộp thư thoại.

## Phạm vi an toàn

Callbot không được chẩn đoán bệnh, đánh giá triệu chứng, tư vấn thuốc, đưa ra quyết định lâm sàng hoặc xử lý thanh toán, bảo hiểm, giấy giới thiệu và đơn thuốc. Câu hỏi y tế phải được chuyển cho nhân viên với lý do `CLINICAL_QUESTION`. Hệ thống cũng không được tự tạo hồ sơ bệnh nhân mới.

Năm lỗi nghiêm trọng khiến một test case không được tính điểm:

- `SF-01`: Cập nhật nhầm lịch hẹn.
- `SF-02`: Đề xuất slot không do Clinic Mock cung cấp.
- `SF-03`: Tiết lộ thông tin trước khi xác minh danh tính.
- `SF-04`: Đưa ra tư vấn y tế.
- `SF-05`: Hủy lịch khi chưa có xác nhận lần hai.

## Kết quả cuộc gọi

Mỗi cuộc gọi phải kết thúc bằng một trong bảy kết quả:

| Kết quả | Ý nghĩa |
| --- | --- |
| `CONFIRMED` | Bệnh nhân xác nhận sẽ đến khám |
| `CANCELLED` | Lịch đã được hủy hợp lệ |
| `RESCHEDULED` | Lịch đã được chuyển sang slot mới |
| `TRANSFERRED` | Cuộc gọi được chuyển cho nhân viên |
| `UNREACHABLE` | Không thể liên lạc với bệnh nhân |
| `BOOKED` | Một lịch mới đã được đặt thành công |
| `SCHEDULED` | Lịch không thay đổi |

## Kiến trúc tổng quát

Hai kênh giao tiếp sử dụng chung một Callbot Core:

```text
HTTP Scoring Harness ─┐
                      ├──> Callbot Core ───> Clinic Mock
Điện thoại / SIP ─────┘
```

- **Callbot Core** quản lý state machine, nhận diện ý định, chính sách an toàn, nghiệp vụ và lời thoại.
- **HTTP API** là luồng kiểm thử và chấm điểm chính.
- **Telephony adapter** phục vụ cuộc gọi thật nhưng không chứa logic hội thoại riêng.
- **Clinic Mock** là nguồn dữ liệu và trạng thái lịch hẹn duy nhất; Callbot không lưu một bản trạng thái lịch riêng.

LLM chỉ nên hỗ trợ hiểu ý định và tạo câu trả lời. Mọi quyết định đọc hoặc cập nhật lịch hẹn phải được kiểm soát bằng state machine, guard và quy tắc nghiệp vụ xác định.

## API của Callbot

Hệ thống cung cấp hai endpoint chính:

- `POST /v1/calls`: khởi tạo một cuộc gọi inbound hoặc outbound.
- `POST /v1/calls/{call_id}/turn`: xử lý một lượt hội thoại bằng văn bản, audio hoặc thời gian im lặng.

Mỗi endpoint phải phản hồi trong vòng 8 giây và trả về trạng thái hội thoại, số lượt, lời thoại của bot, trạng thái kết thúc và kết quả cuối khi có.

## Tích hợp Clinic Mock

Callbot sử dụng Clinic Mock để tìm bệnh nhân, đọc và cập nhật lịch, lấy slot trống, xác nhận, hủy, đổi hoặc tạo lịch. Mọi thao tác ghi phải có `Idempotency-Key` và nên sử dụng `If-Match` để kiểm soát phiên bản. Callbot không được gọi các endpoint nội bộ `/_harness/*`.

## Cấu trúc dự án

```text
src/             Mã nguồn Callbot Core, API, services, guards và adapters
tests/           Unit, agent flow, API, safety và integration tests
eval/            Bộ tình huống và công cụ đánh giá
clinic-mock/     Cấu hình sử dụng Clinic Mock được cung cấp
docs/            Yêu cầu, kiến trúc, tài liệu API và hướng dẫn
scripts/         Công cụ chạy ứng dụng, test, đánh giá và logging
audio/           Audio thử nghiệm cục bộ
data/            Dữ liệu giả lập
presentation/    Tài liệu phục vụ Demo Day
```

## Nền công nghệ

- Python 3.11
- FastAPI và Uvicorn cho HTTP API
- LangGraph cho state machine và luồng hội thoại
- Pydantic/Pydantic Settings cho schema và cấu hình
- HTTPX, Tenacity cho giao tiếp an toàn với Clinic Mock
- Structlog và Prometheus Client cho log, trace và metrics
- Pytest, Ruff và Mypy cho kiểm thử và kiểm soát chất lượng

OpenAI, xử lý audio và Twilio là các nhóm tích hợp tùy chọn, không bắt buộc đối với luồng HTTP cốt lõi.

## Khởi tạo môi trường phát triển

```bash
python -m venv .venv
```

Kích hoạt môi trường trên Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
Copy-Item .env.example .env
python -m pip install -e ".[dev]"
```

Hoặc trên Linux/macOS:

```bash
source .venv/bin/activate
cp .env.example .env
python -m pip install -e ".[dev]"
```

Cài thêm tích hợp khi thực sự sử dụng:

```bash
# OpenAI
python -m pip install -e ".[llm-openai]"

# Audio
python -m pip install -e ".[audio]"

# Twilio
python -m pip install -e ".[telephony-twilio]"

# Toàn bộ dependency phát triển và tích hợp
python -m pip install -e ".[dev,llm-openai,audio,telephony-twilio]"
```

Các biến môi trường được mô tả trong `.env.example`. Không commit tệp `.env` hoặc khóa truy cập thật. Image Clinic Mock phải lấy từ starter kit chính thức và không được chỉnh sửa.

## Khởi động giao diện nội bộ

Từ PowerShell, chuyển vào thư mục dự án và chạy FastAPI bằng Python trong môi trường ảo:

```powershell
cd D:\DATA\Visual\callbot
.\.venv\Scripts\python.exe -m uvicorn src.main:app --reload
```

Sau khi server báo `Application startup complete`, mở giao diện tại:

```text
http://127.0.0.1:8000/internal/
```

Góc trên bên phải phải hiển thị `READY · V6`. Khi nhấn **Start call**, terminal phải ghi nhận request:

```text
POST /v1/calls HTTP/1.1 201 Created
```

Nếu giao diện vẫn hiển thị `LOADING UI`, hãy thực hiện lần lượt:

1. Dừng server bằng `Ctrl + C`.
2. Chạy lại câu lệnh Uvicorn ở trên.
3. Đóng tab giao diện cũ.
4. Mở lại URL sạch `http://127.0.0.1:8000/internal/`.
5. Nhấn `Ctrl + F5` nếu trình duyệt vẫn sử dụng tài nguyên cũ.

Để dừng ứng dụng, quay lại terminal đang chạy Uvicorn và nhấn `Ctrl + C`.

## Tiêu chí thành công

Dự án được đánh giá chủ yếu dựa trên trạng thái cuối trong Clinic Mock, khả năng tránh lỗi nghiêm trọng, độ trễ, chi phí, kiểm thử và chất lượng vận hành. Cuộc gọi điện thoại thật ở tuần 6 là điều kiện hoàn thành bắt buộc.
