# Hướng phát triển DocuMind cho project cá nhân

Cập nhật: 2026-11-10. Đây là đề xuất điều chỉnh lộ trình sau khi làm rõ: chủ project không chuyên huấn luyện AI và không có trách nhiệm cung cấp checkpoint tự huấn luyện.

Giữ nguyên **bốn giai đoạn** trong kế hoạch gốc. Điều chỉnh về checkpoint và quy mô đánh giá nằm trong giai đoạn 2; giai đoạn 3 và 4 tiếp tục được thực hiện theo phạm vi bên dưới.

## 1. Mục tiêu

Hoàn thiện trợ lý đọc tài liệu tiếng Việt cho cá nhân: tải PDF/DOCX/TXT, nhận tóm tắt, hỏi đáp trong nội dung và mở được nguồn. Dùng model đã được người khác huấn luyện/công bố, cấu hình gọn và có hướng dẫn chạy rõ ràng.

Giữ backend, worker, database, nguồn có phiên bản và các kiểm thử đã làm ở giai đoạn 1–2. Các kết quả kiểm thử kỹ thuật không được trình bày thành điểm chất lượng AI.

## 2. Điều chỉnh so với kế hoạch trước

- Không coi việc người dùng cung cấp checkpoint riêng là điều kiện để tiếp tục.
- Không yêu cầu người dùng tự huấn luyện hoặc làm bộ 240 câu hỏi. Runner đánh giá lớn vẫn có thể giữ cho tương lai; không dùng nó làm điều kiện bắt buộc để dùng bản cá nhân.
- Bản đầu kích hoạt một model hỏi đáp và một model tóm tắt đã kiểm tra thực tế. Giữ khả năng bổ sung PhoBERT/BARTpho và so sánh model sau; chưa cần bật đồng thời cả bốn lựa chọn.
- Agent chịu trách nhiệm tìm checkpoint phù hợp, kiểm tra khả năng tải, tokenizer, license, tiền xử lý, tải/nạp và chạy thử. Tài liệu riêng do người dùng cung cấp nếu muốn kiểm tra trên nội dung của họ.
- Docker là lựa chọn môi trường. Hướng dẫn có đường chạy với Python và PostgreSQL/pgvector; không tự bật Docker trong quá trình làm việc nếu chưa được cho phép.

## 3. Lộ trình bốn giai đoạn

| Giai đoạn | Công việc | Trạng thái và điều kiện hoàn tất |
| --- | --- | --- |
| 1. Chặn lỗi nền tảng | Token, đăng nhập/reset/refresh, phân quyền dữ liệu, contract web/mobile, migration và CI. | Đã triển khai và kiểm thử theo báo cáo giai đoạn 1. Giữ các regression test khi thực hiện những giai đoạn sau. |
| 2. Đúng dữ liệu, nguồn và AI chạy thật | Canonical text/chunk/provenance; QA có nguồn; summary nhiều phần. Hoàn thiện chọn/tải checkpoint công khai, tokenizer và tiền xử lý, setup tự động. Agent xây bộ kiểm tra nhỏ trên 5–10 tài liệu và khoảng 20–30 câu hỏi, gồm câu không có đáp án. | Phần pipeline đã triển khai và kiểm thử kỹ thuật. Còn tích hợp/kiểm tra model thật; cần đầu ra đối chiếu được với nguồn, không bỏ phần cuối tài liệu và ghi kết quả thực tế. Bộ mẫu nhỏ không chứng minh tỷ lệ chính xác chung. |
| 3. Beta vận hành được | Storage local/Neon, quota, đọc văn bản không AI, lịch sử, log/health, HTTPS email, backup/restore và công cụ chuyển dữ liệu cũ. | Đã triển khai mã nguồn và kiểm thử cô lập; PostgreSQL, migration và backup/restore chạy trong CI. Nghiệm thu cloud thực tế cần preflight trong môi trường Neon/Brevo đã cấu hình. |
| 4. Công cụ học tập | Thẻ thủ công có nguồn, CRUD, lịch ôn, tiến độ chung web/mobile, tìm nội dung và xuất CSV/Markdown. | Đã triển khai với AI tắt; kiểm thử nguồn, lịch ôn, idempotency, conflict và UI lỗi mạng. Tạo thẻ bằng AI và ôn offline tiếp tục tạm hoãn. |

Theo quyết định ngày 2026-11-08: hoãn tích hợp/chạy AI của giai đoạn 2; triển khai bước quản lý sổ tay/tài liệu của giai đoạn 3 trước. Các mục vận hành còn lại của giai đoạn 3 và toàn bộ giai đoạn 4 được giữ nguyên. Chi tiết đã triển khai: [PHASE3_STEP1_IMPLEMENTATION_VI.md](PHASE3_STEP1_IMPLEMENTATION_VI.md).

## 4. Hướng lựa chọn model — đang tạm hoãn

Ưu tiên tái sử dụng pipeline hiện có và thử model local trước. Quyết định cuối dựa trên khả năng tải và chạy thực tế, RAM/GPU và thời gian phản hồi; chưa cam kết tốc độ khi chưa đo trên máy.

- Tìm kiếm: giữ `intfloat/multilingual-e5-small`, model công bố embedding 384 chiều, tương thích cấu trúc vector hiện có. Nguồn: https://huggingface.co/intfloat/multilingual-e5-small
- Hỏi đáp: thử checkpoint XLM-RoBERTa đã fine-tune cho QA tiếng Việt, thay vì nạp `xlm-roberta-base` và tự tạo head. Một ứng viên cần chạy kiểm tra là `hogger32/xlmRoberta-for-VietnameseQA`; tác giả mô tả đã fine-tune trên UIT-ViQuAD v2. Đây chưa phải kết luận chất lượng. Nguồn: https://huggingface.co/hogger32/xlmRoberta-for-VietnameseQA
- Tóm tắt: thử `VietAI/vit5-base-vietnews-summarization`, bản được công bố cho nhiệm vụ tóm tắt. Model card ghi không cần prefix; phải điều chỉnh runtime hiện đang thêm `summarize: ` mặc định, đồng thời kiểm tra tài liệu ngoài miền tin tức. Nguồn: https://huggingface.co/VietAI/vit5-base-vietnews-summarization
- Reranker: chọn bản công khai có hỗ trợ đa ngôn ngữ và đo chi phí thực tế. Nếu quá nặng, thiết kế chế độ tìm kiếm đơn giản hơn có thông báo rõ, thay vì để toàn bộ chức năng bị khóa vì thiếu reranker.

Nếu máy chạy local không đạt mức sử dụng được, thêm tùy chọn dịch vụ AI qua API sau khi làm rõ chi phí và việc gửi nội dung tài liệu ra ngoài. Không mặc định phát sinh chi phí hoặc gửi tài liệu cá nhân tới dịch vụ khác.

Hỏi đáp trích xuất hiện có phù hợp câu hỏi lấy thông tin trực tiếp từ nguồn. Câu hỏi cần tổng hợp/lập luận qua nhiều đoạn cần một hướng xử lý khác; đây là phần mở rộng sau khi bản cơ bản ổn định.

## 5. Phạm vi công việc kế tiếp

Hiện thực hiện quản lý sổ tay/tài liệu trong giai đoạn 3 với `AI_ENABLED=false`. Không tải model, không gọi API AI và không chạy inference. Chỉ tiếp tục phần AI khi người dùng yêu cầu mở lại.

Tài liệu này là lộ trình đề xuất, chưa phải ghi nhận đã tải/nạp hoặc kiểm chứng chất lượng các checkpoint vừa nêu. Trạng thái triển khai giai đoạn 2 trước đó nằm trong `docs/PHASE2_IMPLEMENTATION_VI.md`.

## 6. Triển khai giai đoạn 3–4

Giữ Render + Vercel; PostgreSQL và file riêng tư dùng Neon. Không dùng Supabase. Xem [vận hành](PHASE3_OPERATIONS_VI.md), [đọc và lịch sử](PHASE3_READING_VI.md), [thẻ học](PHASE4_STUDY_VI.md). Không coi CI hoặc dịch vụ giả lập là xác nhận credential/bucket/email cloud thực tế.
