# Gửi OTP bằng Gmail

DocuMind tự tạo và kiểm tra OTP như trước. Provider `gmail_api` gửi email qua HTTPS, phù hợp backend Render Free. Không dùng mật khẩu Gmail hoặc SMTP cho provider này. Backend chỉ dùng `httpx` đã có, không cài thêm Google SDK.

## Kết nối tài khoản gửi

1. Trong Google Cloud Console, chọn project của bạn và bật **Gmail API**.
2. Cấu hình Google Auth Platform (OAuth consent), chọn đối tượng phù hợp. Nếu app đang ở Testing, thêm Gmail gửi vào danh sách test users.
3. Tạo OAuth client loại **Desktop app**, tải file JSON và giữ ngoài repository.
4. Cài thư viện cho công cụ kết nối trên máy local:

```powershell
python -m pip install -r scripts/gmail-setup-requirements.txt
python scripts/configure_gmail.py --client-file "D:/DocuMindSecrets/google-client.json" --sender "gmail-cua-ban@gmail.com" --output "D:/DocuMindSecrets/cloud/gmail/provider.json"
```

Chọn đúng tài khoản gửi trên trang Google và cho phép gửi thư. Công cụ dùng thư viện OAuth chính thức, state/PKCE và callback loopback; chỉ xin scope `gmail.send`, không xin đọc hộp thư. File kết quả được lưu ngoài repo, hạn chế quyền truy cập; không in token ra terminal. Công cụ từ chối ghi đè file đã có.

Lưu ý vận hành: refresh token của ứng dụng External ở trạng thái Testing thường hết hạn sau 7 ngày với scope Gmail. Muốn dùng lâu dài, cần cấu hình trạng thái phát hành OAuth phù hợp và đáp ứng yêu cầu Google cho trường hợp sử dụng của bạn; không coi token Testing là cấu hình lâu dài.

## Cấu hình Render

Đặt các giá trị trong Environment của đúng service `documind-backend`:

```text
EMAIL_PROVIDER=gmail_api
GMAIL_SENDER_EMAIL=<Gmail đã cấp quyền>
GMAIL_CLIENT_ID=<client ID>
GMAIL_CLIENT_SECRET=<client secret>
GMAIL_REFRESH_TOKEN=<refresh token>
```

Không gửi các giá trị bí mật qua chat hoặc commit file vào Git. `GMAIL_SENDER_EMAIL` dùng riêng để tránh gửi bằng email SMTP mặc định trong source cũ. Giữ nguyên database/storage, SECRET_KEY và AI_ENABLED=false. Blueprint vẫn tắt auto-sync; không áp dụng lại Blueprint chỉ để đổi email.

Sau khi CI đạt và credentials đã có, triển khai backend mới rồi thử quên mật khẩu bằng một địa chỉ nghiệm thu được chủ project chỉ định. Kiểm tra email tới hộp thư và OTP dùng được trong thời hạn. Khi Gmail lỗi/hết quyền hoặc thiếu cấu hình, không gửi qua provider khác; API vẫn trả thông báo chung để tránh lộ tài khoản. Không log OTP, access token, refresh token hoặc phản hồi lỗi chứa secret.

SMTP và Brevo vẫn được giữ để tương thích cấu hình hiện có. Không cần thay đổi web/mobile hoặc huấn luyện model.

Tài liệu chính thức: [gửi email Gmail API](https://developers.google.com/workspace/gmail/api/guides/sending), [OAuth offline access](https://developers.google.com/identity/protocols/oauth2/web-server#offline), [vòng đời refresh token](https://developers.google.com/identity/protocols/oauth2#expiration).
