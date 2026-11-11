# Kiểm chứng giai đoạn 3–4

Ngày kiểm tra: 2026-11-10. PostgreSQL/file cloud theo phương án Neon; backend Render, web Vercel; AI vẫn tắt. Không sử dụng Supabase, OCR hoặc model trong các lần kiểm tra này.

## Mã nguồn đã triển khai

- `feature/cloud-storage-and-operations`: storage local/Neon, quota có reservation, tải file riêng tư, đối soát/chuyển file, backup/restore, HTTPS email và log mã lỗi/request ID.
- `feature/document-history-and-reading`: đọc văn bản trong subprocess giới hạn, nguồn phiên bản, lịch sử và xuất Markdown; không mất bản tóm tắt khi xóa tài liệu.
- `feature/flashcards-and-review`: thẻ thủ công có nguồn, lịch ôn/idempotency/revision, tiến độ, tìm nội dung, CSV; giao diện web/mobile và điều hướng trên màn hình nhỏ.

Các branch nối tiếp nhau; branch cuối chứa toàn bộ thay đổi. Commit dùng tiếng Việt. Không thay credential hoặc tự nâng gói dịch vụ.

## Kiểm tra kỹ thuật

| Bộ kiểm tra | Kết quả ghi nhận |
| --- | --- |
| Python local | 70 đạt; 34 bài PostgreSQL để CI chạy trên database riêng |
| Web local | 28 bài đạt; TypeScript và ESLint đạt |
| Flutter local | 25 bài đạt; analyzer không còn vấn đề |
| CI trên bản tính năng trước các sửa UI cuối | Backend/PostgreSQL/migration/backup-restore, web production build và APK đều đạt; CI bản cuối được chạy lại khi push |
| Dữ liệu thật trên dịch vụ cloud | Chưa kiểm chứng từ workspace; cấu hình dịch vụ do chủ project quản lý |

Kiểm thử PostgreSQL gồm tranh chấp quota hai upload, hai thiết bị ôn cùng revision, migration khớp metadata và pg_dump/restore sang database trống. Backup roundtrip kiểm tra cả file gốc, thẻ và tiến độ đã ôn. Dùng PostgreSQL client cùng major server; CI backend cố định Ubuntu 24.04/PostgreSQL 16.

## Giao diện và hành trình người dùng

Đã thao tác trên bản local với tài khoản/database/file kiểm thử riêng: đăng nhập → tạo ghi chú qua form → đọc chữ → chọn đoạn nguồn tiếng Việt có emoji → tạo thẻ → ôn → tải lại trang. Tổng thẻ, thẻ đến hạn, số thẻ đã ôn và streak lấy từ backend; tiến độ vẫn đúng sau khi tải lại.

Đã sửa lỗi sidebar chiếm bề ngang điện thoại. Tại viewport 390 × 844, bề rộng nội dung đo được 385 px, không tràn ngang toàn trang; điều hướng chuyển sang thanh riêng trên mobile. Hộp đọc/chỉnh sửa thẻ được căn giữa và giới hạn chiều cao. Kiểm thử Flutter có viewport điện thoại và lỗi mạng khi lưu lượt ôn.

Yêu cầu đọc đồng thời của cùng tài liệu được gộp theo phiên đăng nhập; phiên mới không dùng lại kết quả của phiên cũ. Khi AI tắt, trang chủ không ghi tài liệu vừa lưu thành “Đang phân tích”, thao tác tạo QA/tóm tắt bị khóa và thẻ học vẫn mở được. Sidebar bỏ giới hạn số sổ tay giả; dung lượng file được lấy từ API.

## Điều kiện nghiệm thu cloud

Các kết quả trên không thay thế việc chạy `python -m backend.ops preflight` trong môi trường đã có credential, xác minh bucket private/Neon region, revision thực tế và gửi email giao thật. Trước khi phát hành cloud: backup, nâng schema bằng URL direct theo `PHASE3_OPERATIONS_VI.md`, chạy `/ready`, rồi kiểm tra upload/download và dùng chung tài khoản trên web/mobile. Không reset hoặc stamp database cũ để bỏ qua migration.

Các server kiểm thử local phải được dừng khi kết thúc; không để Docker, worker hoặc AI service chạy nền.

## Đợt hoàn tất phát hành — 2026-11-11

Nhánh `feature/cloud-beta-release` bổ sung APK có application ID riêng, HTTPS/release signing bắt buộc, checksum/provenance, workflow công bố tách biệt; backup format 2 đọc schema thực tế trước migration và preflight nghiêm ngặt sau migration. Quy trình tại `CLOUD_BETA_RELEASE_VI.md`.

- Kiểm thử local: 86 bài Python đạt, 35 bài PostgreSQL để CI chạy trên database riêng; Flutter 26 bài đạt và analyzer sạch. Actionlint kiểm định workflow đạt.
- Đã đăng nhập và xác định Neon project `sparkling-band-34724718`, branch `br-falling-hat-aegv7f1c`, PostgreSQL 18, region Ohio, gói Free. Đã tạo bucket `documind-documents` private; chưa upload object để nghiệm thu truy cập thực tế.
- Đã xác định Render service `srv-db163c60tbcc739n4r4g`, URL `https://documind-backend-dqkg.onrender.com`, code đang chạy `435a1c9`. Cấu hình kết nối backend chưa được đổi sang database mới; SECRET_KEY giữ nguyên.
- Đã tạo khóa ký beta cố định, lưu riêng ngoài repo tại `D:/DocuMindSecrets/android-beta` với ACL chỉ chủ máy/SYSTEM. Đã mã hóa và cấu hình bốn GitHub Secrets, hai repository variables cho API URL và fingerprint certificate. Không có secret trong commit/artifact.
- Chủ project đã cho phép lấy thông tin kết nối database/storage và lưu riêng tại `D:/DocuMindSecrets/cloud`, ACL chỉ chủ máy/SYSTEM. Không sao chép SECRET_KEY. Thông tin bí mật không nằm trong repository hoặc báo cáo.

## Kết quả chuyển dữ liệu thực tế — 2026-11-11

- Database nguồn là schema trước baseline: 2 tài khoản, 1 sổ tay, 1 tài liệu; chưa dùng Alembic. Đã backup đủ database và PDF, xác minh manifest/checksum rồi phục hồi sang database riêng trên Neon. Đối chiếu toàn bộ bản ghi, schema, số lượng và file đều khớp.
- File PDF được tìm lại trên Desktop theo đúng tên và tiêu đề, gồm 40 trang, 1.377.592 byte. Schema cũ không có checksum lịch sử nên không khẳng định đối chiếu byte với bản upload cũ trên ổ đĩa Render; provenance ghi rõ nguồn phục hồi. File Desktop được giữ nguyên; các bản sao và file trên Neon khớp SHA-256.
- Database đích mới đã nâng đúng chuỗi Alembic đến `phase4_study`, có extension vector. Nhập đủ 2 tài khoản/1 sổ tay/1 tài liệu, kiểm chứng UUID và password hash được giữ nguyên. Không reset/stamp hoặc ghi vào database nguồn; token/OTP phiên đăng nhập cũ không nhập lại.
- PDF đã chuyển sang bucket `documind-documents`, đọc lại checksum trước khi đổi metadata. Upload/download object thử có credential đạt, download ẩn danh bị từ chối; object thử đã dọn.
- Đã đọc thử PDF thực từ Neon bằng parser nhẹ: 40 mục trang, 187.837 ký tự, checksum khớp backup. Không gọi AI và không ghi phiên bản văn bản vào database trong kiểm tra này.
- Đã tạo thêm backup sau chuyển đổi và phục hồi thành công vào database/thư mục trống riêng. Các bản backup ở `D:/DocuMindBackups/cloud-beta-20261111/before-migration` và `after-migration`.
- Đã giảm reflection lặp/đệ quy trong công cụ operator để tránh quá nhiều truy vấn catalog trên kết nối Neon. Kiểm thử local 86 đạt; kiểm thử PostgreSQL/migration/restore tiếp tục qua CI của PR.

Backend Render đang Suspend trong cửa sổ chuyển đổi; Auto-Deploy = Off và Blueprint Auto Sync = No. Vercel có chốt Git không tự triển khai main cho đến khi backend mới sẵn sàng. Chưa đổi cấu hình/deploy code mới, chưa nghiệm thu OTP Brevo hoặc Android vật lý và chưa công bố prerelease. Chủ project yêu cầu tiếp tục bằng CLI/API, không dùng Computer Use; bước triển khai cần kết nối quản trị Render/Vercel qua API.
