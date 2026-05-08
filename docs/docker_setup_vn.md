# 🚀 Hướng dẫn Chạy Docker Hiện đại (Khuyên dùng)

Docker là cách tốt nhất để vận hành DocuMind. Nó tự động hóa việc cài đặt phức tạp các mô hình AI, cơ sở dữ liệu chuyên dụng và mạng lưới chỉ với một lệnh duy nhất.

---

## 1. Tại sao nên dùng Docker?
- **Không cần cấu hình**: Bạn không cần cài PostgreSQL hay Python trên máy thật.
- **Sẵn sàng cho AI**: Bao gồm sẵn image `pgvector` chuyên dụng cho tìm kiếm ngữ nghĩa.
- **Tính đồng nhất**: Đảm bảo ứng dụng chạy giống hệt nhau trên mọi máy tính.

---

## 2. Bắt đầu nhanh
1. Đảm bảo **Docker Desktop** đã được cài đặt và đang chạy.
2. Mở Terminal tại thư mục gốc của dự án.
3. Chạy lệnh "thần thánh":
   ```bash
   docker-compose up --build
   ```

---

## 3. Quản lý các Dịch vụ
- **Dừng hệ thống**: Nhấn `Ctrl + C` hoặc chạy `docker-compose down`.
- **Chạy ngầm**: `docker-compose up -d` (hữu ích nếu bạn không muốn thấy log hiện liên tục).
- **Xem log**: `docker logs -f documind-backend`.
- **Build lại**: Nếu bạn thay đổi thư viện trong `pyproject.toml`, hãy chạy `docker-compose up --build`.

---

## 4. Truy cập Hệ thống
- **Tài liệu API**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Truy cập Database**: Bạn có thể kết nối vào DB từ máy thật bằng các công cụ như DBeaver/pgAdmin:
  - **Host**: `localhost`
  - **Port**: `5432`
  - **User**: `postgres`
  - **Password**: `password`
  - **Database**: `documind`

---

## 5. Quy trình Phát triển (Hot-Reload)
Thư mục `backend/` trên máy tính của bạn được liên kết trực tiếp với container.
**Khi bạn nhấn Save code trong IDE, server bên trong Docker sẽ tự khởi động lại.** Bạn KHÔNG cần phải build lại container cho mỗi lần thay đổi code.

---

## 💡 Xử lý lỗi thường gặp
- **Lỗi ModuleNotFoundError**: Thường do mount volume sai đường dẫn. Hãy kiểm tra file `docker-compose.yml`.
- **Cổng 5432 hoặc 8000 đã bị chiếm**: Hãy tắt các dịch vụ PostgreSQL hoặc FastAPI đang chạy trực tiếp trên máy trước khi bật Docker.
- **Database trống rỗng**: Nếu bạn vừa chuyển sang Docker, các tài khoản cũ ở máy thật sẽ KHÔNG có ở đây. **Bạn phải đăng ký tài khoản mới trên app di động.**
- **Lỗi Vector Type**: `docker-compose` của chúng ta đã được cấu hình tự động kích hoạt extension này. Nếu vẫn lỗi, hãy kiểm tra log của container `documind-db`.
