# Giai đoạn 3 — Neon storage và vận hành

AI tiếp tục tắt. Backend cloud dùng Render, web dùng Vercel; PostgreSQL và bucket riêng tư nằm trên Neon. Không dùng Supabase. Không tự migrate database hoặc bật Docker khi API khởi động.

## Cấu hình và kiểm tra trước triển khai

- `DATABASE_URL_OVERRIDE`: URL Neon pooled có TLS cho API.
- `DATABASE_DIRECT_URL`: URL Neon direct có TLS cho Alembic, pg_dump và pg_restore.
- `STORAGE_BACKEND=neon_s3`, `STORAGE_BUCKET=documind-documents`.
- `AWS_ENDPOINT_URL_S3`, `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`: credential Storage của đúng Neon branch. Bucket phải private; không đưa credential vào web/mobile.
- `CORS_ORIGINS`: JSON array chỉ chứa origin web thực tế; `NEXT_PUBLIC_API_URL` trên Vercel trỏ backend `/api/v1`; Flutter dùng `--dart-define=API_BASE_URL=https://<backend>/api/v1`.
- `EMAIL_PROVIDER=brevo`, `BREVO_API_KEY`, `EMAILS_FROM_EMAIL`: sender đã xác minh trong Brevo. Local có thể giữ SMTP. Giữ rate limit OTP hiện tại.
- Giữ `AI_ENABLED=false`. Không chạy worker/AI service. Render health check dùng `/health`; kiểm tra `/ready` sau migration/deploy, không cấu hình ping giữ dịch vụ thức.

Cài dependency backend gọn: `uv sync --frozen --only-group backend --only-group dev`. PostgreSQL client `pg_dump`/`pg_restore` phải có trong PATH khi dùng backup; phiên bản client phải tương thích server.

`python -m backend.ops preflight` kiểm tra revision, extension vector và truy cập bucket/ACL. Có thể cấu hình thêm `NEON_API_KEY`, `NEON_PROJECT_ID`, `NEON_BRANCH_ID` để xác minh trạng thái Storage bằng control-plane API. Không in credential trong báo cáo. Thiếu quyền hoặc region không hỗ trợ là điều kiện chưa nghiệm thu cloud, không tự chuyển provider.

## Nâng cấp dữ liệu

1. Dừng backend/worker để không có thao tác ghi. Chụp bản sao database cũ bằng pg_dump trước khi nâng cấp.
2. Với schema đã thuộc baseline giai đoạn 1: `uv run --no-sync alembic upgrade head` dùng URL direct. Migration mới nối tiếp `phase3_management`, không reset dữ liệu.
3. Nếu còn schema trước baseline: tạo database đích trống, migrate đích lên head; đặt `LEGACY_DATABASE_URL` trỏ nguồn cũ và URL direct trỏ đích. Chạy `python -m backend.ops import-legacy` để xem số lượng, rồi thêm `--apply --writes-stopped` để chép. Nguồn chỉ được đọc. UUID/mật khẩu/nội dung được giữ; phiên đăng nhập cũ không được nhập lại. Công cụ từ chối ghi đè bảng đích có dữ liệu.
4. Kiểm tra số lượng và quan hệ. Tài liệu legacy cần kiểm kê file: `python -m backend.ops reconcile`; thêm `--apply --writes-stopped` để lưu kích thước/checksum. File thiếu được báo theo document ID và đánh dấu `ERR_SOURCE_MISSING`; không giả định có thể khôi phục file đã mất trên Render.
5. Chuyển file local còn tồn tại sang Neon bằng `python -m backend.ops migrate-files`, sau đó `--apply --writes-stopped`. Chỉ đổi metadata sau khi đọc lại file cloud và kiểm tra SHA-256. Không xóa bản local gốc.
6. Đổi cấu hình ứng dụng sang đích đã kiểm chứng, khởi động backend và kiểm tra `/ready`, đăng nhập, upload/download. Giữ nguồn/bản sao cũ để quay lại khi cần; không rollback schema bằng cách xóa dữ liệu.

## Quota và dọn dẹp

Mặc định: 25 MiB/file, 512 MiB/tài khoản, 2 GiB/bản triển khai, tối đa 2 job AI queued/running/tài khoản khi AI được bật lại. API upload giữ chỗ dung lượng trong transaction ngắn, truyền file ngoài khóa database, công bố metadata sau khi upload thành công. Các reservation chưa hoàn tất vẫn được tính quota cho đến khi được đối soát.

`GET /api/v1/storage/usage` trả dung lượng tài khoản đã dùng/giữ chỗ và giới hạn. Tài liệu cũ chưa kiểm kê kích thước chặn upload mới với `ERR_STORAGE_RECONCILE_REQUIRED` để tránh tính thiếu dung lượng.

Xóa tài liệu/sổ tay ghi tác vụ xóa object trong cùng transaction; lỗi provider không làm sống lại metadata đã xóa. Chạy `python -m backend.ops cleanup` để xem reservation quá một giờ và tác vụ chờ. Sau khi chắc chắn uploader đã dừng, dùng `--apply --writes-stopped` để giải phóng và thử xóa lại. Không dựa vào lifecycle S3 tự dọn file.

## Backup, restore và sự cố

- Mỗi tuần và trước migration: dừng ghi, chạy `python -m backend.ops backup --writes-stopped --directory D:/DocuMindBackups/<timestamp>`. Thư mục phải mới và nằm ngoài repository. Giữ ba bản hoàn tất gần nhất; chỉ xóa bản cũ sau khi xác minh bản mới.
- Gói backup có `database.dump`, file gốc, manifest SHA-256, revision và số bản ghi từng bảng. Không có manifest nghĩa là backup chưa hoàn tất.
- Kiểm tra gói: `python -m backend.ops verify-backup --directory <backup>`.
- Restore thử với database và bucket/thư mục đích trống: `python -m backend.ops restore --apply --writes-stopped --directory <backup>`. Đối chiếu checksum, số lượng, quan hệ và mở file sau khi khôi phục. Không restore trực tiếp đè lên database thật.
- Nếu hết quota: dừng upload, xem bảng dung lượng và đối soát; không tự nâng gói trả phí. Nếu Render/Neon ngủ, báo đang kết nối và cho người dùng thử lại, không tạo vòng retry vô hạn.
- Log có request ID, route template, status, mã lỗi và thời gian; không ghi query string, request body, token hoặc OTP. Dùng `X-Request-ID` để đối chiếu lỗi.

Kiểm thử local dùng SQLite riêng và S3 giả lập; PostgreSQL migration, upload đồng thời và pg_dump/restore được kiểm tra trong CI với database riêng. Việc test giả lập không chứng minh bucket hoặc tài khoản Neon thực tế đã được cấu hình đúng.
