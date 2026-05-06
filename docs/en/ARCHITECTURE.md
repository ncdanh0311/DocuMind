# DocuMind: System Architecture & Database Design

Tài liệu này mô tả chi tiết cách phân chia các dịch vụ và cấu trúc cơ sở dữ liệu cho ứng dụng DocuMind - Trợ lý đọc tài liệu thông minh.

## 1. Kiến trúc dịch vụ (Service Architecture)

Hệ thống được chia thành 4 thành phần chính để đảm bảo tính mở rộng và hiệu năng cao:

### A. Mobile Client (Flutter)
- **Vai trò:** Giao diện người dùng (UI/UX).
- **Chức năng:** Quản lý đăng nhập, hiển thị sổ tay, chọn file tài liệu, giao diện Chat AI và hiển thị bản tóm tắt.
- **Kết nối:** Giao tiếp với Custom Backend API (REST/GraphQL) và gọi các dịch vụ AI.

### B. Custom Backend & Infrastructure (PostgreSQL + API)
- **Framework:** FastAPI (Python) hoặc NestJS (Node.js).
- **Auth:** Quản lý người dùng qua JWT (JSON Web Tokens).
- **Database (PostgreSQL):** Lưu trữ dữ liệu quan hệ và Vector dữ liệu.
- **File Storage:** Sử dụng Local Storage (trong quá trình dev) hoặc AWS S3 / MinIO.
- **Vector DB (pgvector):** Extension của PostgreSQL để lưu trữ và tìm kiếm Vector.

### C. Document Processor (Background Worker)
- **Vai trò:** Dịch vụ xử lý ngầm (thường viết bằng Python).
- **Luồng hoạt động:**
    1. Nhận file từ API upload.
    2. Lưu trữ file vào hệ thống Storage (Local/S3).
    2. Trích xuất văn bản (Text Extraction) từ file PDF/Docx.
    3. Chia nhỏ văn bản (Chunking) một cách khoa học.
    4. Gọi Embedding Model để chuyển văn bản thành Vector.
    5. Lưu kết quả vào bảng `document_chunks`.
- **Lợi ích:** Người dùng không phải chờ đợi trên app khi đang xử lý tài liệu nặng.

### D. AI Engine (FastAPI/Python)
- **Vai trò:** Điều phối các mô hình ngôn ngữ lớn (LLM).
- **Chức năng:** 
    - **Summarization:** Tạo bản tóm tắt cho tài liệu.
    - **RAG Q&A:** Tìm kiếm các đoạn văn liên quan và trả lời câu hỏi dựa trên tài liệu (Chống bịa đặt).
    - **Flashcard Generator:** Tự động tạo câu hỏi ôn tập.

---

## 2. Thiết kế Cơ sở dữ liệu (Database Schema)

Sử dụng PostgreSQL với extension `pgvector`.

### 2.1. Bảng `users` (Người dùng)
Lưu trữ thông tin tài khoản và định danh người dùng.

| Trường | Kiểu dữ liệu | Mô tả |
| :--- | :--- | :--- |
| `id` | UUID (PK) | Mã định danh duy nhất |
| `email` | VARCHAR(255) | Email (Dùng để đăng nhập, Unique) |
| `password_hash` | TEXT | Mật khẩu đã được mã hóa (Bcrypt/Argon2) |
| `full_name` | TEXT | Họ và tên người dùng |
| `avatar_url` | TEXT | Link ảnh đại diện |
| `created_at` | TIMESTAMP | Thời gian tham gia |
| `updated_at` | TIMESTAMP | Thời gian cập nhật thông tin |

### 2.2. Bảng `notebooks` (Sổ tay)
Lưu trữ các không gian làm việc của người dùng.

| Trường | Kiểu dữ liệu | Mô tả |
| :--- | :--- | :--- |
| `id` | UUID (PK) | Mã định danh sổ tay |
| `user_id` | UUID (FK) | Liên kết với users.id |
| `title` | TEXT | Tiêu đề sổ tay (vd: Học máy) |
| `created_at` | TIMESTAMP | Thời gian tạo |

### 2.2. Bảng `documents` (Tài liệu)
Lưu trữ thông tin về các file được tải lên.

| Trường | Kiểu dữ liệu | Mô tả |
| :--- | :--- | :--- |
| `id` | UUID (PK) | Mã định danh tài liệu |
| `notebook_id` | UUID (FK) | Thuộc về sổ tay nào |
| `title` | TEXT | Tên file hoặc tiêu đề tài liệu |
| `file_url` | TEXT | Đường dẫn file trên hệ thống Storage |
| `raw_content` | TEXT | Toàn bộ văn bản đã trích xuất |
| `status` | VARCHAR | Trạng thái xử lý (processing, completed, error) |
| `summary` | TEXT | Bản tóm tắt do AI tạo |
| `created_at` | TIMESTAMP | Thời gian tải lên |

### 2.3. Bảng `document_chunks` (Đoạn tài liệu - Phục vụ AI)
Chia nhỏ tài liệu để AI có thể trích dẫn chính xác.

| Trường | Kiểu dữ liệu | Mô tả |
| :--- | :--- | :--- |
| `id` | UUID (PK) | Mã định danh đoạn văn |
| `document_id` | UUID (FK) | Thuộc về tài liệu nào |
| `content` | TEXT | Nội dung đoạn văn nhỏ |
| `embedding` | VECTOR(1536) | Vector đặc trưng (cho Gemini/OpenAI) |
| `page_number` | INTEGER | Vị trí trang (để làm trích dẫn) |
| `metadata` | JSONB | Các thông tin bổ sung khác |

### 2.4. Bảng `notes` (Ghi chú cá nhân)
Ghi chú do người dùng tự viết.

| Trường | Kiểu dữ liệu | Mô tả |
| :--- | :--- | :--- |
| `id` | UUID (PK) | Mã định danh ghi chú |
| `notebook_id` | UUID (FK) | Thuộc về sổ tay nào |
| `title` | TEXT | Tiêu đề ghi chú |
| `content` | TEXT | Nội dung ghi chú (Markdown) |
| `created_at` | TIMESTAMP | Thời gian tạo |

### 2.5. Bảng `qa_history` (Lịch sử hỏi đáp)
Lưu trữ các cuộc hội thoại với AI.

| Trường | Kiểu dữ liệu | Mô tả |
| :--- | :--- | :--- |
| `id` | UUID (PK) | Mã định danh câu hỏi |
| `notebook_id` | UUID (FK) | Liên kết với sổ tay |
| `question` | TEXT | Câu hỏi của người dùng |
| `answer` | TEXT | Câu trả lời của AI |
| `source_nodes` | JSONB | Danh sách các `chunk_id` đã dùng để trả lời (để trích dẫn) |
| `created_at` | TIMESTAMP | Thời gian hỏi |

---

## 3. Luồng dữ liệu "Hỏi AI" (RAG Flow)

1. **Người dùng gửi câu hỏi** từ Mobile App.
2. **Backend API** nhận câu hỏi, chuyển câu hỏi thành **Vector**.
3. **Database** thực hiện tìm kiếm (Similarity Search) trong bảng `document_chunks` để lấy ra các đoạn văn liên quan.
4. **AI Engine** gửi các đoạn văn này + Câu hỏi cho LLM với yêu cầu: "Chỉ trả lời dựa trên thông tin được cung cấp".
5. **AI Engine** trả kết quả về Mobile App kèm theo thông tin trang/vị trí để App hiển thị trích dẫn.
