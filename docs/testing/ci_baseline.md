# CI Baseline

## 1. Mục đích

Dựng pipeline CI đầu tiên cho repo (trước đây chưa có `.github/workflows` nào)
chạy lint/typecheck/unit/smoke test trên mỗi PR, và chuẩn bị sẵn một job
riêng cho identity regression để mở rộng dần trong tuần 1, theo đúng Makefile
đã có sẵn (`make lint`, `make typecheck`, `make test-fast`, `make test-safety`).

File: [.github/workflows/ci.yml](../../.github/workflows/ci.yml).

## 2. Hai lỗi có thật đã sửa trước khi viết CI

Khi chạy thử `make check` cục bộ để xác nhận CI sẽ pass, phát hiện 2 vấn đề
có thật trong scaffold (không phải do CI gây ra, CI chỉ là thứ phơi bày ra):

1. **`mypy` fail ngay lập tức** vì `src/api/router.py` và `src/agents/router.py`
   trùng tên module, và không có `__init__.py` nào trong `src/` để mypy phân
   biệt được hai package. Đã thêm `__init__.py` (rỗng) vào toàn bộ 16 thư mục
   package trong `src/` — đây cũng là fix đúng chuẩn cho một ứng dụng (không
   phải distributed library cần namespace package).
2. **`mypy --strict` fail** trên `src/agents/state.py` — 2 field dùng `dict`
   trần (`list[dict]`, `dict | None`) thiếu type argument. Sửa thành
   `dict[str, Any]`.

Không có 2 fix này, CI sẽ đỏ ngay từ commit đầu tiên, trước khi ai kịp mở PR
nào khác.

## 3. Vì sao có "exit-5 tolerance" trong workflow

`pytest` trả **exit code 5** khi không collect được test case nào — khác với
exit 1 (test fail) hay exit 2 (lỗi cấu hình/usage). Ở thời điểm hiện tại,
gần như toàn bộ `tests/unit`, `tests/agents`, `tests/api`, `tests/safety` vẫn
là file rỗng (chưa implement), nên `make test-fast` / `make test-safety` hiện
trả exit 5 — **không phải vì có gì sai**, mà vì chưa có gì để chạy.

Nếu để CI fail cứng ngay bây giờ vì exit 5, mọi PR tuần này đều đỏ vì lý do
không liên quan đến thay đổi của PR đó — vô nghĩa và khiến team bỏ qua CI.
Ngược lại, nếu chỉ bỏ qua exit code hoàn toàn (`|| true`) thì mất tác dụng
gate khi có test fail thật (exit 1).

→ Giải pháp: mỗi bước pytest trong CI chỉ coi **exit 5** là chấp nhận được,
mọi exit code khác (1, 2...) vẫn fail job như bình thường. Đây là biện pháp
tạm thời — có TODO ngay trong `ci.yml` nhắc gỡ bỏ khi bộ test thật đầu tiên
được thêm vào (dùng `identity_test_matrix.md` / `sf03_regression_spec.md` làm
input để convert thành `pytest.mark.parametrize`, như đã ghi trong 2 file đó).

## 4. Vì sao có smoke test riêng (`tests/smoke/test_imports.py`)

Task gốc yêu cầu "CI baseline cho syntax/unit/smoke tests" — nhưng `make
test-fast` trước khi có fix này thực sự **không chạy gì cả** (exit 5), nên
"smoke test" chỉ nằm trên giấy. Đã thêm 1 test thật:
`tests/smoke/test_imports.py` — import toàn bộ module trong `src/` (trừ các
module phụ thuộc optional extras: Twilio/Stringee, STT/TTS, LLM OpenAI — vì
CI baseline chỉ cài `dev` extra, không cài `llm-openai`/`audio`/
`telephony-twilio`) và assert import không lỗi.

Test này hiện pass với 83 module vì tất cả đều rỗng — nhưng có giá trị thật
từ hôm nay: nếu ai commit code có lỗi cú pháp/import sai ở bất kỳ module core
nào trong tuần này, CI bắt được ngay, không cần đợi tới khi có test logic
nghiệp vụ.

Marker `smoke` đã được đăng ký ở cả `pytest.ini` (file thực sự được pytest
đọc) và `pyproject.toml` (`[tool.pytest.ini_options]`, hiện bị `pytest.ini`
che nên không có hiệu lực — giữ đồng bộ để tránh lệch nếu sau này xóa
`pytest.ini`).

## 5. Cấu trúc 2 job

- **`lint-typecheck-test`**: `make install` → `make lint` → `make typecheck`
  → `make test-fast` (bao gồm cả smoke test, vì `smoke` không nằm trong
  `not integration and not slow`).
- **`identity-regression`**: chạy sau job trên (`needs:`), gọi `make
  test-safety`. Tách riêng vì đây là job sẽ **mở rộng dần trong tuần 1** khi
  các case SF-01..SF-05 được viết thành code — tách job giúp về sau có thể
  gắn thêm bước riêng (vd. publish coverage riêng cho safety, hoặc chặn merge
  nghiêm ngặt hơn cho job này) mà không ảnh hưởng job lint/typecheck chung.

## 6. Giới hạn đã biết: không chặn merge được ở mức GitHub

"Merge should fail on test failure" trong task gốc thường được hiện thực qua
**branch protection rule** (Require status checks to pass before merging).
Repo này là **private trên GitHub Free**, và GitHub chỉ cho bật branch
protection miễn phí với repo **public** — private repo cần plan trả phí
(Pro/Team/Enterprise) mới có tính năng này.

Đã cân nhắc các phương án thay thế (PR template nhắc nhở thủ công, tự động
chuyển PR về Draft khi CI fail qua `gh pr ready --undo`, chuyển repo sang
public) và **quyết định không dùng cơ chế chặn merge nào ở giai đoạn này** —
CI chỉ đóng vai trò **báo hiệu** (status check hiển thị pass/fail trên PR và
tab Actions), việc có merge PR đang đỏ hay không phụ thuộc vào người review.

Nếu sau này nâng cấp plan trả phí hoặc chuyển repo sang public, quay lại bật
"Require status checks to pass before merging" cho `main`, chọn 2 check
`Lint, typecheck, unit/smoke tests` và
`Identity safety regression (SF-01 / SF-03)`.

## 7. Việc cần làm tiếp

- [ ] Bật branch protection theo mục 6.
- [ ] Khi có case pytest thật đầu tiên trong `tests/safety/`, xóa đoạn
  exit-5-tolerance của job `identity-regression` trong `ci.yml`.
- [ ] Tương tự cho job `lint-typecheck-test` khi `tests/unit`/`tests/agents`/
  `tests/api` có case thật.
- [ ] Khi `src/telephony/providers/*`, `stt_service.py`, `tts_service.py`,
  `llm_service.py` được implement thật, cân nhắc thêm job CI riêng cài đủ
  extras (`make install-all`) thay vì loại trừ trong `tests/smoke/test_imports.py`.
