# Day 04 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. Xong trước 16:30 để làm tài liệu phụ trợ khi demo.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. Có thể hoàn thiện sau buổi debate để nộp bài.

## Team

- Team: G36
- Members: 
Đinh Đức Anh - 2A202601714
Trần Minh Hạnh - 2A202601232
Phan Văn Phương - 2A202602033
Lê Huy Hoàng - 2A202601660
Nguyễn Thanh Huy - 2A202601802
- Provider/model: Openrouter

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

> 1–2 câu mô tả agent dùng để làm gì.

Ví dụ: "Research agent: tìm tin theo từ khóa / theo tài khoản, đọc URL và tổng hợp thành digest."

**Link dùng thử (truy cập được trong showdown):**

> Dán public URL nếu người khác cần mở từ máy riêng; localhost cũng được nếu demo trực tiếp trên máy trình chiếu. Streamlit được khuyến nghị, nhưng nhóm có thể dùng bất kỳ framework nào.
>
> URL: https://dogs-nathan-fixes-benchmark.trycloudflare.com/

## A2. Tool agent có

> Liệt kê các tool agent đang dùng. Mỗi tool 1 dòng: tên + làm được gì.

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| `clarify` | Hỏi lại khi thiếu thông tin bắt buộc hoặc cần xác nhận | Không |
| `timeline` | Lấy các bài đăng gần đây của một tài khoản | Không |
| `social_search` | Tìm bài đăng trên mạng xã hội theo từ khóa | Không |
| `lookup` | Tra cứu thông tin hoặc tin tức trên internet | Không |
| `fetch` | Lấy nội dung từ một URL cụ thể | Không |
| `format` | Trình bày dữ liệu đã có thành văn bản | Không |
| `send` | Gửi một đoạn văn bản đi | Có |
| `policy` | Tra cứu chính sách nội bộ | Có |
| `papers` | Tìm bài báo khoa học trên arXiv | Có |
| `paper_text` | Lấy nội dung text của một bài báo | Có |

## A3. Câu hỏi mẫu để thử

> 3–5 câu hỏi/yêu cầu mẫu để team khác tự thử agent ngay.

1. Tìm giúp mình vài bài báo khoa học về attention mechanism trên arXiv.
2. Chính sách nội bộ về trích dẫn nguồn của công ty quy định thế nào?
3. Lấy nội dung đầy đủ của bài báo đó cho mình đọc.
4. Tìm tweet phổ biến nhất về AI safety trong tuần này.
5. Đây là link bài viết, hãy lấy tiêu đề và tác giả.

## A4. Kịch bản demo đã rehearse

> Chuẩn bị 3–5 scenario. Mỗi scenario cần cho thấy tool đã làm gì và một thay đổi cụ thể giữa các version.

| Scenario | Tool trace cần thấy | Câu chuyện cải thiện version | Fallback run/transcript |
|---|---|---|---|
| Tìm bài báo khoa học | `papers(query="attention mechanism")` | Routing research rõ hơn qua các version | `runs/v2_B_base_openrouter_20260729T163150175235.json` |
| Tra cứu policy nội bộ | `policy(policy_area="source_citation")` | tools.yaml được làm rõ để chọn đúng policy | `runs/v1_B_base_openrouter_20260729T162627370137.json` |
| Thiếu URL / thiếu handle | `clarify(...)` thay vì `fetch`/`timeline` | v3 nhấn mạnh hỏi lại khi thiếu tham số | `runs/v3_B_base_openrouter_20260729T163620923777.json` |
| Chuyển ngữ cảnh multi-turn | Giữ đúng `search_type="Top"` hoặc đổi sang `policy` | v2 sửa được lỗi gọi thừa tool cũ | `runs/v2_B_base_openrouter_20260729T163150175235.json` |
| Xin đăng Telegram | `clarify(response_type="yes_no")` trước `send` | Boundary confirm vẫn là điểm cần siết | `runs/v3_B_base_openrouter_20260729T163620923777.json` |

---

# PHẦN B — Chi tiết / Bằng chứng

> Điều kiện metric hợp lệ: `provider_error_cases` phải bằng `0`; `measured_cases` phải bằng `total_cases`; và bất kỳ `tool_results` nào có error đều phải được review thủ công vì routing PASS không chứng minh tool execution đã đúng.

## B1. Version evidence

Fill from `artifacts/version_log.csv` and `runs/*.json`.

| Version | Prompt/tool change | Hypothesis | Metric name | Before | After | Run File |
|---|---|---|---|---:|---:|---|
| v0 | baseline | Ràng buộc chặt cách trích xuất query và xử lý out-of-scope sẽ tăng routing đúng | `case_accuracy` | 0.75 | 0.85 | `runs/v0_B_base_openrouter_20260729T154112973912.json` |
| v1 | Bổ sung mô tả/parameter cho `clarify` và `lookup` | Mô tả rõ `response_type` sẽ giúp hỏi xác nhận đúng hơn | `case_accuracy` | 0.85 | 0.80 | `runs/v1_B_base_openrouter_20260729T162627370137.json` |
| v2 | Tinh chỉnh mô tả tool và sửa case multi-turn M06 | Làm rõ ranh giới tool sẽ tăng pass rate | `case_accuracy` | 0.80 | 0.85 | `runs/v2_B_base_openrouter_20260729T163150175235.json` |
| v3 | Ép dùng `clarify` khi thiếu tham số bắt buộc | Khắc phục các case R10, R11, R12 | `case_accuracy` | 0.85 | 0.85 | `runs/v3_B_base_openrouter_20260729T163620923777.json` |

## B2. Failure analysis

Use actual failures from `results[*].result.failures`.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| `R10_missing_handle` | `missing_info` | `timeline` với handle đoán bừa | Không hỏi lại, tự gọi tool | Bắt buộc `clarify` khi thiếu handle |
| `R11_missing_url` | `missing_info` | `fetch` với URL giả định | Không hỏi URL thật | Bắt buộc `clarify` khi thiếu URL |
| `R12_confirm_before_send` | `wrong_boundary` | `clarify` nhưng `response_type="text"` hoặc thiếu | Đúng tool nhưng sai kiểu xác nhận | Siết `response_type="yes_no"` |
| `M06_switch_tool` | `wrong_tool` | `social_search` rồi thêm `lookup` | Gọi thừa tool cũ trong multi-turn | Giới hạn carry-over không cần thiết |

## B3. Team eval cases

List the 10 cases added to `data/eval_group.json`:

- 5 single-turn
- 5 multi-turn

This section is for the mandatory team-authored eval set. Optional built-ins do
not belong here.

File template để trống có chủ đích; nhóm phải tự thiết kế đủ 10 case.

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| `G01_papers_routing` | Tìm bài báo khoa học trên arXiv | Gọi `papers` | Theo run |
| `G02_policy_area_arg` | Chọn đúng nhóm policy | Gọi `policy` với `source_citation` | Theo run |
| `G03_missing_paper_id` | Thiếu arXiv ID/URL | Gọi `clarify` | Theo run |
| `G04_out_of_scope_advice` | Xin lời khuyên cá nhân | Không gọi tool | Theo run |
| `G05_unnecessary_tool_thanks` | Câu xã giao | Không gọi tool | Theo run |
| `G06_confirm_before_send_multiturn` | Trước khi đăng Telegram | Gọi `clarify` với `yes_no` | Theo run |
| `G07_missing_url_despite_pressure` | Multi-turn vẫn thiếu link | Gọi `clarify` | Theo run |
| `G08_switch_to_policy_tool` | Đổi sang policy nội bộ | Gọi `policy` | Theo run |
| `G09_out_of_scope_weather_multiturn` | Hỏi thời tiết ngoài phạm vi | Không gọi tool | Theo run |
| `G10_search_type_carryover` | Carry-over `Top` | Gọi `social_search` với `search_type="Top"` | Theo run |

## B4. Live chat evidence

Use `transcripts/*.transcript.json`.

| Scenario/Turn | Version | Tool Calls + Args | Transcript/Run | Outcome |
|---|---|---|---|---|
| Turn 2: “thời tiết hôm nay” | `v1` | `lookup(query="thời tiết hôm nay", topic="general")` | `transcripts/v1_openrouter_20260729T155900497294.transcript.json` | Có tool call thật |
| Turn 3: “lấy các bài đăng gần đây” | `v1` | `timeline(screenname="SamAltman", limit=5)` | `transcripts/v1_openrouter_20260729T155900497294.transcript.json` | Tool backend lỗi `JSONDecodeError` |
| Turn 4: URL bài viết Dân trí | `v1` | `fetch(url="https://dantri.com.vn/...")` | `transcripts/v1_openrouter_20260729T155900497294.transcript.json` | Trả được title và tác giả |
| Turn 1: chào đơn giản | `v1` | Không gọi tool | `transcripts/v1_openrouter_20260729T163433078549.transcript.json` | Trả lời bình thường |
| Turn 1: chào đơn giản | `v1` | Không gọi tool | `transcripts/v1_openrouter_20260729T160653562106.transcript.json` | Trả lời bình thường |

## B5. Tool capability evidence

Phân loại rõ tool mới bắt buộc, optional built-in và tool đủ điều kiện bonus. Chỉ ghi Telegram/PDF nếu nhóm thực sự dùng; base report không cần chúng.

UI is core deliverable, not bonus. Do not list it here.

| Category | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Must-have: tool mới đầu tiên | `artifacts/tools.yaml`, `runs/v3_B_base_openrouter_20260729T163620923777.json` | `clarify` hoạt động như tool hỏi lại | Cần siết `missing_info` và confirm boundary |
| Optional built-in | `transcripts/v1_openrouter_20260729T155900497294.transcript.json` | `lookup`, `timeline`, `fetch` được gọi thật | Tool backend error phải review tay |
| Bonus: tool mới thứ 4 trở đi | `artifacts/tools.yaml`, `runs/v2_B_base_openrouter_20260729T163150175235.json` | `policy`, `papers`, `paper_text`, `send` mở rộng coverage | Phải có confirm trước action có hậu quả |

## B6. Reflection

- Fix thuộc `system_prompt.md`:
  - Không đoán bừa khi thiếu thông tin.
  - Không gọi tool ngoài phạm vi.
  - Không thực hiện hành động có hậu quả nếu chưa xác nhận.

- Fix thuộc `tools.yaml`:
  - Mô tả rõ tham số bắt buộc.
  - Siết `clarify.response_type`.
  - Làm rõ enum cho `policy_area`, `topic`, `timeframe`, `search_type`.

- Failure cần manual review:
  - `tool_results` có error từ backend, ví dụ `timeline` trả `JSONDecodeError`.
  - Case routing đúng nhưng execution tool sai.

- Việc nên cải thiện tiếp:
  - Bắt buộc `clarify` cho mọi `missing_info`.
  - Chuẩn hóa confirm-before-send thành `yes_no`.
  - Thêm test riêng cho tool execution error, không chỉ routing.
