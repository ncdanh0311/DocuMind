# Sử dụng Python 3.12 bản nhẹ
FROM python:3.12-slim

# Thiết lập thư mục làm việc
WORKDIR /app

# Cài đặt các công cụ hệ thống cần thiết
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy file định nghĩa thư viện từ thư mục gốc
COPY pyproject.toml .
COPY uv.lock .

# Cài đặt uv để quản lý thư viện nhanh hơn
RUN pip install uv
RUN uv pip install --system .

# Copy chỉ thư mục backend vào container
COPY backend/ ./backend/

# Mở cổng 8000
EXPOSE 8000

# Lệnh khởi chạy server (chạy module backend.main)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
