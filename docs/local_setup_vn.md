# 🔧 Hướng dẫn Cài đặt Local Chi tiết (Backend & DB)

Tài liệu này dành cho các lập trình viên muốn tự quản lý môi trường phát triển trên máy. Việc chạy Local giúp bạn kiểm soát hoàn toàn hệ thống nhưng đòi hỏi phải cài đặt PostgreSQL và các thành phần AI thủ công.

---

## 1. Yêu cầu Tiên quyết
Hãy đảm bảo máy bạn đã cài sẵn:
- **Python 3.12+**: Tải tại [python.org](https://www.python.org/).
- **uv**: Công cụ quản lý thư viện Python siêu tốc. Cài đặt bằng:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- **PostgreSQL 15+**: Hệ quản trị cơ sở dữ liệu.
- **Flutter SDK**: Để chạy ứng dụng Mobile.

---

## 2. Chuẩn bị Database (Quan trọng nhất)
DocuMind sử dụng **PostgreSQL** cùng với extension **pgvector** để xử lý các tìm kiếm AI.

### Bước 2.1: Cài đặt pgvector
- **MacOS (Dùng Homebrew)**: 
  ```bash
  brew install pgvector
  ```
- **Windows/Linux**: Tải bản build sẵn hoặc tự build theo hướng dẫn tại [pgvector GitHub](https://github.com/pgvector/pgvector#installation).

### Bước 2.2: Khởi tạo Database
1. Mở Terminal hoặc công cụ như DBeaver/pgAdmin.
2. Đăng nhập vào Postgres: `psql -U postgres`.
3. Chạy các lệnh SQL sau:
   ```sql
   CREATE DATABASE documind;
   \c documind;
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

---

## 3. Cấu hình Môi trường
1. Tìm file `.env` ở thư mục gốc của dự án.
2. Cập nhật `DATABASE_URL_OVERRIDE` trỏ về database máy bạn:
   ```env
   PROJECT_NAME=DocuMind
   # Định dạng: postgresql://[user]:[password]@localhost:[port]/[db_name]
   DATABASE_URL_OVERRIDE=postgresql://postgres:password@localhost:5432/documind
   SECRET_KEY=chuoi_ky_tu_bi_mat_cua_ban
   ```

---

## 4. Thiết lập Backend
1. **Đồng bộ thư viện**:
   ```bash
   uv sync
   ```
2. **Kiểm tra AI**:
   Chạy thử script này để xem máy có tải được mô hình AI không:
   ```bash
   uv run python tests/test_summarization.py
   ```
3. **Chạy Server**:
   ```bash
   uv run uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
   ```

---

## 5. Thiết lập Mobile
1. Vào thư mục mobile: `cd mobile`
2. Tải thư viện Flutter: `flutter pub get`
3. Chạy App: `flutter run`

---

## 💡 Xử lý lỗi thường gặp
- **Lỗi kết nối DB**: Kiểm tra lại Username/Password trong file `.env`. Đảm bảo Postgres đang chạy.
- **Lỗi ModuleNotFoundError**: Luôn dùng lệnh kèm theo `uv run` để đảm bảo môi trường Python được kích hoạt đúng.
- **Lỗi Vector Type**: Lỗi này nghĩa là bạn chưa chạy lệnh `CREATE EXTENSION vector;` bên trong đúng database `documind`.
