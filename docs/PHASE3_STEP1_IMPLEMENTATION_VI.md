# Giai đoạn 3 — Bước 1: Quản lý sổ tay và tài liệu

Cập nhật 2026-11-08. Triển khai theo plan quản lý dữ liệu; phần AI được tạm hoãn theo yêu cầu của chủ project.

## Đã thay đổi

- `AI_ENABLED` mặc định `false`. Upload và tạo ghi chú chỉ lưu file/database, không tạo job AI. Worker thoát khi bị tắt; các job/kết quả cũ được giữ nguyên. Các request hỏi đáp, tóm tắt và reprocess trả `503 ERR_AI_DISABLED`; capabilities trả các model không sẵn sàng mà không gọi AI service.
- Sổ tay có `category` và `description` được lưu thật. Web/mobile hỗ trợ tạo/chỉnh sửa tên, mô tả, phân loại, icon, đánh dấu riêng tư và hiển thị ở trang chủ. Quyền sở hữu tiếp tục áp dụng; đánh dấu riêng tư không tạo cơ chế chia sẻ công khai.
- Bỏ suy đoán phân loại theo tên. Migration `phase3_management` kế tiếp `phase2_pipeline`, nhận diện icon danh mục cũ theo basename, hỗ trợ dấu `/` và `\`; không nhận diện được thì gán `personal`. Mô tả cũ thành chuỗi rỗng. Không reset dữ liệu.
- Web/mobile tìm sổ tay theo tên/mô tả, lọc theo danh mục; tìm tài liệu theo tên, lọc định dạng/trạng thái; sắp xếp mới nhất/cũ nhất/tên. Tìm kiếm không phân biệt hoa thường hoặc dấu tiếng Việt. Hai client dùng bộ ví dụ chung tại `contracts/management.json`.
- Tài liệu có thể đổi tên phần trước đuôi file. ID, storage key, checksum, phiên bản và bytes gốc giữ nguyên; không chạy lại pipeline.
- Khi AI tắt, tài liệu mới hiển thị “Đã lưu”, không polling chờ job. Chức năng AI bị vô hiệu hóa và có thông báo. Kết quả tải danh sách hoặc lưu từ ngữ cảnh cũ được chặn để không cập nhật nhầm sổ tay.
- Xóa sổ tay trên cả hai client có xác nhận sẽ xóa tài liệu bên trong; sau sửa/upload/xóa, làm mới các danh sách và số lượng liên quan.
- Cấu hình Compose đặt AI service/worker trong profile `ai`, không khởi động chúng trong cấu hình mặc định. Backend image chỉ cài dependency nhóm backend; worker có Dockerfile riêng cho cấu hình AI về sau. Không build hoặc bật Docker trong lần triển khai này.

## Contract

Các API tạo/sửa/đọc sổ tay giữ URL hiện có, bổ sung:

```json
{"category": "personal", "description": "Ghi chú cá nhân"}
```

`category`: `study | project | research | personal`; mặc định `personal` khi tạo. Mô tả tối đa 1.000 ký tự; dùng `""` để xóa mô tả. Tên sổ tay tối đa 200 ký tự. Update chỉ tác động trường được gửi; `category: null` bị từ chối.

- `GET /api/v1/app-config`: yêu cầu đăng nhập, trả `{"ai_enabled": false}`.
- `PATCH /api/v1/documents/{id}`: body `{"title": "Tên mới"}`; trả `DocumentResponse` hiện có. Tên phải có nội dung sau trim, tối đa 200 ký tự, không chứa `/`, `\` hoặc ký tự điều khiển. Đuôi file được giữ tự động.
- Response danh sách vẫn là mảng; lọc và sắp xếp hiện thực hiện trên client. Không có tìm kiếm nội dung hoặc semantic search trong bước này.
- Các fixture contract mới ở `contracts/phase3.json`; giữ các fixture giai đoạn trước để đối chiếu.

## Chạy phiên bản mới

Cần PostgreSQL/pgvector và cấu hình SECRET_KEY hợp lệ như giai đoạn 1. Trước khi chạy ứng dụng với database phát triển, áp dụng migration mới:

```powershell
uv run --no-sync alembic upgrade head
uv run --no-sync uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Giữ `AI_ENABLED=false`; không cần mở AI service hoặc worker. Không sửa secret và không migrate database thật trong lần triển khai này. Với môi trường backend mới cần cài gọn, dùng nhóm dependency đã có:

```powershell
uv sync --frozen --only-group backend --only-group dev
```

Không cần cài thêm dependency Flutter/npm mới cho bước này. Tài liệu chưa xử lý chỉ có thông tin tệp; chưa có chunk/canonical text để xem như một tài liệu đã phân tích.

## Kiểm chứng và giới hạn

- API quản lý được kiểm thử bằng SQLite riêng, không bật Docker và không dùng dữ liệu thật. Kiểm tra lưu/sửa/đọc lại metadata, ownership, rename giữ nguyên file, xóa, chế độ chỉ lưu file, không gọi AI và worker không nhận job.
- Web có kiểm thử form tạo/sửa, lọc/sắp xếp tiếng Việt, không polling khi AI tắt và bỏ qua phản hồi muộn của sổ tay khác.
- Mobile có kiểm thử contract tạo/sửa/rename/app-config và cùng bộ ví dụ tìm/lọc/sắp xếp với web, cùng regression đăng nhập và summary controller.
- Migration đã sinh SQL PostgreSQL offline; bài kiểm thử upgrade dữ liệu cũ được thêm vào suite PostgreSQL/CI. Chưa chạy integration/migration trên PostgreSQL trong lần này vì database test đang tắt; không coi kiểm thử SQLite là thay thế xác minh PostgreSQL.
- Không tải model, chạy inference, huấn luyện, benchmark AI, gửi SMTP thật, build APK hay chạy CI remote.

Kết quả kiểm tra cuối tại máy phát triển:

| Kiểm tra | Kết quả |
| --- | --- |
| Python mặc định | 40 qua; 31 bài PostgreSQL skip vì chưa cấu hình/chạy database test |
| Web | 17 bài qua; TypeScript, ESLint và production build Webpack qua |
| Flutter | 18 bài qua; analyzer không có ERROR/WARNING, còn 5 INFO lint/deprecation |
| Cấu hình/mã nguồn | AST Python, SQL migration offline, Compose config, lockfile check và `git diff --check` qua |
| Tiến trình sau kiểm thử | Không có server ứng dụng/test database được mở ở cổng 3000/8000/8001/55432 |

Phần kế tiếp của giai đoạn 3 vẫn gồm lịch sử, quota tổng dung lượng/job, backup/restore và đóng gói. Giai đoạn 4 vẫn gồm flashcard, lịch ôn và tiến độ học. Trình xem PDF đầy đủ, di chuyển tài liệu, thùng rác và chỉnh sửa nội dung file chưa thuộc bước này.
