# Giai đoạn 3 — Đọc văn bản và lịch sử

Đọc PDF có lớp chữ bằng PyMuPDF, DOCX bằng python-docx và TXT UTF-8. Không dùng Docling/OCR/model. Upload chỉ lưu file; `POST /api/v1/documents/{id}/extract-text` thực hiện đọc theo yêu cầu, tối đa một subprocess/instance, timeout 15 giây, 200 trang PDF, một triệu ký tự. Linux giới hạn không gian địa chỉ subprocess ở 256 MiB. DOCX giới hạn số mục và tổng kích thước giải nén để tránh zip bomb. Vượt giới hạn báo lỗi, không cắt nội dung âm thầm.

Kết quả canonical được lưu có phiên bản; mở lại dùng cache. Trạng thái `text_status` độc lập trạng thái xử lý AI: đọc chữ thành công không đánh dấu tài liệu đã có embedding hoặc sẵn sàng hỏi đáp. PDF scan cần OCR, file hỏng/khóa và timeout vẫn tải được file gốc. API `/source` giữ cách tính offset theo Unicode code point; hai client dùng cùng ví dụ emoji/văn bản tổ hợp tại `contracts/learning.json`.

Web/mobile mở màn hình đọc từ danh sách tài liệu, chọn trang/mục, tải file gốc và đọc bản nguồn cũ. Màn hình hiển thị dung lượng và lịch sử theo sổ tay. Lịch sử hỗ trợ keyset cursor `{items,next_cursor}`, xem hỏi đáp và tóm tắt khi AI tắt, xuất Markdown; không gọi AI để tạo lại nội dung. API `/summaries/{id}` giữ contract cũ, màn hình lịch sử dùng `/summary-history/{id}` để xem nội dung cũ kèm trạng thái nguồn thay vì coi nó là kết quả mới.

Migration `phase3_reading` đổi FK summary → document sang SET NULL; xóa tài liệu không xóa bản tóm tắt đã lưu. Snapshot trích dẫn giữ đoạn nguồn ngay cả sau khi chunks/file bị xóa; API phân biệt nguồn còn, thay đổi và không còn tồn tại. Xóa cả sổ tay vẫn xóa lịch sử theo quyền sở hữu.

Nâng cấp: dừng ghi, backup theo `PHASE3_OPERATIONS_VI.md`, chạy Alembic bằng URL direct, triển khai backend rồi web/mobile. Không migrate database thật từ kiểm thử. Các thay đổi API bổ sung, không đổi response dạng mảng cũ. Không cần worker chạy thường trực cho đọc văn bản.

Kiểm thử: PDF/DOCX/TXT thật, phần cuối/trang cuối/bảng, Unicode, cache không tạo version trùng, file scan/hỏng, busy/timeout, ownership và phân trang lịch sử. Web kiểm tra fallback tải file, mở phiên bản cũ và nguồn đã xóa; mobile/web đối chiếu cùng contract vị trí nguồn. Việc đọc văn bản không nghiệm thu chất lượng AI.
