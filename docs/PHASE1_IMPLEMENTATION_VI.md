# Giai đoạn 1: xác thực, phân quyền và database mới

## Thay đổi

- Nhiều phiên đăng nhập độc lập trên web/mobile; access và refresh JWT gắn với session riêng.
- Refresh token chỉ lưu SHA-256 trong database, xoay nguyên tử; token cũ không dùng lại được.
- Logout thu hồi phiên hiện tại ngay ở server. Đổi/reset mật khẩu thu hồi mọi phiên; reset tạo phiên mới.
- OTP sinh bằng secrets, lưu HMAC có khóa, hạn 5 phút, tối đa 5 lần nhập sai. Reset token có purpose riêng, hạn 10 phút và dùng một lần.
- Gửi OTP cách nhau tối thiểu 60 giây, tối đa 5 lần/giờ theo cả email và IP. Phản hồi luôn giống nhau cho email tồn tại, không tồn tại hoặc bị giới hạn. IP lấy từ kết nối đã được server xác định; chỉ cấu hình trusted proxy đáng tin cậy khi triển khai.
- HTTP 401 cho xác thực, 404 cho tài nguyên không thuộc người dùng. Bỏ endpoint `/init-db`.
- `/health` chỉ báo tiến trình; `/ready` kiểm tra kết nối, pgvector và migration head, trả 503 khi chưa sẵn sàng.
- Request validation và lỗi server không phản chiếu password, JWT hoặc exception database. Mobile không ghi response body vào log.
- Hai client gộp refresh đồng thời; web đồng bộ AuthContext sau reset. Mobile bỏ qua phản hồi refresh của thao tác xác thực cũ, kể cả khi đăng nhập mới chưa lưu token. Response dùng `reset_token`, `body`, `page_number`, `source_title`, `snippet`, `document_count`.
- Model QA hợp lệ: `phobert_qa`, `xlmroberta_qa`; model summary: `vit5`, `bartpho`. ID khác trả 422. Model thiếu checkpoint trả 503 khi gọi AI.
- Font Inter/Outfit của web nằm trong source cùng giấy phép OFL; build không tải Google Fonts. Production build dùng Webpack do Turbopack gặp lỗi tạo tiến trình PostCSS trên môi trường Windows này.

## Chạy trực tiếp với PostgreSQL cục bộ

Docker không bắt buộc. Cần PostgreSQL có extension pgvector, Python 3.12.9+, uv, Node 22 và Flutter.

1. Tạo **database mới** tên `documind_phase1` bằng công cụ PostgreSQL. Không trỏ baseline vào database cũ.
2. Trong `.env`, giữ các cấu hình SMTP/AI cần dùng; đặt `DATABASE_URL_OVERRIDE` trỏ vào database mới. Tạo secret bằng `python -c "import secrets; print(secrets.token_hex(32))"` rồi đặt vào `SECRET_KEY`. Giá trị mẫu/rỗng sẽ bị từ chối.
3. Cấu hình `CORS_ORIGINS` là JSON array các origin web được phép, ví dụ `["http://localhost:3000","http://127.0.0.1:3000"]`.
4. Chạy từ thư mục gốc:

```powershell
uv sync --frozen
uv run --no-sync alembic upgrade head
uv run --no-sync alembic check
uv run --no-sync uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Tài khoản chạy migration cần quyền tạo extension `vector`, hoặc quản trị viên tạo extension trước. API không tự sửa schema khi khởi động. Dùng `/ready` để kiểm tra khả năng phục vụ; `/health` không chứng minh database đã sẵn sàng.

Web:

```powershell
cd web
npm ci
npm run dev
```

Mobile giữ cách chạy hiện tại; có thể đặt URL theo môi trường mà không sửa source:

```powershell
cd mobile
flutter run --dart-define=API_BASE_URL=http://127.0.0.1:8000/api/v1
```

Điện thoại cần địa chỉ truy cập được hoặc `adb reverse`; Android emulator có thể dùng `10.0.2.2`. Chỉ dùng HTTP cho phát triển cục bộ; môi trường public dùng HTTPS.

## Database cũ và Docker Compose

Baseline `phase1_baseline` thay chuỗi migration phát triển cũ. Không chạy `stamp head` trên database cũ để bỏ qua khác biệt schema. Không có chuyển đổi dữ liệu cũ trong giai đoạn này.

Compose dùng volume mới `postgres_phase1_data`; volume `postgres_data` cũ không bị xóa. Service `migrate` phải thành công trước backend. Secret lấy từ `.env`; không có secret mẫu ghi đè. Có thể chạy `docker compose up --build` sau khi chuẩn bị cấu hình, nhưng chạy Docker không phải điều kiện để dùng ứng dụng.

## Kiểm thử cô lập

Bộ pytest mặc định chỉ thu thập `tests/api`; các script AI thủ công không tự chạy hoặc tải model khi thu thập test. Dữ liệu giả dùng chung tại `contracts/phase1.json` được kiểm tra ở backend, TypeScript và Dart.

Đặt `TEST_DATABASE_URL` tới một database **chỉ dành cho test**, tên phải kết thúc bằng `_test`. Bộ test sẽ truncate các bảng của database này và kiểm tra downgrade/rebuild baseline. Nếu không đặt biến, test tích hợp database sẽ được đánh dấu skip; CI luôn đặt biến này.

```powershell
$env:TEST_DATABASE_URL = 'postgresql://postgres:YOUR_TEST_PASSWORD@127.0.0.1:5432/documind_phase1_test'
uv run --no-sync pytest
```

Muốn chỉ cài dependency kiểm thử backend vào môi trường riêng:

```powershell
$env:UV_PROJECT_ENVIRONMENT = '.venv-backend'
uv sync --frozen --only-group backend --only-group dev
uv run --no-sync pytest
```

Nhóm backend tối thiểu phục vụ test API bằng AI giả; chạy ingestion thực tế cần bộ dependency đầy đủ, AI service và checkpoint (hoàn thiện trong giai đoạn 2).

```powershell
cd web
npm test
npm run lint
npm run build
```

```powershell
cd mobile
flutter test
flutter analyze --no-fatal-infos
```

CI cài dependency frozen, kiểm thử API/phân quyền/token/migration trên PostgreSQL/pgvector, chạy test web và Flutter rồi build web/APK. Không bỏ qua lỗi cài dependency.

## Giới hạn của giai đoạn 1

Chưa thay pipeline chia đoạn, số trang nguồn, cơ chế chọn span hoặc giới hạn tóm tắt 800 từ/512 token. Các vấn đề này thuộc giai đoạn 2. Chưa thêm worker, flashcard, cookie HttpOnly hay triển khai production. Web tiếp tục lưu token trong localStorage; mobile dùng secure storage.

SMTP thật và inference với checkpoint thật cần cấu hình riêng. Kiểm thử giai đoạn 1 giả lập gửi email và dịch vụ AI; không gửi email hay đổi mật khẩu trên tài khoản thật.

## Kết quả xác minh tại máy phát triển

- 29 test backend qua trên PostgreSQL 16 + pgvector riêng, gồm refresh/reset đồng thời và downgrade/rebuild baseline.
- Next.js/eslint-config-next được cập nhật lên 16.4.5; các dependency có bản vá tương thích được cập nhật. Audit dependency runtime trả 0 cảnh báo. Cảnh báo critical/high đã được loại bỏ; npm còn báo 16 moderate trong chuỗi công cụ ESLint/minimatch. Không áp dụng `audit fix --force` vì đề xuất downgrade ESLint phá vỡ công cụ hiện tại.
- 7 test web qua; ESLint, TypeScript và production build Webpack qua.
- 10 test Flutter qua (cập nhật 05/11/2026), gồm trường hợp refresh thất bại đến muộn trong khi đăng nhập mới. Analyzer đã chạy trước lần cập nhật này không có error/warning, còn 6 thông tin lint tại màn hình AI/notebook có từ trước.
- `alembic check` không có khác biệt schema; `uv lock --check --offline` và kiểm tra cú pháp toàn bộ Python qua.
- Chưa chạy SMTP thật, inference checkpoint thật, build APK cục bộ hoặc workflow GitHub Actions trên remote.
