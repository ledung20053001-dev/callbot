# Synthetic Identity Test Data

## 1. Mục đích

Cung cấp fixture data cụ thể cho các persona đã được tham chiếu bằng placeholder
(`PAT-001`, `PAT-002`...) xuyên suốt
[identity_test_matrix.md](identity_test_matrix.md) và
[sf03_regression_spec.md](sf03_regression_spec.md), để các file test có thể
chạy thật thay vì chỉ mô tả bằng lời.

**Không có dữ liệu bệnh nhân thật** ở đâu trong các file này — toàn bộ tên,
ngày sinh, số điện thoại đều bịa, theo đúng nguyên tắc README
("Chỉ được sử dụng dữ liệu bệnh nhân giả lập trong quá trình phát triển và
kiểm thử").

File tạo ra:

- `tests/fixtures/patients.json` — 9 persona
- `tests/fixtures/appointments.json` — 8 lịch hẹn (không phải mọi persona đều
  cần có lịch hẹn)
- `tests/fixtures/dob_formats.json` — tổ hợp định dạng DOB tương đương/dễ nhầm

## 2. Nguyên tắc thiết kế

Data không chỉ là "vài bản ghi ngẫu nhiên" — mỗi persona được dựng để **kích
hoạt đúng một rủi ro cụ thể** đã nêu trong matrix, để test có gì đó thật để
assert thay vì chỉ test logic tầm thường:

- **Positive record** đơn giản (happy path) — 1 persona.
- **Ambiguous nhưng resolvable** — 2 persona trùng tên, khác DOB (phân biệt
  được bằng DOB).
- **Ambiguous và không resolvable bằng tên+DOB** — 2 persona trùng cả tên lẫn
  DOB (buộc phải hỏi thêm câu phân biệt, theo quyết định ở matrix §2 mục 7).
- **Cross-patient leak target** — 1 persona dùng để test việc hỏi hộ người
  khác không được làm lộ thông tin của họ.
- **Near-miss do chuẩn hóa quá tay** — 1 persona tên gần giống persona chính
  (khác dấu) nhưng là người khác thật, DOB khác — để bắt lỗi nếu matching
  bỏ dấu tiếng Việt một cách ẩu và gộp nhầm hai người.
- **Bẫy đảo ngày/tháng** — 2 persona mà DOB thật của người thứ hai trùng đúng
  với cách đọc sai (hoán đổi ngày/tháng) của người thứ nhất — đây là trường
  hợp nguy hiểm nhất vì lỗi parse không gây ra "không tìm thấy", mà gây ra
  **xác thực nhầm sang một người có thật khác** (SF-01).

## 3. Bảng persona

| Patient ID | Tên | DOB | Có lịch hẹn | Dùng cho case |
| --- | --- | --- | --- | --- |
| `PAT-001` | Nguyễn Văn An | 1990-03-15 | `APT-001` | Happy path (IDN-01, IDN-02), toàn bộ SF03-01..06 |
| `PAT-002` | Trần Thị Bình | 1985-07-02 | `APT-002` | IDN-15 (ambiguity pair A, 1/2) |
| `PAT-003` | Trần Thị Bình | 1992-11-20 | `APT-003` | IDN-15 (ambiguity pair A, 2/2) — trùng tên PAT-002, khác DOB |
| `PAT-004` | Lê Hoàng Nam | 1978-01-09 | `APT-004` | IDN-16 (exact-collision pair, 1/2) |
| `PAT-005` | Lê Hoàng Nam | 1978-01-09 | `APT-005` | IDN-16 (exact-collision pair, 2/2) — trùng cả tên lẫn DOB với PAT-004 |
| `PAT-006` | Phạm Thị Cúc | 1995-02-14 | `APT-006` | IDN-27 / SF03-07 (cross-patient leak) |
| `PAT-007` | Nguyễn Văn Ân | 1990-06-21 | — | IDN-03 (near-miss diacritic của PAT-001, không được gộp nhầm) |
| `PAT-008` | Vũ Thành Đạt | 1988-05-08 | `APT-008` | IDN-08 (nguồn của bẫy đảo ngày/tháng) |
| `PAT-009` | Hoàng Thị Mai | 1988-08-05 | `APT-009` | IDN-08 (đích của bẫy — DOB thật trùng với cách đọc sai của PAT-008) |

## 4. Lưu ý khi dùng

- `PAT-004`/`PAT-005` cố tình **không** có field nào khác giúp phân biệt
  ngoài `patient_id` nội bộ — cơ chế câu hỏi phân biệt cụ thể (hỏi thêm gì)
  là quyết định của dev/product khi implement, fixture này chỉ đảm bảo tình
  huống trùng lặp là có thật và có 2 lịch hẹn khác nhau để so sánh kết quả.
- `PAT-007` **không có lịch hẹn** — đây là fixture chỉ phục vụ test matching
  tên, không phục vụ test disclosure.
- `tests/fixtures/dob_formats.json` tách riêng khỏi `patients.json` vì nó mô
  tả **input/format**, không phải bản ghi hồ sơ.
- Field name trong các file JSON (`patient_id`, `full_name`, `dob`, `clinic`,
  `status`...) là **tạm thời**, cần khớp lại khi `src/models/patient.py` và
  `src/models/appointment.py` (hiện đang trống) có schema chính thức.
- Ngày hẹn trong `appointments.json` cố tình để trong tương lai gần
  (2026-09-22 → 2026-09-29) để không bị coi là quá hạn khi test chạy.

## 5. Việc cần làm tiếp

- [ ] Khớp field name với `src/models/patient.py` / `appointment.py` khi có.
- [ ] Khi Clinic Mock thật được tích hợp (`clinic-mock/`), seed bộ data này
  vào Clinic Mock qua `scripts/seed_mock.py` (hiện đang trống — thuộc phạm vi
  một task riêng, không nằm trong chuỗi Week 1 Day 1 này).
- [ ] Bổ sung persona cho slot/booking/reschedule flow khi có task tương ứng
  — phạm vi hiện tại chỉ phục vụ identity verification.
