# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1

- Tên: `high_latency_p95`
- Severity: Warning
- Duration: 5m
- Kênh thông báo: Slack (#alerts-sre-day13)
- SLI/SLO liên quan: `fast_successful_requests` (Target: 99.5% requests <= 3000ms trong 28d)
- Điều kiện và thời gian duy trì: `latency_p95 > 3000ms` liên tục trong 5 phút
- Ảnh hưởng tới người dùng: Người dùng trải nghiệm phản hồi chậm, thời gian chờ sinh câu trả lời kéo dài
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard tại panel **Latency percentiles and TTFT**, xác định xem đuôi trễ P95/P99 tăng từ thời điểm nào.
  2. Lọc file `data/logs.jsonl` tìm các request có `latency_ms > 3000` trong khung giờ bị cảnh báo và lấy `correlation_id`.
  3. Tìm `trace_id` tương ứng trên Langfuse và kiểm tra waterfall xem độ trễ nằm ở span `retrieve` (vector DB) hay `generation` (LLM timeout).
- Mitigation tạm thời:
  - Nếu span `retrieve` bị nghẽn (do vector DB chậm), kích hoạt cache tài liệu hoặc chuyển sang fallback local docs.
  - Nếu LLM model bị nghẽn, kiểm tra xem có incident `rag_slow` đang bật không để disable (`python scripts/inject_incident.py --disable`), hoặc chuyển tạm sang fast model.
- Owner: `sre-oncall`

## Alert 2

- Tên: `high_error_rate`
- Severity: Critical
- Duration: 3m
- Kênh thông báo: Slack (#alerts-critical-day13)
- SLI/SLO liên quan: `fast_successful_requests` & Error Guardrail (Error rate <= 2%)
- Điều kiện và thời gian duy trì: `error_rate_pct > 2%` liên tục trong 3 phút
- Ảnh hưởng tới người dùng: Người dùng nhận mã lỗi HTTP 500 (`Internal Server Error`), gián đoạn dịch vụ hoàn toàn
- Ba bước kiểm tra đầu tiên:
  1. Kiểm tra panel **Errors** trên dashboard xem tỷ lệ lỗi `request_failed / request_received` và nhóm `error_type` chính.
  2. Truy vấn log `data/logs.jsonl` với `event == "request_failed"` để xem stack trace và thông điệp lỗi trong `payload.detail`.
  3. Lấy `correlation_id` của request lỗi, mở trace trên Langfuse để xác định span ném ngoại lệ.
- Mitigation tạm thời:
  - Khởi động lại service API hoặc rollback model prompt về phiên bản stable gần nhất (v1).
  - Kiểm tra các cờ incident đang kích hoạt (`/health`) và tắt các kịch bản lỗi giả định nếu đang chạy test.
- Owner: `sre-oncall`

## Alert 3

- Tên: `low_retrieval_success`
- Severity: Warning
- Duration: 5m
- Kênh thông báo: Slack (#alerts-rag-day13)
- SLI/SLO liên quan: Guardrail `retrieval_success_rate_pct_min: 90%`
- Điều kiện và thời gian duy trì: `tool_success_rate_pct < 90%` liên tục trong 5 phút
- Ảnh hưởng tới người dùng: Câu trả lời của bot bị mất ngữ cảnh tài liệu chuyên ngành, chất lượng phản hồi giảm (fallback generic answer)
- Ba bước kiểm tra đầu tiên:
  1. Kiểm tra panel **Errors and retrieval success** trên dashboard, đối chiếu tỷ lệ `tool_success == true` so với tổng tool calls.
  2. Lọc các dòng log `response_sent` có `tool_success == false` hoặc `tool_name == "retrieval"` bị lỗi.
  3. Kiểm tra kết nối mạng và độ trễ tới vector database / retrieval service.
- Mitigation tạm thời:
  - Kích hoạt cơ chế fallback tài liệu tĩnh (static curated knowledge base) để duy trì câu trả lời.
  - Tăng timeout cho retrieval service nếu đang bị nghẽn mạng cục bộ.
- Owner: `rag-platform-team`

