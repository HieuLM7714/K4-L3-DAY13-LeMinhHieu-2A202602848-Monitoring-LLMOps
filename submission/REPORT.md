# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Lê Minh Hiếu
- **MSSV:** 2A202602848
- **Lớp:** K4-L3A
- **Repository URL:** https://github.com/HieuLM7714/K4-L3-DAY13-LeMinhHieu-2A202602848-Monitoring-LLMOps.git
- **Commit SHA cuối:**
- **Challenge ID:** day13-k4-l3a-monitoring-llmops-v1
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
| `validate_dashboard.py` | 6/6 panel | 6/6 panel | Đạt chuẩn 6/6 panel theo dashboard contract (latency, traffic, errors, cost, tokens, quality) |
| `pytest` | 22/22 passed | 24/24 passed | Toàn bộ unit tests pass (bổ sung test CCCD & thẻ tín dụng) |
| Số traces hợp lệ | 10 | 14+ | Các traces do chính học viên tạo trong project Langfuse cá nhân |
| Số PII leak | 0 | 0 | 0 leak sau khi áp dụng processor PII scrubber |
| Latency P95 / TTFT P95 | 1168.3 ms / 50.0 ms | 153.6 ms / 50.0 ms | Đáp ứng tốt ngưỡng SLO latency <= 3000ms |
| Retrieval success rate | 100.0% | 100.0% | Đáp ứng guardrail tối thiểu 90% |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Trong `CorrelationIdMiddleware` (`app/middleware.py`), trước khi xử lý request thực hiện `clear_contextvars()` để tránh rò rỉ context giữa các request. Trích xuất header `x-request-id`, nếu client không gửi thì sinh tự động theo chuẩn `f"req-{uuid.uuid4().hex[:8]}"`. Bind vào contextvars thông qua `bind_contextvars(correlation_id=correlation_id)` và lưu vào `request.state.correlation_id`. Sau khi request hoàn tất, gắn correlation ID vào response header `x-request-id` và trả kèm thời gian thực thi qua `x-response-time-ms`.
- **Các metadata được ghi vào structured log:** Các trường toàn cục bắt buộc: `ts` (ISO UTC), `level` (info/error), `service` ("api"), `event` ("request_received", "response_sent", "request_failed"), `correlation_id`. Tại endpoint `/chat`, context được làm giàu với `bind_contextvars`: `user_id_hash` (băm SHA-256 lấy 12 ký tự), `session_id`, `feature`, `model` ("claude-sonnet-4-5"), `env` ("dev"). Ở log `response_sent`, bổ sung thêm các số liệu vận hành: `latency_ms`, `ttft_ms`, `tokens_in`, `tokens_out`, `cost_usd`, `quality_score`, `tool_name`, `tool_success`.
- **Cách bảo đảm PII được scrub trước khi ghi:** Xây dựng processor `scrub_event` trong `app/logging_config.py` và đăng ký vào chuỗi processor của structlog ngay trước `JsonlFileProcessor()` và `JSONRenderer()`. Hàm `_scrub_value` duyệt đệ quy qua chuỗi, dictionary, list và áp dụng các regex trong `app/pii.py` (Email, Phone VN, CCCD 12 số, Credit Card, Passport) để thay thế thông tin nhạy cảm thành `[REDACTED_...]` trước khi dữ liệu được serialize và ghi ra file `data/logs.jsonl` hoặc stdout.
- **Cách kiểm chứng kết quả:** Chạy `python scripts/validate_logs.py` đạt điểm tuyệt đối 100/100 (0 missing required, 0 missing enrichment, 0 PII leaks, 10/10 correlation IDs duy nhất). Chạy `python -m pytest -q` vượt qua 24/24 tests bao gồm các unit test chuyên biệt cho việc redact Email, Số điện thoại Việt Nam, CCCD và Thẻ thanh toán.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** Traces được ghi trực tiếp vào project riêng `day13-k4-l3a-2A202602848` (Project ID: `cmumcrino048iad0d7elppjn5`) trên Langfuse Cloud bằng API key cá nhân (`pk-lf-b9688cd7...`). Trên giao diện Langfuse hiển thị rõ tên project cá nhân và danh sách trace do chính workload của tôi phát sinh.
- **Cấu trúc root/retrieval/generation observations:**
  - **Root observation:** `@observe(name="lab-agent-run", as_type="agent")` bao bọc toàn bộ chu trình xử lý của `LabAgent.run`, truyền các context tag (`user_id`, `session_id`, `correlation_id`, `env`).
  - **Child observation 1 (retrieval):** `@observe(name="retrieve", as_type="retriever")` trong `app/mock_rag.py`, đo thời gian tra cứu tài liệu ngữ cảnh.
  - **Child observation 2 (generation):** `@observe(name="fake-llm-generate", as_type="generation")` trong `app/mock_llm.py`, nhận managed prompt từ Langfuse, ghi nhận model (`claude-sonnet-4-5`), `usage_details` (`input_tokens`, `output_tokens`) và `cost_details`.
  - Cả hai child observation đều bật `capture_input=False, capture_output=False` để triệt tiêu hoàn toàn nguy cơ rò rỉ PII thô lên hệ thống tracing đám mây.
- **Cách nối trace với log:** Sử dụng `correlation_id` làm khóa liên kết 1-1. `correlation_id` (ví dụ `req-f8ef7ebc`) được ghi nhận trong structured log `data/logs.jsonl` và đồng thời được inject vào trace metadata của Langfuse thông qua `propagate_attributes(metadata={"correlation_id": correlation_id})`. Ngoài ra, `trace_id` của Langfuse cũng được lưu vào payload của sự kiện log `response_sent`.
- **Prompt name:** `day13-chat`
- **Version/label baseline:** Version 1, label: `baseline` (và ban đầu là `production`)
- **Version/label candidate:** Version 2, label: `candidate`
- **Trace ID của mỗi version:**
  - Version 1 (Baseline prompt v1): Trace ID `0a509d477f5071010f7fff4213ea8db7` (Correlation ID: `req-5fb474f1`, hiển thị trong `07-trace-waterfall.png` và `08-trace-metadata.png`) & Trace ID `26df8c106007f30e72337f289d749f1a` (Correlation ID: `req-f8ef7ebc`)
  - Version 2 (Candidate prompt v2): Trace ID `7c4fe34dbac6d77fe1226d94443afb81` (Correlation ID: `req-cee90fff`)
- **Cách promote và rollback `production`:**
  - **Promote:** Thực hiện chuyển nhãn `production` sang Version 2 qua SDK: `client.update_prompt(name="day13-chat", version=2, new_labels=["candidate", "production"])`. Khi đó các request tiếp theo tự động fetch template prompt v2.
  - **Rollback:** Khi cần hoàn tác về Version 1 ổn định, chạy lệnh rollback: `client.update_prompt(name="day13-chat", version=1, new_labels=["baseline", "production"])` và gỡ label khỏi v2: `client.update_prompt(name="day13-chat", version=2, new_labels=["candidate"])`. Xóa cache client để áp dụng ngay lập tức mà không cần deploy lại mã nguồn.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** Xây dựng runtime dashboard chuẩn contract tại `http://127.0.0.1:8000/dashboard` tổng hợp dữ liệu từ `data/logs.jsonl` trong time range 60 phút, refresh 30 giây:
  1. `Latency & TTFT`: P50, P95, P99 và TTFT P95 (đơn vị: ms, threshold: P95 <= 3000 ms).
  2. `Request Traffic`: Tổng số request nhận và throughput rate (đơn vị: req/min, threshold: rate >= 1 req/min).
  3. `Errors & Retrieval`: Tỷ lệ lỗi toàn hệ thống và tỷ lệ tra cứu tri thức thành công (đơn vị: %, threshold: Error Rate <= 2%, Retrieval >= 90%).
  4. `Cost Over Time`: Chi phí tích lũy theo USD và trung bình/request (đơn vị: USD, threshold: Total <= 2.50 USD).
  5. `Tokens Volume`: Tổng số token tiêu thụ input và output (đơn vị: tokens, threshold: sum <= 50,000 tokens).
  6. `Quality Proxy`: Điểm đánh giá chất lượng câu trả lời theo heuristic grounding (đơn vị: score_0_to_1, threshold: mean >= 0.75).
- **SLO và lý do chọn:**
  - Tên SLO: `fast_successful_requests` với chu kỳ đánh giá rolling 28 ngày (`28d`).
  - SLI = (Số lượng sự kiện `response_sent` có `latency_ms <= 3000`) / (Tổng số sự kiện `request_received`).
  - Target: **99.5%**.
  - Lý do chọn: Dựa trên baseline thực tế (Latency P95 dao động trong khoảng 150ms – 1200ms), ngưỡng 3000ms là mức giới hạn chịu đựng tối đa của người dùng đối với một hệ thống AI Assistant tra cứu kết hợp LLM sinh nội dung. Mức 99.5% đảm bảo độ tin cậy cao của dịch vụ trong môi trường production.
- **Cách tính error budget:**
  - Error budget = 100% - Target% = 100% - 99.5% = **0.5%** tổng số request trong cửa sổ 28 ngày.
  - Ví dụ: Với lưu lượng 100,000 request/tháng, hệ thống cho phép tối đa 500 request bị chậm (> 3000ms) hoặc thất bại. Nếu tốc độ đốt ngân sách (burn rate) vượt ngưỡng cho phép, đội ngũ SRE sẽ kích hoạt freeze release tính năng để tập trung tối ưu hóa hạ tầng và độ trễ.
- **Ba alert và runbook tương ứng:**
  1. `high_latency_p95`: Severity Warning, condition: P95 latency > 3000ms trong 5m, owner: `sre-oncall`, Slack: `#alerts-sre-day13`, runbook: `docs/alerts.md#alert-1`.
  2. `high_error_rate`: Severity Critical, condition: error_rate_pct > 2% trong 3m, owner: `sre-oncall`, Slack: `#alerts-critical-day13`, runbook: `docs/alerts.md#alert-2`.
  3. `low_retrieval_success`: Severity Warning, condition: tool_success_rate_pct < 90% trong 5m, owner: `rag-platform-team`, Slack: `#alerts-rag-day13`, runbook: `docs/alerts.md#alert-3`.

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3a-monitoring-llmops-v1`
- **Khoảng thời gian điều tra:** 2026-09-29 15:56:00 – 16:15:00
- **Triệu chứng từ metrics:** P95 Latency của endpoint `/chat` tăng vọt lên **3758.2 ms** (vượt xa ngưỡng threshold 2000ms định nghĩa trong challenge). Khi chạy tải đồng thời (concurrency = 5), thời gian phản hồi chạm mức 12.4s – 15.1s do hàng đợi tích lũy. Trên dashboard (`evidence/12-incident-metric.png`), panel Latency & TTFT kích hoạt cờ đỏ **BREACH**.
- **Log line và correlation ID liên quan:** Correlation ID tiêu biểu: `req-5de6dce8` (Session `k4-l3a-challenge-s01`, feature `monitoring`, user_id_hash `dde2e75b20cf`). Log `response_sent` ghi nhận `latency_ms: 3763`, `ttft_ms: 50`, `tokens_in: 35`, `tokens_out: 124`, `cost_usd: 0.001965`, `tool_name: retrieval`, `tool_success: true`, payload liên kết trực tiếp `trace_id: 1e2524eda30b9d7542d9872d81ce77a0`.
- **Trace ID và span gây ảnh hưởng:** Trace ID: `1e2524eda30b9d7542d9872d81ce77a0` (hiển thị trong `evidence/14-incident-trace.png` trên Langfuse, thời gian thực thi: **3.76s**, khớp hoàn hảo với Dashboard P95). Trong trace waterfall, span **`retrieve`** (loại retriever) tốn tới **2.50s** (chiếm phần lớn thời gian xử lý), trong khi span `fake-llm-generate` chỉ tốn 0.15s và hàng đợi/I-O tốn thời gian còn lại.
- **Root cause:** Nghẽn cổ chai tại tầng tra cứu RAG (span `retrieve`). Kịch bản `rag_slow` đã kích hoạt độ trễ giả lập 2.5s khi tra cứu tài liệu liên quan tới feature `monitoring` (mô phỏng vector database bị chậm do thiếu index hoặc quá tải).
- **Fix action:** Thực hiện tắt sự cố bằng lệnh `python scripts/inject_incident.py --disable`. Trong môi trường thực tế, tiến hành kiểm tra kết nối và tài nguyên của vector DB cluster, bổ sung cache ngữ nghĩa (Semantic Caching trên Redis) cho các câu hỏi phổ biến, và thiết lập client-side timeout cho retrieval.
- **Preventive measure:** Bổ sung Circuit Breaker Pattern cho cuộc gọi retrieval với timeout nghiêm ngặt (1000ms), tự động fallback sang tài liệu tĩnh nếu vector store không phản hồi kịp thời; cấu hình cảnh báo `high_latency_p95` và cảnh báo riêng cho `retrieval_latency > 1000ms`.

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** Đặt processor làm sạch PII (`scrub_event`) ở tầng middleware xử lý log trước khi JSON được serialize và ghi ra file/stdout; đồng thời đặt `capture_input=False, capture_output=False` trên các decorator `@observe` của Langfuse. Quyết định này giúp bảo đảm nguyên tắc Zero Trust / Privacy by Design: dữ liệu nhạy cảm (Email, CCCD, Phone, Card) không bao giờ bị ghi lọt vào log lưu trữ hay đẩy lên cloud tracing bên thứ ba.
- **Một lỗi/blocker đã gặp:** Khi chạy baseline validator ban đầu (`validate_logs.py`), điểm số chỉ đạt 30/100 do log cũ trong file `data/logs.jsonl` từ các lượt chạy trước không có correlation ID và chưa được redact. Validator đọc toàn bộ file nên log cũ làm rớt điểm nghiêm trọng dù code mới đã sửa.
- **Cách tìm nguyên nhân và xử lý:** Đọc tài liệu `docs/GUIDE.md`, nhận diện cơ chế đọc toàn bộ file của script validator. Đã thực hiện sao lưu log baseline cũ, reset `data/logs.jsonl`, khởi động lại API server và chạy lại kịch bản `load_test.py`. Kết quả validator ngay lập tức đạt điểm tuyệt đối 100/100.
- **Cách hiểu luồng Metrics → Logs → Traces:**
  - **Metrics** là giác quan đầu tiên báo hiệu *CÁI GÌ đang xảy ra và KHI NÀO* (ví dụ: P95 latency tăng vọt từ 150ms lên 2650ms lúc 15:56).
  - **Logs** giúp khoanh vùng *REQUEST NÀO bị ảnh hưởng* bằng cách lọc các bản ghi log trong khung thời gian đó, bốc tách ra `correlation_id` cụ thể (`req-22100687`).
  - **Traces** đào sâu vào chi tiết *BƯỚC NÀO là nguyên nhân gốc rễ* bằng cách mở trace waterfall có cùng correlation ID trên Langfuse, so sánh thời gian thực thi của từng span con để phát hiện chính xác span `retrieve` nghẽn 2.50s.
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:**
  - Prompt là "mã nguồn mềm" của AI: việc đánh version và gắn label (`baseline`, `production`, `candidate`) cho phép quản lý vòng đời prompt có kỷ luật, tự tin thử nghiệm và rollback tức thì trong vài giây mà không cần redeploy backend.
  - Quản lý token & cost: LLM tính phí trên token; theo dõi sát sao input/output token usage giúp phát hiện sớm các hiện tượng prompt blow-up, token loop hoặc cost spike.
  - SLO & Error budget: Đặt ra ranh giới định lượng giữa tốc độ phát triển tính năng và độ ổn định của hệ thống.
- **Điều quan trọng nhất đã học:** Kỹ năng xây dựng hệ thống quan sát toàn diện (End-to-End Observability) cho ứng dụng GenAI / Agentic LLM: biến AI từ một "hộp đen" thành hệ thống có thể mổ xẻ, truy vết và định vị lỗi chính xác trong thời gian thực.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** Hệ thống mock RAG hiện tại đang chạy dữ liệu in-memory; trong production cần tích hợp thêm distributed tracing tới cụm Qdrant/Pinecone/Milvus thực tế và cấu hình OpenTelemetry Collector chuyên dụng.

## 9. Checklist trước khi nộp

- [x] Kết quả và evidence thuộc commit SHA cuối.
- [x] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [x] Incident evidence nối đúng metric → log → trace.
- [x] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [x] Repository chạy lại được theo README.
- [x] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [x] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
