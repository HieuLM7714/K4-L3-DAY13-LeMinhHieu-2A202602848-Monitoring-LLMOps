# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Lê Minh Hiếu
- **MSSV:** 2A202602848
- **Lớp:** K4-L3A
- **Repository URL:** https://github.com/HieuLM7714/K4-L3-DAY13-LeMinhHieu-2A202602848-Monitoring-LLMOps.git
- **Commit SHA cuối:**
- **Challenge ID:**
- **Tên project Langfuse cá nhân:** `day13-k4-l3a-2A202602848`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/01-pytest.png` |
| Log validator | `evidence/02-log-validator.png` |
| Dashboard validator | `evidence/03-dashboard-validator.png` |
| Structured log | `evidence/04-structured-log.png` |
| PII redaction | `evidence/05-pii-redaction.png` |
| Trace list | `evidence/06-trace-list.png` |
| Trace waterfall | `evidence/07-trace-waterfall.png` |
| Trace metadata | `evidence/08-trace-metadata.png` |
| Prompt versions | `evidence/09-prompt-versions.png` |
| Prompt rollback | `evidence/10-prompt-rollback.png` |
| Dashboard runtime | `evidence/11-dashboard-overview.png` |
| Incident metric | `evidence/12-incident-metric.png` |
| Incident log | `evidence/13-incident-log.png` |
| Incident trace | `evidence/14-incident-trace.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100 | 100/100 | Đạt 100/100 sau khi bind correlation_id, enrichment và scrub PII |
| `validate_dashboard.py` | 6/6 panel | | Đạt chuẩn cấu hình dashboard ban đầu |
| `pytest` | 22/22 passed | 24/24 passed | Toàn bộ unit tests pass (bổ sung test CCCD & thẻ tín dụng) |
| Số traces hợp lệ | 10 | 10 | 10 traces được sinh qua load_test.py |
| Số PII leak | 0 | 0 | 0 leak sau khi áp dụng processor PII scrubber |
| Latency P95 / TTFT P95 | 1168.3 ms / 50.0 ms | | Sẽ cập nhật lại ở CP2 |
| Retrieval success rate | 100.0% | | Sẽ cập nhật lại ở CP2 |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Trong `CorrelationIdMiddleware` (`app/middleware.py`), trước khi xử lý request thực hiện `clear_contextvars()` để tránh rò rỉ context giữa các request. Trích xuất header `x-request-id`, nếu client không gửi thì sinh tự động theo chuẩn `f"req-{uuid.uuid4().hex[:8]}"`. Bind vào contextvars thông qua `bind_contextvars(correlation_id=correlation_id)` và lưu vào `request.state.correlation_id`. Sau khi request hoàn tất, gắn correlation ID vào response header `x-request-id` và trả kèm thời gian thực thi qua `x-response-time-ms`.
- **Các metadata được ghi vào structured log:** Các trường toàn cục bắt buộc: `ts` (ISO UTC), `level` (info/error), `service` ("api"), `event` ("request_received", "response_sent", "request_failed"), `correlation_id`. Tại endpoint `/chat`, context được làm giàu với `bind_contextvars`: `user_id_hash` (băm SHA-256 lấy 12 ký tự), `session_id`, `feature`, `model` ("claude-sonnet-4-5"), `env` ("dev"). Ở log `response_sent`, bổ sung thêm các số liệu vận hành: `latency_ms`, `ttft_ms`, `tokens_in`, `tokens_out`, `cost_usd`, `quality_score`, `tool_name`, `tool_success`.
- **Cách bảo đảm PII được scrub trước khi ghi:** Xây dựng processor `scrub_event` trong `app/logging_config.py` và đăng ký vào chuỗi processor của structlog ngay trước `JsonlFileProcessor()` và `JSONRenderer()`. Hàm `_scrub_value` duyệt đệ quy qua chuỗi, dictionary, list và áp dụng các regex trong `app/pii.py` (Email, Phone VN, CCCD 12 số, Credit Card, Passport) để thay thế thông tin nhạy cảm thành `[REDACTED_...]` trước khi dữ liệu được serialize và ghi ra file `data/logs.jsonl` hoặc stdout.
- **Cách kiểm chứng kết quả:** Chạy `python scripts/validate_logs.py` đạt điểm tuyệt đối 100/100 (0 missing required, 0 missing enrichment, 0 PII leaks, 10/10 correlation IDs duy nhất). Chạy `python -m pytest -q` vượt qua 24/24 tests bao gồm các unit test chuyên biệt cho việc redact Email, Số điện thoại Việt Nam, CCCD và Thẻ thanh toán.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:**
- **Cấu trúc root/retrieval/generation observations:**
- **Cách nối trace với log:**
- **Prompt name:**
- **Version/label baseline:**
- **Version/label candidate:**
- **Trace ID của mỗi version:**
- **Cách promote và rollback `production`:**

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:**
- **SLO và lý do chọn:**
- **Cách tính error budget:**
- **Ba alert và runbook tương ứng:**

## 7. Điều tra challenge

- **Challenge ID:**
- **Khoảng thời gian điều tra:**
- **Triệu chứng từ metrics:**
- **Log line và correlation ID liên quan:**
- **Trace ID và span gây ảnh hưởng:**
- **Root cause:**
- **Fix action:**
- **Preventive measure:**

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:**
- **Một lỗi/blocker đã gặp:**
- **Cách tìm nguyên nhân và xử lý:**
- **Cách hiểu luồng Metrics → Logs → Traces:**
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:**
- **Điều quan trọng nhất đã học:**
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:**

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [ ] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [ ] Incident evidence nối đúng metric → log → trace.
- [ ] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [ ] Repository chạy lại được theo README.
- [ ] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
