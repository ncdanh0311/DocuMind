# Giai đoạn 4 — Thẻ học thật và ôn tập trực tuyến

Mỗi sổ tay là một bộ thẻ. Thẻ được lưu qua API, không còn dữ liệu mẫu trong giao diện flashcard. Web/mobile hỗ trợ tạo, sửa, xóa, tìm theo câu hỏi/đáp án không phân biệt dấu, mở nguồn, xem thẻ đến hạn và tiến độ. Đăng nhập/quyền sở hữu hiện tại được giữ nguyên; không dùng Supabase, AI hay OCR.

## Dữ liệu và API

Migration `phase4_study` nối tiếp `phase3_reading`: thêm `flashcards`, `review_states`, `review_events`. Trạng thái ôn riêng với revision nội dung thẻ. Nguồn có FK SET NULL và snapshot giữ nguyên đoạn văn/phiên bản; xóa tài liệu vẫn giữ thẻ, xóa sổ tay xóa cả thẻ/lượt ôn.

- `GET/POST /api/v1/notebooks/{id}/flashcards`: `{items,next_cursor}` hoặc tạo thẻ, mặc định 20/tối đa 100.
- `GET/PATCH/DELETE /api/v1/flashcards/{id}`: đọc/sửa/xóa. PATCH gửi đầy đủ question/answer và `expected_revision` của nội dung. Không gửi `source` thì giữ nguồn; `source:null` bỏ nguồn. Sửa thẻ không reset lịch ôn.
- `GET /api/v1/flashcards/due?notebook_id=...`: tối đa 20 thẻ đến hạn, sắp theo hạn và ID; không đẩy tiến độ trước khi lưu thành công.
- `POST /api/v1/flashcards/{id}/reviews`: `request_id` UUID, `grade=again|remembered`, `expected_revision` trạng thái ôn và `card_revision` nội dung đang xem. UUID giống nhau/payload giống nhau trả lại kết quả cũ. UUID tái sử dụng cho payload khác hoặc revision cũ trả 409. Không cho chấm thẻ chưa đến hạn.
- `GET /api/v1/study/stats?notebook_id=...`: tổng thẻ, đến hạn, số thẻ khác nhau đã ôn hôm nay và streak; thời gian UTC, ngày học `Asia/Ho_Chi_Minh`. Streak duy trì nếu ngày học gần nhất là hôm qua; bỏ trống một ngày thì về 0.
- Nguồn khi tạo/sửa: document_id, version, start_offset/end_offset theo Unicode code point và snippet tùy chọn. Backend kiểm tra cùng sổ tay, phiên bản, khoảng ký tự và snippet chính xác; tự lấy tên/trang/mục, không tin metadata do client gửi.

Hợp đồng mẫu dùng chung `contracts/learning.json`; backend kiểm tra DTO response, web/mobile kiểm tra parse và vị trí Unicode.

## Quy tắc ôn

Thẻ mới đến hạn ngay. Mỗi lần nhớ chuyển lần lượt 1, 3, 7, 14, 30 ngày; đạt mức cuối tiếp tục 30 ngày. “Chưa nhớ” đưa về mức 0 và hẹn 10 phút. Lưu lượt ôn và trạng thái trong một transaction, khóa trên sổ tay/trạng thái để hai thiết bị không ghi hai lượt cho cùng revision.

Khi mạng lỗi hoặc chưa rõ kết quả, client giữ thẻ, đáp án và UUID yêu cầu để thử lại cùng lượt; không tự cộng số đã ôn. Khi 409, tải lại hàng đợi từ server và báo trạng thái thay đổi. Hai client dùng cùng server, làm mới khi quay lại màn hình/làm mới thủ công, không polling liên tục và chưa có chế độ offline.

## Tạo từ nguồn, tìm và xuất

Mở tài liệu → chọn đoạn văn → tạo thẻ. Nguồn được giữ riêng với câu trả lời người dùng nhập. Khi tài liệu đã đổi phiên bản, thẻ vẫn mở phiên bản nguồn gốc; khi file bị xóa, đoạn trích vẫn có và được ghi rõ nguồn không còn.

`GET /notebooks/{id}/search?q=...` tìm tiêu đề/nội dung canonical của phiên bản hiện tại, không dùng embedding. Tài liệu chưa đọc văn bản không có trong kết quả tìm nội dung. Hai client có màn hình tìm và mở đúng phiên bản tìm được.

`GET /notebooks/{id}/flashcards/export` xuất CSV UTF-8 BOM, có câu hỏi, đáp án, trích đoạn/tên/phiên bản nguồn; ô có tiền tố công thức được bảo vệ khi mở bằng spreadsheet. `/documents/{id}/export` xuất văn bản/ghi chú Markdown; `/history/qa|summary/{id}/export` xuất kết quả lịch sử hoàn tất kèm nguồn/model/thời điểm. Xuất dữ liệu không gọi AI.

## Kiểm chứng và phát hành

- Chạy bộ kiểm thử backend, web và Flutter; CI chạy PostgreSQL, migration, concurrency review/quota, pg_dump/restore, production build web và APK. Không build APK hoặc chạy model ở máy phát triển.
- Kiểm thử lịch bằng đồng hồ giả, nhớ đến mức cuối, quên, retry cùng UUID, UUID tái sử dụng, sửa revision cũ và hai thiết bị; ngày Việt Nam qua nửa đêm, nguồn đã xóa và cascade khi xóa sổ tay.
- Web kiểm tra form lưu lỗi giữ nội dung, lỗi mạng giữ thẻ và retry cùng UUID, xung đột tải lại server. Flutter có controller test và widget test trên viewport điện thoại cho hành trình ôn/lỗi mạng/retry.
- Triển khai backend sau backup/migration bằng URL Neon direct, rồi web và mobile dùng cùng API. Các kiểm thử cô lập không xác nhận credential cloud, trạng thái bucket hoặc email giao thật; chạy `backend.ops preflight` trong môi trường đã cấu hình trước khi nghiệm thu cloud.

Quota tổng storage còn tính cả file chờ xóa để tránh vượt dung lượng vật lý khi provider lỗi. Đọc văn bản thủ công có thể hủy job AI cũ đang tạm hoãn của cùng tài liệu; job vẫn được giữ trong lịch sử, lease bị vô hiệu hóa và không thể công bố đè lên phiên bản văn bản mới.
