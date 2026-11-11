# Phát hành DocuMind beta cá nhân

Mục tiêu: web Vercel, backend Render, PostgreSQL/file riêng tư Neon, email Brevo và APK cài trực tiếp. AI giữ nguyên code/model/checkpoint và tiếp tục `AI_ENABLED=false`. Không bật Docker hoặc build APK trên máy local.

## Cấu hình Android và CI

- Application ID beta: `com.ncdanh0311.documind`; debug: `com.ncdanh0311.documind.debug`. Hai bản này tách khỏi APK thử cũ `com.example.documind_mobile`. Bản beta đầu cài như ứng dụng mới; không gỡ bản cũ hoặc hứa chuyển dữ liệu local cũ tự động. Dữ liệu trên server được mở lại bằng tài khoản của server đó.
- Bản release bắt buộc HTTPS và đường dẫn `/api/v1`, không nhận localhost/IP, thông tin đăng nhập, query hoặc fragment. Bản debug giữ HTTP local để phát triển. Không nhúng credential backend vào APK.
- Repository variables: `API_BASE_URL` (URL Render kèm `/api/v1`), `ANDROID_SIGNING_CERT_SHA256` (fingerprint SHA-256 public của certificate release).
- Repository secrets: `ANDROID_KEYSTORE_BASE64`, `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS`, `ANDROID_KEY_PASSWORD`. Giữ keystore và mật khẩu trong vị trí riêng ngoài repository, có bản sao dự phòng. Không đưa chúng vào chat, log, artifact, `key.properties` được commit hoặc PR.
- Khóa ký tạo một lần và dùng lại. Job main giải mã vào thư mục tạm của runner, cấu hình Gradle release và luôn dọn file sau build. Thiếu khóa không dùng debug thay thế. Hướng dẫn chính thức: https://docs.flutter.dev/deployment/android.
- Phiên bản đầu: `1.0.0-beta.1`; versionCode = `1000 + github.run_number` của workflow CI hiện tại. Không đặt lại workflow/run counter khi phát hành ứng dụng này; nếu thay workflow phải chọn mốc mới lớn hơn versionCode đã phát hành.
- CI nhánh/PR chạy các bộ test, production build web và APK debug `DocuMind-Test-APK`. Đây không phải bản phát hành và không nghiệm thu kết nối cloud.
- Sau khi các job đạt, CI `main` mới build APK có chữ ký thành artifact `DocuMind-Beta-APK`, chứa APK, `SHA256SUMS`, `release-manifest.json`. Manifest ghi commit, run ID, URL API, package, phiên bản và fingerprint certificate; không có secret.

## Kiểm tra cloud trước khi merge

Kiểm kê chỉ đọc các dịch vụ đang dùng; không giả định biến có trong máy chỉ vì đã cấu hình trên dashboard. Không đổi `SECRET_KEY` hoặc database nguồn. API dùng pooled URL, operator/migration dùng direct URL có TLS.

1. Xác nhận revision, extension vector, database đang kết nối, bucket `documind-documents` private, region và credential đúng Neon branch. Kiểm tra ACL qua S3; thử download ẩn danh một object kiểm thử phải bị từ chối. Bucket trống chỉ xác nhận được cấu hình private, chưa chứng minh upload/download.
2. Trên Render, ghi lại cấu hình Auto-Deploy; tạm đặt Off trước khi merge. Dịch vụ được Blueprint quản lý còn phải tạm đặt Blueprint Auto Sync = No: chỉ tắt Auto-Deploy của service chưa đủ để ngăn Blueprint cập nhật tài nguyên khi `render.yaml` thay đổi. File blueprint trong repo đặt auto-deploy off để dùng phát hành có kiểm soát.
3. Kiểm tra production deployment Vercel. Giữ bản cũ hoạt động trong khi backend chưa nâng schema; không promote giao diện mới trước backend. Root directory là `web`, `NEXT_PUBLIC_API_URL` cùng giá trị `API_BASE_URL`; CORS chỉ cho phép origin web đã kiểm chứng.
4. Kiểm tra `EMAIL_PROVIDER=brevo`, API key và sender đã xác minh. Chỉ gửi OTP đến tài khoản nghiệm thu được chỉ định, không reset mật khẩu tài khoản cá nhân của người dùng để thử.

## Backup, migration và phục hồi

Tham khảo quy trình đầy đủ ở `PHASE3_OPERATIONS_VI.md`. Dừng API/worker ghi trước khi backup và trong toàn bộ cửa sổ nâng cấp. Không dùng endpoint công khai để migrate.

```text
python -m backend.ops preflight
python -m backend.ops backup --writes-stopped --directory <thu-muc-moi-ngoai-repo>
python -m backend.ops verify-backup --directory <ban-backup>
```

Backup format 2 kiểm kê bảng/cột thực tế và revision (null với schema chưa dùng Alembic), nên sao lưu được trước migration. Format 1 cũ vẫn đọc được. Có file thiếu/đổi checksum thì ghi `backup-errors.json` và trả lỗi, không tạo manifest hoàn tất. Không tự đánh dấu backup đạt hoặc tiếp tục nâng dữ liệu khi lỗi chưa được xử lý.

Phục hồi thử vào database và bucket/thư mục **đích trống, tách biệt** bằng `restore --apply --writes-stopped`; đọc lại file đích kiểm tra SHA-256, revision, schema và số bản ghi. Schema cũ chưa có cột storage phải phục hồi file về local trước, rồi nâng/import và chuyển file; không gán metadata cloud mà schema cũ không lưu được. PostgreSQL client phải cùng major server; đặt `DOCUMIND_PG_BIN` nếu cần.

Sau khi backup/restore thử đạt:

- Schema thuộc chuỗi Alembic: chạy `alembic upgrade head` bằng URL direct.
- Schema trước baseline: import sang database mới đã migrate, giữ nguồn nguyên trạng, UUID và quan hệ. Không reset, `stamp head` hoặc ghi đè đích có dữ liệu.
- Chạy `reconcile` dạng xem trước; xử lý báo cáo file thiếu. Chạy `migrate-files --apply --writes-stopped` với file local còn tồn tại; chỉ đổi metadata sau khi đọc lại SHA-256, giữ bản local gốc.
- Chạy `python -m backend.ops preflight --require-current-schema`. Chế độ này trả lỗi nếu revision chưa đúng hoặc thiếu vector; kiểm tra ban đầu không yêu cầu schema đã nâng.

Rollback cần bộ code/cấu hình/database/file cùng thời điểm. Khôi phục backup sang đích trống rồi đổi kết nối, khôi phục file local tương ứng cho code cũ nếu cần. Không chỉ rollback image khi file đã chuyển provider. Sau khi mở lại ghi, phải kiểm kê dữ liệu phát sinh trước khi quyết định phục hồi bản cũ; không tự làm mất các thao tác mới.

## Nghiệm thu và công bố

Sau merge CI đạt: deploy backend của đúng SHA, `/health` và `/ready` đạt, rồi deploy web đúng API, cài APK có chữ ký từ CI. Không đổi database/bucket nguồn chỉ để làm test concurrency hoặc hết quota.

| Kiểm tra | Điều kiện đạt |
| --- | --- |
| Upload, đọc, tải PDF/DOCX/TXT | Nội dung tiếng Việt/emoji và checksum đúng; không có request AI |
| Quyền sở hữu | Tài khoản B không truy cập dữ liệu A; object riêng tư không tải ẩn danh |
| Redeploy | Tài liệu, nguồn, lịch sử, thẻ và tiến độ còn nguyên |
| Web → Android → web | Tạo thẻ có nguồn, ôn trên Android thật, web hiện đúng lịch/thống kê |
| Mất mạng/retry/xung đột | Không tăng tiến độ trước xác nhận, không ghi trùng, 409 tải trạng thái mới |
| Cập nhật APK | Hai bản beta liên tiếp cùng certificate, versionCode tăng, cài đè không phải gỡ |
| Brevo | OTP tới hộp thư nghiệm thu thật; log không ghi OTP/token |
| Backup/restore | Khôi phục vào đích riêng, đối chiếu schema/revision/số lượng/file SHA-256 |

Chỉ sau khi kiểm tra cloud **và** Android thật hoàn tất mới chạy workflow `Publish Verified DocuMind Beta` trên main: nhập CI run ID, full SHA đã nghiệm thu, xác nhận hai cờ nghiệm thu. Workflow từ chối run nhánh, run thất bại/bỏ qua signed build, manifest/checksum khác hoặc tag đã tồn tại. Công bố prerelease `v1.0.0-beta.1` gắn chính xác commit đó; không công bố APK debug hoặc tạo release chỉ vì CI build thành công.

Hằng tuần và trước migration: backup trong cửa sổ dừng ghi, giữ ba bản hoàn tất gần nhất ngoài repo. Giữ bản cũ đến khi bản mới kiểm chứng xong. Kết thúc phải dừng server kiểm thử local; không đặt lịch ping giữ Render/Neon thức.
