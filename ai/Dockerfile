# Sử dụng Python 3.12 bản nhẹ làm base image
FROM python:3.12-slim

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Cài đặt các thư viện hệ thống cần thiết để compile/install
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt uv để quản lý package nhanh hơn
RUN pip install uv

# Copy requirements.txt của AI service vào container trước
COPY ai/requirements.txt ./ai_requirements.txt

# Cài đặt PyTorch CPU trước để giữ dung lượng image tối ưu nhất (khoảng 1.5-2GB thay vì 6GB+ với CUDA)
RUN uv pip install --system torch --index-url https://download.pytorch.org/whl/cpu

# Cài đặt toàn bộ các thư viện liên quan
RUN uv pip install --system -r ./ai_requirements.txt

# Copy toàn bộ mã nguồn thư mục ai vào container
COPY ai/ ./ai/

# Mở cổng 8001 cho AI Service
EXPOSE 8001

# Chạy AI service sử dụng Uvicorn
CMD ["uvicorn", "ai.main:app", "--host", "0.0.0.0", "--port", "8001"]
